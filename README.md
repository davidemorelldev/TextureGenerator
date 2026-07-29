# PyTextureStudio

A PySide6 and OpenGL desktop app for processing 3D textures, generating PBR maps starting from an albedo (Height, Normal, Roughness, Metallic, AO), creating seamless tiles, and packing ORM textures for Unreal Engine and Unity.

## Requirements

- Python 3.10+
- OpenGL 3.3 compatible graphics drivers

## Setup & Running

```bash
pip install -r requirements.txt
python main.py
```

## Features

- **Base Texture & Seamless**: Adjust Hue, Saturation, Value, and Tiling. Includes a **Make Seamless** tool to generate tileable textures via center-patch blending.
- **PBR Map Generation**:
  - **Heightmap**: Contrast, brightness, and inversion controls.
  - **Normal Map**: Generated via Sobel filters with intensity scaling and DirectX / OpenGL Y-channel toggle.
  - **Roughness & Metallic Maps**: Custom contrast/threshold and brightness settings (with Glossy invert option).
  - **Ambient Occlusion**: Heightmap-derived AO with Gaussian blur radius control.
- **ORM Channel Packing**: Packs Ambient Occlusion (Red), Roughness (Green), and Metallic (Blue) into a single `ORM_Packed.png` texture.
- **3D Viewport**:
  - Rendered using OpenGL 3.3 Core and custom GLSL shaders (Key, Fill, and Rim lighting).
  - Built-in Cube and Sphere primitives, plus custom `.obj` mesh loading with automatic UV and normal calculation.
  - Mouse orbit rotation, zoom, auto-rotate toggle, and bump/AO strength sliders.
- **Batch Processing & Presets**:
  - Asynchronous batch conversion of entire image folders using `QThread` workers.
  - Save and load UI parameter configurations to JSON files.

## File Overview

```
├── main.py               # Entry point
├── main_window.py        # MainWindow UI layout, sidebar controls, presets, and batch logic
├── texture_processor.py  # Image processing algorithms and async worker threads
├── gl_viewport.py        # QOpenGLWidget viewport, OBJ importer, and GLSL shaders
└── requirements.txt      # Dependencies
```

## Controls Quick Reference

| Action | Control / Gesture |
|--------|-------------------|
| Load Texture | **Load Image** button |
| Make Tileable | **Make Seamless** button |
| Load 3D Model | **Import .obj** button |
| Save/Load Settings | **Save Preset** / **Load Preset** buttons |
| Batch Process | **Batch Process Folder** button |
| Export Packed ORM | **Export ORM (UE/Unity)** button |
| Export Maps | **Export All Individual Maps** button |
| Orbit Camera | Left mouse drag in viewport |
| Zoom Camera | Mouse scroll wheel in viewport |
| Reset Camera | Double-click in viewport |


