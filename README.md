# PyTextureStudio Professional v2.3

**PyTextureStudio** is a professional desktop application for generating PBR (Physically Based Rendering) textures for 3D engines, video games, and architectural rendering. Built with Python, PySide6, OpenCV, and OpenGL 3.3.

![Version](https://img.shields.io/badge/version-2.3-purple)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

---

## Features

### Emission Map Generator
- Generate emission maps based on texture brightness
- Threshold and intensity controls
- Full support in batch processing

### Built-in Preset Library
- **6 professional presets** ready to use:
  - Default
  - High Contrast
  - Glossy Surface  
  - Metallic Surface
  - Weathered Look
  - Soft Organic

### ORM Export
- Export packed ORM textures (Ambient Occlusion, Roughness, Metallic)
- Single PNG file for optimized workflow

### Batch Processing
- Process entire folders of textures
- Three export modes: Individual Maps, ORM Only, or Both

### Make Seamless
- Convert any image to a tileable seamless texture
- Center-patch blending algorithm

### 3D Viewport
- Real-time preview on cube or sphere
- Import custom .obj meshes
- Auto-rotation and manual camera controls
- Adjustable bump scale and AO strength

---

## Installation

```bash
# Clone or download the project
cd PyTextureStudio

# Install dependencies
pip install -r requirements.txt

# Launch the application
python main.py
```

### Requirements
- Python 3.10+
- OpenGL 3.3 compatible
- 4GB RAM minimum (8GB recommended)
- GPU with OpenGL 3.3+ support

---

## Quick Commands

| Action | Toolbar Button |
|--------|---------------|
| Load Image | Load Image |
| Make Seamless | Make Seamless |
| Save Preset | Save Preset |
| Load Preset | Load Preset |
| Batch Process | Batch Process Folder |
| Export ORM | Export ORM (UE/Unity) |
| Export All Maps | Export All Individual Maps |

---

## 3D Viewport Controls

| Action | Control |
|--------|---------|
| Rotate camera | Drag left mouse button |
| Zoom | Scroll wheel |
| Reset camera | Double click |
| Auto-rotation | "Auto-Rotate" checkbox |

---

## Project Structure

```
PyTextureStudio/
├── main.py                 # Application entry point
├── main_window.py          # Main UI, toolbar, viewport
├── texture_processor.py    # Image processing algorithms
├── gl_viewport.py          # OpenGL 3D viewport
├── config.py               # Configuration and presets
├── about_dialog.py         # About dialog
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## PBR Maps Generated

1. **Albedo/Base** - Color texture with HSV adjustments and tiling
2. **Heightmap** - Height map from contrast/brightness
3. **Normal Map** - DirectX/OpenGL normal map
4. **Roughness** - Roughness map (optional glossy invert)
5. **Metallic** - Metallic map with threshold control
6. **Ambient Occlusion** - AO derived from heightmap with blur
7. **Emission** - Emission map from brightness threshold

---

## Supported Formats

### Input
- PNG, JPEG, TGA, BMP

### Output
- PNG (recommended for quality)
- JPEG, TGA, BMP

---

## Configuration

User settings are saved in:
```
~/.pytexturestudio/
├── config.json      # Application settings
└── presets/         # User presets
```

### Available Settings
- Window dimensions
- Default export format
- Recent files history
- Last export folder

---

## Usage Tips

### For Tileable Textures
1. Use "Make Seamless" before generating maps
2. Adjust "Tiling" slider to control repetition
3. Check the result in the 3D viewport

### For Metallic Materials
1. Enable the Metallic Map checkbox
2. Adjust threshold and brightness for details
3. Use the "Metallic Surface" preset as starting point

### For Glossy Surfaces
1. Use the "Glossy Surface" preset
2. Enable "Invert (Glossy)" on Roughness
3. Reduce Normal Map intensity

### For Lights and Neon
1. Enable "Emission Map"
2. Adjust Threshold to isolate bright areas
3. Increase Intensity for glow effect

---

MIT License - See LICENSE for details.

---

