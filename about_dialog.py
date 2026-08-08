"""
about_dialog.py
---------------
About dialog and application information for PyTextureStudio
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                                QTextBrowser, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AboutDialog(QDialog):
    """Professional about dialog with application info and credits"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PyTextureStudio")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("PyTextureStudio")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #a78bfa; padding: 10px;")
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 3.0.0 Professional")
        version.setFont(QFont("Segoe UI", 12))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #9ca3af;")
        layout.addWidget(version)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #3a3a48;")
        layout.addWidget(line)
        
        # Description
        desc = QTextBrowser()
        desc.setHtml("""
        <div style='color: #d4d4d8; font-size: 13px; line-height: 1.6;'>
        <p><strong>PyTextureStudio</strong> è un'applicazione professionale per la generazione 
        di texture PBR (Physically Based Rendering) per motori 3D e videogiochi.</p>
        
        <p style='margin-top: 15px;'><strong>Funzionalità Principali:</strong></p>
        <ul>
            <li>Generazione mappe PBR: Height, Normal, Roughness, Metallic, AO, Emission</li>
            <li>Creazione texture seamless (tileable)</li>
            <li>Packing ORM per Unreal Engine, Unity, Godot</li>
            <li>Viewport 3D OpenGL con illuminazione dinamica</li>
            <li>Processo batch per cartelle intere</li>
            <li>Sistema di preset personalizzabili</li>
            <li>Supporto formati: PNG, JPEG, TGA, BMP, EXR, HDR</li>
        </ul>
        
        <p style='margin-top: 15px;'><strong>Tecnologie:</strong> Python, PySide6, OpenCV, OpenGL 3.3</p>
        </div>
        """)
        desc.setMaximumHeight(200)
        desc.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
        """)
        layout.addWidget(desc)
        
        # Credits
        credits_label = QLabel("© 2024 PyTextureStudio - Tutti i diritti riservati")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        layout.addWidget(credits_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Chiudi")
        close_btn.setObjectName("ExportBtn")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
