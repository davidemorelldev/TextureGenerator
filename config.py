"""
config.py
---------
Application configuration and constants for PyTextureStudio
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
import json
from pathlib import Path


@dataclass
class AppSettings:
    """Application settings with defaults"""
    # Window settings
    window_width: int = 1600
    window_height: int = 1000
    theme: str = "dark"  # dark, light
    
    # Texture settings
    default_export_format: str = "PNG"
    export_quality: int = 95  # For JPEG
    auto_save_preset: bool = True
    
    # Processing settings
    max_texture_size: int = 4096
    use_gpu_acceleration: bool = True
    cache_enabled: bool = True
    cache_size_mb: int = 512
    
    # Viewport settings
    default_mesh: str = "Sphere"
    auto_rotate_enabled: bool = True
    rotation_speed: float = 0.008
    default_camera_distance: float = 3.5
    
    # Recent files
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10
    
    # Presets
    last_preset_folder: str = ""
    last_export_folder: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Built-in presets library
BUILTIN_PRESETS = {
    "Default": {
        'hue': 0.0, 'sat': 1.0, 'val': 1.0, 'tile': 1.0,
        'hm_on': True, 'hm_c': 1.0, 'hm_b': 0.0, 'hm_inv': False,
        'nm_on': True, 'nm_i': 2.0, 'nm_inv': False,
        'r_on': True, 'r_c': 1.0, 'r_b': 0.0, 'r_inv': False,
        'm_on': False, 'm_c': 2.0, 'm_b': -0.5, 'm_inv': False,
        'ao_on': True, 'ao_c': 1.5, 'ao_b': -0.1, 'ao_blur': 3.0
    },
    "High Contrast": {
        'hue': 0.0, 'sat': 1.2, 'val': 1.1, 'tile': 1.0,
        'hm_on': True, 'hm_c': 2.0, 'hm_b': 0.0, 'hm_inv': False,
        'nm_on': True, 'nm_i': 3.0, 'nm_inv': False,
        'r_on': True, 'r_c': 2.0, 'r_b': 0.0, 'r_inv': False,
        'm_on': True, 'm_c': 2.5, 'm_b': -0.3, 'm_inv': False,
        'ao_on': True, 'ao_c': 2.0, 'ao_b': -0.2, 'ao_blur': 5.0
    },
    "Glossy Surface": {
        'hue': 0.0, 'sat': 1.0, 'val': 1.0, 'tile': 1.0,
        'hm_on': True, 'hm_c': 0.8, 'hm_b': 0.1, 'hm_inv': False,
        'nm_on': True, 'nm_i': 1.5, 'nm_inv': False,
        'r_on': True, 'r_c': 0.7, 'r_b': 0.2, 'r_inv': True,
        'm_on': False, 'm_c': 2.0, 'm_b': -0.5, 'm_inv': False,
        'ao_on': True, 'ao_c': 1.3, 'ao_b': 0.0, 'ao_blur': 2.0
    },
    "Metallic Surface": {
        'hue': 0.0, 'sat': 0.8, 'val': 0.9, 'tile': 1.0,
        'hm_on': True, 'hm_c': 1.5, 'hm_b': -0.1, 'hm_inv': False,
        'nm_on': True, 'nm_i': 2.5, 'nm_inv': False,
        'r_on': True, 'r_c': 1.2, 'r_b': -0.1, 'r_inv': False,
        'm_on': True, 'm_c': 1.8, 'm_b': 0.0, 'm_inv': False,
        'ao_on': True, 'ao_c': 1.8, 'ao_b': -0.15, 'ao_blur': 4.0
    },
    "Weathered Look": {
        'hue': -10.0, 'sat': 0.7, 'val': 0.85, 'tile': 1.0,
        'hm_on': True, 'hm_c': 2.5, 'hm_b': 0.1, 'hm_inv': False,
        'nm_on': True, 'nm_i': 4.0, 'nm_inv': False,
        'r_on': True, 'r_c': 1.8, 'r_b': 0.1, 'r_inv': False,
        'm_on': True, 'm_c': 3.0, 'm_b': -0.2, 'm_inv': True,
        'ao_on': True, 'ao_c': 2.2, 'ao_b': -0.3, 'ao_blur': 6.0
    },
    "Soft Organic": {
        'hue': 5.0, 'sat': 1.1, 'val': 1.05, 'tile': 1.0,
        'hm_on': True, 'hm_c': 0.6, 'hm_b': 0.05, 'hm_inv': False,
        'nm_on': True, 'nm_i': 1.2, 'nm_inv': False,
        'r_on': True, 'r_c': 0.8, 'r_b': 0.0, 'r_inv': False,
        'm_on': False, 'm_c': 2.0, 'm_b': -0.5, 'm_inv': False,
        'ao_on': True, 'ao_c': 1.2, 'ao_b': 0.0, 'ao_blur': 4.0
    }
}

# Engine-specific ORM configurations
ENGINE_PRESETS = {
    "Unreal Engine": {
        'orm_channels': {'A': 'R', 'R': 'G', 'M': 'B'},
        'normal_format': 'DirectX',
        'export_format': 'PNG',
        'description': 'AO(R), Roughness(G), Metallic(B)'
    },
    "Unity": {
        'orm_channels': {'A': 'R', 'R': 'G', 'M': 'B'},
        'normal_format': 'OpenGL',
        'export_format': 'PNG',
        'description': 'AO(R), Roughness(G), Metallic(B)'
    },
    "Godot": {
        'orm_channels': {'A': 'R', 'R': 'G', 'M': 'B'},
        'normal_format': 'OpenGL',
        'export_format': 'PNG',
        'description': 'AO(R), Roughness(G), Metallic(B)'
    },
    "Three.js": {
        'orm_channels': {'A': 'R', 'R': 'G', 'M': 'B'},
        'normal_format': 'OpenGL',
        'export_format': 'JPG',
        'description': 'AO(R), Roughness(G), Metallic(B)'
    }
}

SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr', '.hdr']
EXPORT_FORMATS = ['PNG', 'JPEG', 'TGA', 'BMP']

CONFIG_FILE = Path.home() / ".pytexturestudio" / "config.json"
PRESETS_FOLDER = Path.home() / ".pytexturestudio" / "presets"


def ensure_config_dirs():
    """Ensure configuration directories exist"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRESETS_FOLDER.mkdir(parents=True, exist_ok=True)


def load_settings() -> AppSettings:
    """Load application settings from file"""
    ensure_config_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return AppSettings.from_dict(data)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading settings: {e}")
    return AppSettings()


def save_settings(settings: AppSettings):
    """Save application settings to file"""
    ensure_config_dirs()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings.to_dict(), f, indent=2)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error saving settings: {e}")


def add_recent_file(settings: AppSettings, filepath: str) -> AppSettings:
    """Add a file to recent files list"""
    if filepath in settings.recent_files:
        settings.recent_files.remove(filepath)
    settings.recent_files.insert(0, filepath)
    settings.recent_files = settings.recent_files[:settings.max_recent_files]
    return settings


def get_builtin_presets() -> Dict[str, Dict]:
    """Get built-in presets library"""
    return BUILTIN_PRESETS.copy()


def get_engine_preset(engine_name: str) -> Dict:
    """Get engine-specific export preset"""
    return ENGINE_PRESETS.get(engine_name, ENGINE_PRESETS["Unreal Engine"])
