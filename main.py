"""
main.py
-------
PyTextureStudio - Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from main_window import MainWindow, DARK_QSS


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyTextureStudio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PyTextureStudio")

    app.setStyleSheet(DARK_QSS)

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
