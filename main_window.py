"""
main_window.py
--------------
Main GUI application window, controls sidebar, previews, and 3D viewport.
PyTextureStudio - Professional PBR Texture Generator
"""

from __future__ import annotations
import os
import cv2
import json
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QSlider, QCheckBox, QPushButton, QFileDialog, QProgressDialog,
    QScrollArea, QSizePolicy, QComboBox, QStatusBar, QToolBar,
    QGroupBox, QSplitter, QSpacerItem, QDoubleSpinBox, QMessageBox, QInputDialog,
    QMenu, QMenuBar, QAction, QShortcut, QKeySequence, QDialog, QTextEdit,
    QTabWidget, QFrame, QToolButton, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QThread, QSettings, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QFont, QIcon, QKeySequence, QActionGroup

from texture_processor import (
    TextureProcessor,
    HeightmapWorker, NormalMapWorker, HsvWorker, RoughnessWorker, MetallicWorker, AoWorker, EmissionWorker,
    ProcessingThread
)
from gl_viewport import GLViewport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pytexturestudio.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


DARK_QSS = """
QWidget { background-color: #1a1a1f; color: #d4d4d8; font-family: "Segoe UI", sans-serif; font-size: 12px; }
QMainWindow { background-color: #111114; }
#Sidebar { background-color: #141418; border-right: 1px solid #2a2a32; }

QGroupBox { border: 1px solid #2e2e38; border-radius: 6px; margin-top: 14px; padding-top: 8px; font-weight: bold; color: #a78bfa; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; top: 1px; padding: 0 4px; }
QGroupBox::indicator { width: 14px; height: 14px; border: 1px solid #4a4a5a; border-radius: 3px; background: #1e1e26; }
QGroupBox::indicator:checked { background: #7c3aed; }

QSlider::groove:horizontal { height: 4px; background: #2e2e3a; border-radius: 2px; }
QSlider::handle:horizontal { background: #7c3aed; border: 2px solid #a78bfa; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
QSlider::sub-page:horizontal { background: #7c3aed; border-radius: 2px; }

QDoubleSpinBox { background: #22222c; border: 1px solid #3a3a48; border-radius: 4px; padding: 2px 4px; color: #a78bfa; }
QDoubleSpinBox:focus { border: 1px solid #7c3aed; background: #2a2a35; }

QPushButton { background-color: #2a2a35; border: 1px solid #3a3a48; border-radius: 5px; padding: 5px 12px; color: #c4b5fd; }
QPushButton:hover { background-color: #3d3d50; border-color: #7c3aed; }
QPushButton:pressed { background-color: #7c3aed; color: #fff; }
QPushButton#ExportBtn { background-color: #5b21b6; border: none; color: #fff; font-weight: bold; padding: 7px 18px; }
QPushButton#ExportBtn:hover { background-color: #7c3aed; }

QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #4a4a5a; border-radius: 3px; background: #1e1e26; }
QCheckBox::indicator:checked { background: #7c3aed; }

QComboBox { background: #22222c; border: 1px solid #3a3a48; border-radius: 4px; padding: 3px 8px; color: #c4b5fd; }
QLabel#MapLabel { background: #0d0d10; border: 1px solid #2a2a32; border-radius: 4px; }
QStatusBar { background-color: #0d0d10; color: #6b7280; font-size: 11px; border-top: 1px solid #1e1e26; }
QScrollArea { border: none; }
QSplitter::handle { background: #2a2a32; width: 2px; }
QToolBar { background-color: #141418; border-bottom: 1px solid #2a2a32; spacing: 5px; padding: 5px; }
"""


def _np_to_pixmap(bgr: np.ndarray, w: int, h: int) -> QPixmap:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.shape[1] * 3, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimg).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


class LabeledSlider(QWidget):
    valueChanged = Signal(float)

    def __init__(self, label: str, min_val: float, max_val: float, default: float, decimals: int = 2, parent=None):
        super().__init__(parent)
        self._scale = 10 ** decimals
        self._decimals = decimals

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)

        lbl = QLabel(label)
        lbl.setFixedWidth(90)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(int(min_val * self._scale), int(max_val * self._scale))
        self._slider.setValue(int(default * self._scale))

        self._spinbox = QDoubleSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setValue(default)
        self._spinbox.setSingleStep(1.0 if decimals == 0 else 0.1)
        self._spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self._spinbox.setKeyboardTracking(False)
        self._spinbox.setFixedWidth(60)

        lay.addWidget(lbl)
        lay.addWidget(self._slider, 1)
        lay.addWidget(self._spinbox)

        self._slider.valueChanged.connect(self._on_slider_change)
        self._spinbox.valueChanged.connect(self._on_spinbox_change)

    def _on_slider_change(self, raw: int):
        v = raw / self._scale
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(v)
        self._spinbox.blockSignals(False)
        self.valueChanged.emit(v)

    def _on_spinbox_change(self, v: float):
        self._slider.blockSignals(True)
        self._slider.setValue(int(v * self._scale))
        self._slider.blockSignals(False)
        self.valueChanged.emit(v)

    def value(self) -> float:
        return self._spinbox.value()

    def setValue(self, v: float):
        self._spinbox.setValue(v)


class SidebarPanel(QScrollArea):
    baseChanged = Signal()
    heightChanged = Signal()
    normalChanged = Signal()
    aoChanged = Signal()
    roughChanged = Signal()
    metalChanged = Signal()
    togglesSynced = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setWidgetResizable(True)
        self.setFixedWidth(290)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        def add_box(title, sliders, checks, signal, checkable=True):
            b = QGroupBox(title)
            b.setCheckable(checkable)
            b.setChecked(True)
            l = QVBoxLayout(b)
            for sl in sliders:
                l.addWidget(sl)
                sl.valueChanged.connect(signal)
            for ch in checks:
                l.addWidget(ch)
                ch.stateChanged.connect(lambda _: signal.emit())
            if checkable:
                b.toggled.connect(lambda _: self.togglesSynced.emit())
            lay.addWidget(b)
            return b

        self.s_hue = LabeledSlider("Hue Shift", -180, 180, 0.0, 0)
        self.s_sat = LabeledSlider("Saturation", 0.0, 3.0, 1.0)
        self.s_val = LabeledSlider("Value", 0.0, 3.0, 1.0)
        self.s_tile = LabeledSlider("Tiling", 0.1, 8.0, 1.0)
        self.base_box = add_box("Base Texture", [self.s_hue, self.s_sat, self.s_val, self.s_tile], [], self.baseChanged, False)

        self.s_hm_c = LabeledSlider("Contrast", 0.1, 4.0, 1.0)
        self.s_hm_b = LabeledSlider("Brightness", -1.0, 1.0, 0.0)
        self.cb_hm_inv = QCheckBox("Invert")
        self.hm_box = add_box("Heightmap", [self.s_hm_c, self.s_hm_b], [self.cb_hm_inv], self.heightChanged)

        self.s_nm_i = LabeledSlider("Intensity", 0.1, 10.0, 2.0)
        self.cb_nm_inv = QCheckBox("Invert Y Channel")
        self.nm_box = add_box("Normal Map", [self.s_nm_i], [self.cb_nm_inv], self.normalChanged)

        self.s_r_c = LabeledSlider("Contrast", 0.1, 4.0, 1.0)
        self.s_r_b = LabeledSlider("Brightness", -1.0, 1.0, 0.0)
        self.cb_r_inv = QCheckBox("Invert (Glossy)")
        self.rough_box = add_box("Roughness Map", [self.s_r_c, self.s_r_b], [self.cb_r_inv], self.roughChanged)

        self.s_m_c = LabeledSlider("Threshold", 0.1, 4.0, 2.0)
        self.s_m_b = LabeledSlider("Brightness", -1.0, 1.0, -0.5)
        self.cb_m_inv = QCheckBox("Invert")
        self.metal_box = add_box("Metallic Map", [self.s_m_c, self.s_m_b], [self.cb_m_inv], self.metalChanged)
        self.metal_box.setChecked(False)

        self.s_ao_c = LabeledSlider("Contrast", 0.1, 4.0, 1.5)
        self.s_ao_b = LabeledSlider("Brightness", -1.0, 1.0, -0.1)
        self.s_ao_blur = LabeledSlider("Blur Radius", 0.0, 20.0, 3.0, 0)
        self.ao_box = add_box("Ambient Occlusion", [self.s_ao_c, self.s_ao_b, self.s_ao_blur], [QCheckBox("Invert")], self.aoChanged)

        lay.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.setWidget(container)

    def get_settings(self) -> dict:
        return {
            'hue': self.s_hue.value(),
            'sat': self.s_sat.value(),
            'val': self.s_val.value(),
            'tile': self.s_tile.value(),
            'hm_on': self.hm_box.isChecked(),
            'hm_c': self.s_hm_c.value(),
            'hm_b': self.s_hm_b.value(),
            'hm_inv': self.cb_hm_inv.isChecked(),
            'nm_on': self.nm_box.isChecked(),
            'nm_i': self.s_nm_i.value(),
            'nm_inv': self.cb_nm_inv.isChecked(),
            'r_on': self.rough_box.isChecked(),
            'r_c': self.s_r_c.value(),
            'r_b': self.s_r_b.value(),
            'r_inv': self.cb_r_inv.isChecked(),
            'm_on': self.metal_box.isChecked(),
            'm_c': self.s_m_c.value(),
            'm_b': self.s_m_b.value(),
            'm_inv': self.cb_m_inv.isChecked(),
            'ao_on': self.ao_box.isChecked(),
            'ao_c': self.s_ao_c.value(),
            'ao_b': self.s_ao_b.value(),
            'ao_blur': self.s_ao_blur.value()
        }

    def load_settings(self, d: dict):
        self.s_hue.setValue(d['hue'])
        self.s_sat.setValue(d['sat'])
        self.s_val.setValue(d['val'])
        self.s_tile.setValue(d['tile'])
        self.hm_box.setChecked(d['hm_on'])
        self.s_hm_c.setValue(d['hm_c'])
        self.s_hm_b.setValue(d['hm_b'])
        self.cb_hm_inv.setChecked(d['hm_inv'])
        self.nm_box.setChecked(d['nm_on'])
        self.s_nm_i.setValue(d['nm_i'])
        self.cb_nm_inv.setChecked(d['nm_inv'])
        self.rough_box.setChecked(d['r_on'])
        self.s_r_c.setValue(d['r_c'])
        self.s_r_b.setValue(d['r_b'])
        self.cb_r_inv.setChecked(d['r_inv'])
        self.metal_box.setChecked(d['m_on'])
        self.s_m_c.setValue(d['m_c'])
        self.s_m_b.setValue(d['m_b'])
        self.cb_m_inv.setChecked(d['m_inv'])
        self.ao_box.setChecked(d['ao_on'])
        self.s_ao_c.setValue(d['ao_c'])
        self.s_ao_b.setValue(d['ao_b'])
        self.s_ao_blur.setValue(d['ao_blur'])


class MapPreview(QLabel):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("MapLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(150, 150)
        self._title = title
        self.clear_image("no image")

    def set_image(self, bgr: np.ndarray):
        self.setPixmap(_np_to_pixmap(bgr, self.width() - 4, self.height() - 4))

    def clear_image(self, text: str = "Disabled"):
        self.clear()
        self.setText(f"<span style='color:#3a3a4a; font-size:13px;'>{self._title}<br><span style='font-size:10px;'>({text})</span></span>")

    def resizeEvent(self, event):
        super().resizeEvent(event)


class BatchWorker(QThread):
    progress = Signal(str, int, int)
    done = Signal()

    def __init__(self, in_dir: str, out_dir: str, cfg: dict, export_mode: str):
        super().__init__()
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.cfg = cfg
        self.export_mode = export_mode

    def run(self):
        files = [f for f in os.listdir(self.in_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.bmp'))]
        for i, f in enumerate(files):
            self.progress.emit(f"Processing {f}...", i, len(files))
            img = cv2.imread(os.path.join(self.in_dir, f), cv2.IMREAD_COLOR)
            if img is None:
                continue

            c = self.cfg
            albedo = TextureProcessor.adjust_hsv(img, c['hue'], c['sat'], c['val'])
            albedo = TextureProcessor.apply_tiling(albedo, c['tile'])

            hm = TextureProcessor.apply_tiling(TextureProcessor.generate_heightmap(img, c['hm_c'], c['hm_b'], c['hm_inv']), c['tile']) if c['hm_on'] else None
            nm = TextureProcessor.generate_normal_map(hm, c['nm_i'], c['nm_inv']) if hm is not None and c['nm_on'] else None
            rm = TextureProcessor.apply_tiling(TextureProcessor.generate_heightmap(img, c['r_c'], c['r_b'], c['r_inv']), c['tile']) if c['r_on'] else None
            mm = TextureProcessor.apply_tiling(TextureProcessor.generate_heightmap(img, c['m_c'], c['m_b'], c['m_inv']), c['tile']) if c['m_on'] else None

            aom = None
            if c['ao_on'] and hm is not None:
                gray = cv2.cvtColor(hm, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                if c['ao_blur'] > 0:
                    gray = cv2.GaussianBlur(gray, (int(c['ao_blur']) * 2 + 1, int(c['ao_blur']) * 2 + 1), 0)
                aom = cv2.cvtColor(np.clip((np.clip((gray - 0.5) * c['ao_c'] + 0.5, 0, 1) + c['ao_b']) * 255, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)

            out_folder = os.path.join(self.out_dir, os.path.splitext(f)[0])
            os.makedirs(out_folder, exist_ok=True)

            save_all = self.export_mode in ["All Individual Maps", "Both (Individual + ORM)"]
            save_orm = self.export_mode in ["ORM Packed Only", "Both (Individual + ORM)"]

            if save_all:
                TextureProcessor.save_image(os.path.join(out_folder, "albedo.png"), albedo)
                if hm is not None:
                    TextureProcessor.save_image(os.path.join(out_folder, "heightmap.png"), hm)
                if nm is not None:
                    TextureProcessor.save_image(os.path.join(out_folder, "normal.png"), nm)
                if rm is not None:
                    TextureProcessor.save_image(os.path.join(out_folder, "roughness.png"), rm)
                if mm is not None:
                    TextureProcessor.save_image(os.path.join(out_folder, "metallic.png"), mm)
                if aom is not None:
                    TextureProcessor.save_image(os.path.join(out_folder, "ao.png"), aom)

            if save_orm:
                if not save_all:
                    TextureProcessor.save_image(os.path.join(out_folder, "albedo.png"), albedo)
                if nm is not None and not save_all:
                    TextureProcessor.save_image(os.path.join(out_folder, "normal.png"), nm)

                orm = TextureProcessor.pack_orm(aom, rm, mm, albedo.shape[:2])
                TextureProcessor.save_image(os.path.join(out_folder, "ORM_packed.png"), orm)

        self.progress.emit("Batch Complete", len(files), len(files))
        self.done.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyTextureStudio v2.3")
        self.resize(1440, 900)

        self._source_image: np.ndarray | None = None
        self._albedo_image: np.ndarray | None = None
        self._heightmap: np.ndarray | None = None
        self._normal_map: np.ndarray | None = None
        self._rough_map: np.ndarray | None = None
        self._metal_map: np.ndarray | None = None
        self._ao_map: np.ndarray | None = None
        self._active_threads: list[ProcessingThread] = []

        self._build_ui()
        self._connect_signals()
        self.statusBar().showMessage("Ready. Load a texture to begin.")

    def _build_ui(self):
        tb = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        tb.addAction("Load Image", self._load_texture)
        tb.addAction("Make Seamless", self._make_seamless)
        tb.addSeparator()
        tb.addAction("Save Preset", self._save_preset)
        tb.addAction("Load Preset", self._load_preset)
        tb.addSeparator()
        tb.addAction("Batch Process Folder", self._run_batch)
        tb.addSeparator()
        tb.addAction("Export ORM (UE/Unity)", self._export_orm)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = SidebarPanel()
        root.addWidget(self._sidebar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        root.addWidget(splitter, 1)

        grid_w = QWidget()
        gl = QVBoxLayout(grid_w)
        gl.setContentsMargins(8, 8, 8, 8)
        gl.setSpacing(4)

        btn_export = QPushButton("Export All Individual Maps")
        btn_export.setObjectName("ExportBtn")
        btn_export.clicked.connect(self._export_all)
        gl.addWidget(btn_export)

        map_grid = QGridLayout()
        self._prev_albedo = MapPreview("Albedo / Base")
        self._prev_height = MapPreview("Heightmap")
        self._prev_normal = MapPreview("Normal Map")
        self._prev_rough = MapPreview("Roughness")
        self._prev_metal = MapPreview("Metallic")
        self._prev_ao = MapPreview("Ambient Occlusion")

        map_grid.addWidget(self._prev_albedo, 0, 0)
        map_grid.addWidget(self._prev_height, 0, 1)
        map_grid.addWidget(self._prev_normal, 0, 2)
        map_grid.addWidget(self._prev_rough, 1, 0)
        map_grid.addWidget(self._prev_metal, 1, 1)
        map_grid.addWidget(self._prev_ao, 1, 2)
        gl.addLayout(map_grid, 1)
        splitter.addWidget(grid_w)

        vp_w = QWidget()
        vl = QVBoxLayout(vp_w)
        vl.setContentsMargins(0, 8, 8, 8)

        box_3d = QGroupBox("3D Viewport Settings")
        cl = QGridLayout(box_3d)

        cl.addWidget(QLabel("Mesh:"), 0, 0)
        self.cb_mesh = QComboBox()
        self.cb_mesh.addItems(["Cube", "Sphere"])
        cl.addWidget(self.cb_mesh, 0, 1)

        btn_obj = QPushButton("Import .obj")
        btn_obj.clicked.connect(self._load_obj_dialog)
        cl.addWidget(btn_obj, 0, 2)

        self.cb_autorot = QCheckBox("Auto-Rotate")
        self.cb_autorot.setChecked(True)
        cl.addWidget(self.cb_autorot, 0, 3)

        self.s_bump = LabeledSlider("Bump Scale", 0.0, 0.5, 0.05)
        self.s_ao_str = LabeledSlider("AO Strength", 0.0, 1.0, 1.0)
        cl.addWidget(self.s_bump, 1, 0, 1, 2)
        cl.addWidget(self.s_ao_str, 1, 2, 1, 2)

        vl.addWidget(box_3d)

        hint = QLabel(" (drag to rotate, scroll to zoom, double-click to reset)")
        hint.setStyleSheet("color:#6b7280; font-size:11px; padding:2px 4px;")
        vl.addWidget(hint)
        self._gl = GLViewport()
        vl.addWidget(self._gl, 1)
        splitter.addWidget(vp_w)

        splitter.setSizes([700, 420])
        self.setStatusBar(QStatusBar())

    def _connect_signals(self):
        sb = self._sidebar
        sb.baseChanged.connect(self._schedule_base)
        sb.heightChanged.connect(self._schedule_height)
        sb.normalChanged.connect(self._schedule_normal)
        sb.roughChanged.connect(self._schedule_roughness)
        sb.metalChanged.connect(self._schedule_metal)
        sb.aoChanged.connect(self._schedule_ao)
        sb.togglesSynced.connect(self._sync_toggles)

        self.cb_mesh.currentIndexChanged.connect(self._on_mesh_changed)

        self.s_bump.valueChanged.connect(self._gl.set_bump_scale)
        self.s_ao_str.valueChanged.connect(self._gl.set_ao_strength)
        self.cb_autorot.stateChanged.connect(lambda s: self._gl.set_auto_rotate(s == Qt.CheckState.Checked.value))

    def _on_mesh_changed(self, index: int):
        data = self.cb_mesh.itemData(index)
        if data:
            self._gl.set_mesh(data)
        else:
            self._gl.set_mesh(self.cb_mesh.itemText(index))

    def _load_texture(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Texture", filter="Images (*.png *.jpg *.jpeg *.tga *.bmp)")
        if not path:
            return
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            return
        self._source_image = img
        self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")
        self._schedule_base()

    def _load_obj_dialog(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load Mesh", filter="3D Files (*.obj *.OBJ);;All Files (*)")
        if p:
            name = os.path.basename(p)
            existing_idx = self.cb_mesh.findData(p)
            if existing_idx != -1:
                self.cb_mesh.setCurrentIndex(existing_idx)
            else:
                self.cb_mesh.addItem(name, p)
                self.cb_mesh.setCurrentIndex(self.cb_mesh.count() - 1)
            self.statusBar().showMessage(f"Loaded mesh: {name}")

    def _make_seamless(self):
        if self._source_image is not None:
            self._source_image = TextureProcessor.make_seamless(self._source_image)
            self.statusBar().showMessage("Converted image to seamless texture.")
            self._schedule_base()

    def _save_preset(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save Preset", filter="JSON (*.json)")
        if p:
            with open(p, 'w') as f:
                json.dump(self._sidebar.get_settings(), f, indent=2)

    def _load_preset(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load Preset", filter="JSON (*.json)")
        if p:
            with open(p, 'r') as f:
                self._sidebar.load_settings(json.load(f))
            self._schedule_base()

    def _run_batch(self):
        items = ["All Individual Maps", "ORM Packed Only", "Both (Individual + ORM)"]
        mode, ok = QInputDialog.getItem(self, "Batch Export Mode", "Select what to export:", items, 0, False)
        if not ok:
            return

        in_f = QFileDialog.getExistingDirectory(self, "Select INPUT Folder")
        if not in_f:
            return
        out_f = QFileDialog.getExistingDirectory(self, "Select OUTPUT Folder")
        if not out_f:
            return

        self.progress = QProgressDialog("Processing Batch...", "Cancel", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()

        self.bw = BatchWorker(in_f, out_f, self._sidebar.get_settings(), mode)
        self.bw.progress.connect(lambda t, c, m: (self.progress.setLabelText(t), self.progress.setMaximum(m), self.progress.setValue(c)))
        self.bw.done.connect(lambda: (self.progress.close(), QMessageBox.information(self, "Done", "Batch Export Complete!")))
        self.bw.start()

    def _schedule_base(self):
        if self._source_image is None:
            return
        sb = self._sidebar
        worker = HsvWorker(self._source_image, sb.s_hue.value(), sb.s_sat.value(), sb.s_val.value(), sb.s_tile.value())
        self._start_worker(worker, self._on_base_done, "Computing base texture...")

    def _schedule_height(self):
        if self._source_image is None:
            return
        sb = self._sidebar
        worker = HeightmapWorker(self._source_image, sb.s_hm_c.value(), sb.s_hm_b.value(), sb.cb_hm_inv.isChecked(), sb.s_tile.value())
        self._start_worker(worker, self._on_height_done, "Generating heightmap...")

    def _schedule_normal(self):
        if self._heightmap is None:
            return
        sb = self._sidebar
        worker = NormalMapWorker(self._heightmap, sb.s_nm_i.value(), sb.cb_nm_inv.isChecked())
        self._start_worker(worker, self._on_normal_done, "Generating normal map...")

    def _schedule_roughness(self):
        if self._source_image is None:
            return
        sb = self._sidebar
        worker = RoughnessWorker(self._source_image, sb.s_r_c.value(), sb.s_r_b.value(), sb.cb_r_inv.isChecked(), sb.s_tile.value())
        self._start_worker(worker, self._on_rough_done, "Generating roughness map...")

    def _schedule_metal(self):
        if self._source_image is None:
            return
        sb = self._sidebar
        worker = MetallicWorker(self._source_image, sb.s_m_c.value(), sb.s_m_b.value(), sb.cb_m_inv.isChecked(), sb.s_tile.value())
        self._start_worker(worker, self._on_metal_done, "Generating metallic map...")

    def _schedule_ao(self):
        if self._heightmap is None:
            return
        sb = self._sidebar
        worker = AoWorker(self._heightmap, sb.s_ao_c.value(), sb.s_ao_b.value(), int(sb.s_ao_blur.value()), False)
        self._start_worker(worker, self._on_ao_done, "Generating AO map...")

    def _start_worker(self, worker, callback, message: str):
        self.statusBar().showMessage(message)
        thread = ProcessingThread(worker)
        worker.finished.connect(callback)
        worker.error.connect(lambda e: self.statusBar().showMessage(f"Error: {e}"))
        thread.finished.connect(lambda: self._active_threads.remove(thread) if thread in self._active_threads else None)
        self._active_threads.append(thread)
        thread.start()

    def _sync_toggles(self):
        sb = self._sidebar
        if sb.hm_box.isChecked() and self._heightmap is not None:
            self._prev_height.set_image(self._heightmap)
            self._gl.set_heightmap(self._heightmap)
        else:
            self._prev_height.clear_image()
            self._gl.set_heightmap(None)

        if sb.nm_box.isChecked() and self._normal_map is not None:
            self._prev_normal.set_image(self._normal_map)
            self._gl.set_normal_map(self._normal_map)
        else:
            self._prev_normal.clear_image()
            self._gl.set_normal_map(None)

        if sb.rough_box.isChecked() and self._rough_map is not None:
            self._prev_rough.set_image(self._rough_map)
            self._gl.set_roughness_map(self._rough_map)
        else:
            self._prev_rough.clear_image()
            self._gl.set_roughness_map(None)

        if sb.metal_box.isChecked() and self._metal_map is not None:
            self._prev_metal.set_image(self._metal_map)
            self._gl.set_metal_map(self._metal_map)
        else:
            self._prev_metal.clear_image()
            self._gl.set_metal_map(None)

        if sb.ao_box.isChecked() and self._ao_map is not None:
            self._prev_ao.set_image(self._ao_map)
            self._gl.set_ao_map(self._ao_map)
        else:
            self._prev_ao.clear_image()
            self._gl.set_ao_map(None)

    def _on_base_done(self, result: np.ndarray):
        self._albedo_image = result
        self._prev_albedo.set_image(result)
        self._gl.set_albedo(result)
        self._schedule_height()
        self._schedule_roughness()
        self._schedule_metal()

    def _on_height_done(self, result: np.ndarray):
        self._heightmap = result
        self._sync_toggles()
        self._schedule_normal()
        self._schedule_ao()

    def _on_normal_done(self, result: np.ndarray):
        self._normal_map = result
        self._sync_toggles()

    def _on_rough_done(self, result: np.ndarray):
        self._rough_map = result
        self._sync_toggles()

    def _on_metal_done(self, result: np.ndarray):
        self._metal_map = result
        self._sync_toggles()

    def _on_ao_done(self, result: np.ndarray):
        self._ao_map = result
        self._sync_toggles()
        self.statusBar().showMessage("All maps ready")

    def _export_orm(self):
        if self._albedo_image is None:
            return
        f, _ = QFileDialog.getSaveFileName(self, "Export ORM Texture", "ORM_Packed.png", "PNG (*.png)")
        if f:
            orm = TextureProcessor.pack_orm(
                self._ao_map if self._sidebar.ao_box.isChecked() else None,
                self._rough_map if self._sidebar.rough_map.isChecked() else None,
                self._metal_map if self._sidebar.metal_box.isChecked() else None,
                self._albedo_image.shape[:2]
            )
            TextureProcessor.save_image(f, orm)
            self.statusBar().showMessage(f"Saved packed ORM map: {f}")

    def _export_all(self):
        if self._albedo_image is None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not folder:
            return

        sb = self._sidebar
        exports = [
            ("albedo.png", self._albedo_image, None),
            ("heightmap.png", self._heightmap, sb.hm_box),
            ("normal_map.png", self._normal_map, sb.nm_box),
            ("roughness.png", self._rough_map, sb.rough_box),
            ("metallic.png", self._metal_map, sb.metal_box),
            ("ao_map.png", self._ao_map, sb.ao_box),
        ]

        for name, img, box in exports:
            if img is not None and (box is None or box.isChecked()):
                TextureProcessor.save_image(os.path.join(folder, name), img)

        self.statusBar().showMessage("All enabled maps exported successfully!")