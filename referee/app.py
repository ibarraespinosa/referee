#!/usr/bin/env python3
"""
Referee - Entry point.
Usage:
    referee [file.pdf]
"""
import sys
import os

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from referee.main_window import MainWindow

def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Referee")
    app.setOrganizationName("OpenSourceReviewer")

    initial_pdf = sys.argv[1] if len(sys.argv) > 1 else None
    window = MainWindow(initial_pdf=initial_pdf)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
