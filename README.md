# PyTextureStudio Professional v3.0 🎨

**PyTextureStudio** è un'applicazione desktop professionale per la generazione di texture PBR (Physically Based Rendering) per motori 3D, videogiochi e rendering architettonico. Sviluppata con Python, PySide6, OpenCV e OpenGL 3.3.

![Version](https://img.shields.io/badge/version-3.0.0-purple)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)

---

## ✨ Nuove Funzionalità v3.0

### 🔥 Emission Map Generator
- Genera mappe di emissione basate sulla luminosità della texture
- Controllo soglia (threshold) e intensità
- Supporto completo nel batch processing

### 📚 Libreria di Preset Integrati
- **6 preset professionali** pronti all'uso:
  - Default
  - High Contrast
  - Glossy Surface  
  - Metallic Surface
  - Weathered Look
  - Soft Organic

### ⚙️ Configurazione Engine-Specific
- Export ORM ottimizzato per:
  - Unreal Engine
  - Unity
  - Godot
  - Three.js

### 💾 Gestione File Recenti
- Accesso rapido alle ultime texture aperte
- Fino a 10 file nella cronologia

### 🎯 Miglioramenti UI/UX
- Menu bar completo con scorciatoie da tastiera
- Toolbar con icone intuitive
- Status bar con messaggi di conferma (✓)
- Dialog About professionale
- Salvataggio automatico impostazioni finestra

### 📁 Sistema di Preset Avanzato
- Salvataggio preset in cartella dedicata (~/.pytexturestudio/presets/)
- Menu Presets con accesso a built-in e user preset
- Caricamento one-click

---

## 🚀 Installazione

```bash
# Clona o scarica il progetto
cd PyTextureStudio

# Installa le dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python main.py
```

### Requisiti
- Python 3.10+
- OpenGL 3.3 compatibile
- 4GB RAM minimo (8GB consigliato)
- GPU con supporto OpenGL 3.3+

---

## 📋 Comandi Rapidi

| Azione | Scorciatoia | Menu |
|--------|-------------|------|
| Apri Texture | `Ctrl+O` | File → Open |
| Salva Preset | `Ctrl+S` | File → Save Preset |
| Carica Preset | `Ctrl+Shift+O` | File → Load Preset |
| Batch Process | `Ctrl+B` | File → Batch Process |
| Make Seamless | `Ctrl+M` | Tools → Make Seamless |
| Export ORM | `Ctrl+E` | Tools → Export ORM |
| Export All | `Ctrl+Shift+E` | Tools → Export All |
| Esci | `Ctrl+Q` | File → Exit |

---

## 🎮 Controlli Viewport 3D

| Azione | Controllo |
|--------|-----------|
| Ruota camera | Drag mouse sinistro |
| Zoom | Scroll wheel |
| Reset camera | Doppio click |
| Auto-rotazione | Checkbox "Auto-Rotate" |

---

## 🗂️ Struttura Progetto

```
PyTextureStudio/
├── main.py                 # Entry point applicazione
├── main_window.py          # UI principale, menu, toolbar
├── texture_processor.py    # Algoritmi processing immagini
├── gl_viewport.py          # Viewport OpenGL 3D
├── config.py               # Configurazione e preset
├── about_dialog.py         # Dialog informazioni
├── requirements.txt        # Dipendenze Python
└── README.md              # Questo file
```

---

## 🎨 Mappe PBR Generate

1. **Albedo/Base** - Texture colore con regolazioni HSV e tiling
2. **Heightmap** - Mappa altezza da contrasto/luminosità
3. **Normal Map** - Mappa normali DirectX/OpenGL
4. **Roughness** - Mappa rugosità (opzionale glossy invert)
5. **Metallic** - Mappa metallicità con threshold
6. **Ambient Occlusion** - AO derivata da heightmap con blur
7. **Emission** - Nuova! Mappa emissione da soglia luminosità

---

## 📦 Formati Supportati

### Input
- PNG, JPEG, TGA, BMP, EXR, HDR

### Output
- PNG (consigliato per qualità)
- JPEG (per dimensioni ridotte)
- TGA, BMP

---

## 🔧 Configurazione

Le impostazioni utente sono salvate in:
```
~/.pytexturestudio/
├── config.json      # Impostazioni applicazione
└── presets/         # Preset utente
```

### Impostazioni Disponibili
- Dimensioni finestra
- Preset engine preferito
- Formato export default
- Cartelle recenti
- Cronologia file

---

## 💡 Consigli d'Uso

### Per Texture Tileable
1. Attiva "Make Seamless" prima di generare le mappe
2. Regola "Tiling" per controllare la ripetizione
3. Verifica nel viewport 3D con la sfera

### Per Materiali Metallici
1. Usa il preset "Metallic Surface"
2. Attiva la checkbox "Metallic Map"
3. Regola threshold e brightness per dettagli

### Per Superfici Lucide
1. Usa il preset "Glossy Surface"  
2. Attiva "Invert (Glossy)" su Roughness
3. Riduci intensità Normal Map

### Per Luci e Neon
1. Attiva "Emission Map"
2. Regola Threshold per isolare aree luminose
3. Aumenta Intensity per effetto glow

---

## 🛠️ Sviluppo

### Aggiungere un Nuovo Worker
```python
class NewWorker(_BaseWorker):
    def __init__(self, image, param1, param2):
        super().__init__()
        self._image = image
        self._param1 = param1
        self._param2 = param2
    
    def run(self):
        try:
            result = process(self._image, self._param1, self._param2)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### Aggiungere un Preset
Modifica `config.py`:
```python
BUILTIN_PRESETS["MyPreset"] = {
    'hue': 0.0, 'sat': 1.0, ...
}
```

---

## 📄 Licenza

MIT License - Vedi LICENSE per dettagli.

---

