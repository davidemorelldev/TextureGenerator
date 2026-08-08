"""
texture_processor.py
--------------------
Texture processing utilities and asynchronous workers.
"""

from __future__ import annotations
import numpy as np
import cv2
from PySide6.QtCore import QThread, Signal, QObject


def _to_float32(img: np.ndarray) -> np.ndarray:
    if img.dtype == np.float32 and img.max() <= 1.0:
        return img
    return img.astype(np.float32) / 255.0


def _to_uint8(img: np.ndarray) -> np.ndarray:
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)


class TextureProcessor:

    @staticmethod
    def make_seamless(image: np.ndarray) -> np.ndarray:
        """Generates a seamless tileable texture using center-patch blending."""
        img_f = _to_float32(image)
        h, w = img_f.shape[:2]

        rolled = np.roll(img_f, (h // 2, w // 2), axis=(0, 1))

        blend_w = max(4, int(w * 0.20))
        blend_h = max(4, int(h * 0.20))

        mask_x = np.zeros(w, dtype=np.float32)
        cx = w // 2
        x0, x1 = cx - blend_w // 2, cx + blend_w // 2
        mask_x[x0:x1] = np.sin(np.linspace(0, np.pi, x1 - x0))

        mask_y = np.zeros(h, dtype=np.float32)
        cy = h // 2
        y0, y1 = cy - blend_h // 2, cy + blend_h // 2
        mask_y[y0:y1] = np.sin(np.linspace(0, np.pi, y1 - y0))

        mask_2d_x = np.tile(mask_x, (h, 1))
        mask_2d_y = np.tile(mask_y[:, None], (1, w))

        mask = np.maximum(mask_2d_x, mask_2d_y)[..., None]

        blended = img_f * mask + rolled * (1.0 - mask)
        return _to_uint8(blended)

    @staticmethod
    def adjust_hsv(
        image: np.ndarray,
        hue_shift: float = 0.0,
        saturation_scale: float = 1.0,
        value_scale: float = 1.0
    ) -> np.ndarray:
        img = _to_float32(image)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 360.0
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0.0, 1.0)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * value_scale, 0.0, 1.0)
        return _to_uint8(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))

    @staticmethod
    def apply_tiling(image: np.ndarray, scale: float = 1.0) -> np.ndarray:
        if scale <= 0:
            scale = 1.0
        h, w = image.shape[:2]
        new_w, new_h = max(1, int(w / scale)), max(1, int(h / scale))
        tile = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        rep_x, rep_y = -(-w // new_w), -(-h // new_h)
        tiled = np.tile(tile, (rep_y, rep_x, 1)) if image.ndim == 3 else np.tile(tile, (rep_y, rep_x))
        return tiled[:h, :w]

    @staticmethod
    def generate_heightmap(
        image: np.ndarray,
        contrast: float = 1.0,
        brightness: float = 0.0,
        invert: bool = False
    ) -> np.ndarray:
        gray = cv2.cvtColor(_to_float32(image), cv2.COLOR_BGR2GRAY)
        gray = np.clip((gray - 0.5) * contrast + 0.5, 0, 1)
        gray = np.clip(gray + brightness, 0, 1)
        if invert:
            gray = 1.0 - gray
        return cv2.cvtColor(_to_uint8(gray), cv2.COLOR_GRAY2BGR)

    @staticmethod
    def generate_normal_map(
        heightmap_bgr: np.ndarray,
        intensity: float = 1.0,
        invert_y: bool = False
    ) -> np.ndarray:
        gray = cv2.cvtColor(heightmap_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3) * intensity
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3) * intensity
        if invert_y:
            sobel_y = -sobel_y
        normal = np.stack([-sobel_x, -sobel_y, np.ones_like(sobel_x)], axis=2)
        normal /= (np.linalg.norm(normal, axis=2, keepdims=True) + 1e-8)
        encoded = ((normal + 1.0) * 0.5 * 255.0).astype(np.uint8)
        return encoded[:, :, ::-1].copy()

    @staticmethod
    def pack_orm(
        ao: np.ndarray | None,
        rough: np.ndarray | None,
        metal: np.ndarray | None,
        shape: tuple[int, int]
    ) -> np.ndarray:
        h, w = shape
        a = cv2.cvtColor(ao, cv2.COLOR_BGR2GRAY) if ao is not None else np.full((h, w), 255, dtype=np.uint8)
        r = cv2.cvtColor(rough, cv2.COLOR_BGR2GRAY) if rough is not None else np.full((h, w), 128, dtype=np.uint8)
        m = cv2.cvtColor(metal, cv2.COLOR_BGR2GRAY) if metal is not None else np.full((h, w), 0, dtype=np.uint8)
        return cv2.merge([m, r, a])

    @staticmethod
    def save_image(path: str, image: np.ndarray) -> bool:
        try:
            cv2.imwrite(path, image)
            return True
        except Exception:
            return False


class _BaseWorker(QObject):
    finished = Signal(np.ndarray)
    error = Signal(str)


class HsvWorker(_BaseWorker):
    def __init__(self, image: np.ndarray, hue: float, saturation: float, value: float, tiling: float):
        super().__init__()
        self._image = image
        self._hue = hue
        self._saturation = saturation
        self._value = value
        self._tiling = tiling

    def run(self):
        try:
            res = TextureProcessor.adjust_hsv(self._image, self._hue, self._saturation, self._value)
            self.finished.emit(TextureProcessor.apply_tiling(res, self._tiling))
        except Exception as exc:
            self.error.emit(str(exc))


class HeightmapWorker(_BaseWorker):
    def __init__(self, image: np.ndarray, contrast: float, brightness: float, invert: bool, tiling: float):
        super().__init__()
        self._image = image
        self._contrast = contrast
        self._brightness = brightness
        self._invert = invert
        self._tiling = tiling

    def run(self):
        try:
            result = TextureProcessor.generate_heightmap(self._image, self._contrast, self._brightness, self._invert)
            self.finished.emit(TextureProcessor.apply_tiling(result, self._tiling))
        except Exception as exc:
            self.error.emit(str(exc))


class NormalMapWorker(_BaseWorker):
    def __init__(self, heightmap: np.ndarray, intensity: float, invert_y: bool):
        super().__init__()
        self._heightmap = heightmap
        self._intensity = intensity
        self._invert_y = invert_y

    def run(self):
        try:
            self.finished.emit(TextureProcessor.generate_normal_map(self._heightmap, self._intensity, self._invert_y))
        except Exception as exc:
            self.error.emit(str(exc))


class RoughnessWorker(_BaseWorker):
    def __init__(self, image: np.ndarray, contrast: float, brightness: float, invert: bool, tiling: float):
        super().__init__()
        self._image = image
        self._contrast = contrast
        self._brightness = brightness
        self._invert = invert
        self._tiling = tiling

    def run(self):
        try:
            result = TextureProcessor.generate_heightmap(self._image, self._contrast, self._brightness, self._invert)
            self.finished.emit(TextureProcessor.apply_tiling(result, self._tiling))
        except Exception as exc:
            self.error.emit(str(exc))


class MetallicWorker(_BaseWorker):
    def __init__(self, image: np.ndarray, contrast: float, brightness: float, invert: bool, tiling: float):
        super().__init__()
        self._image = image
        self._contrast = contrast
        self._brightness = brightness
        self._invert = invert
        self._tiling = tiling

    def run(self):
        try:
            result = TextureProcessor.generate_heightmap(self._image, self._contrast, self._brightness, self._invert)
            self.finished.emit(TextureProcessor.apply_tiling(result, self._tiling))
        except Exception as exc:
            self.error.emit(str(exc))


class AoWorker(_BaseWorker):
    def __init__(self, hm: np.ndarray, c: float, b: float, blur: int, inv: bool):
        super().__init__()
        self._hm = hm
        self._c = c
        self._b = b
        self._blur = max(0, blur)
        self._inv = inv

    def run(self):
        try:
            gray = cv2.cvtColor(self._hm, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
            if self._blur > 0:
                gray = cv2.GaussianBlur(gray, (self._blur * 2 + 1, self._blur * 2 + 1), 0)
            gray = np.clip((gray - 0.5) * self._c + 0.5, 0, 1)
            gray = np.clip(gray + self._b, 0, 1)
            if self._inv:
                gray = 1.0 - gray
            gray8 = np.clip(gray * 255, 0, 255).astype(np.uint8)
            self.finished.emit(cv2.cvtColor(gray8, cv2.COLOR_GRAY2BGR))
        except Exception as e:
            self.error.emit(str(e))


class EmissionWorker(_BaseWorker):
    """Worker for generating emission map from brightness/color threshold"""
    def __init__(self, image: np.ndarray, threshold: float, intensity: float, tiling: float):
        super().__init__()
        self._image = image
        self._threshold = threshold
        self._intensity = intensity
        self._tiling = tiling

    def run(self):
        try:
            img = _to_float32(self._image)
            # Calculate brightness and create mask based on threshold
            brightness = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            mask = np.clip((brightness - self._threshold) / (1.0 - self._threshold), 0, 1)
            # Apply intensity
            mask = np.clip(mask * self._intensity, 0, 1)
            emission = _to_uint8(mask)
            result = cv2.cvtColor(emission, cv2.COLOR_GRAY2BGR)
            self.finished.emit(TextureProcessor.apply_tiling(result, self._tiling))
        except Exception as e:
            self.error.emit(str(e))


class ProcessingThread(QThread):
    def __init__(self, worker: _BaseWorker, parent=None):
        super().__init__(parent)
        self._worker = worker
        self._worker.moveToThread(self)
        self.started.connect(self._worker.run)