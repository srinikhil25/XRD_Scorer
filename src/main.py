"""
Main entry point for XRD Scorer application
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from .gui.main_window import MainWindow


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    PyInstaller creates a temp folder and stores path in _MEIPASS
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Running in development mode
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    # Set application icon (for taskbar, etc.)
    # Try multiple locations, including PyInstaller temp directory
    icon_paths = [
        get_resource_path("assets/icons/app_icon.ico"),
        get_resource_path("assets/icons/app_icon.png"),
        get_resource_path("icon.ico"),
        get_resource_path("icon.png"),
        # Fallback to development paths
        Path(__file__).parent.parent / "assets" / "icons" / "app_icon.ico",
        Path(__file__).parent.parent / "assets" / "icons" / "app_icon.png",
        Path(__file__).parent.parent / "icon.ico",
        Path(__file__).parent.parent / "icon.png",
    ]
    
    for icon_path in icon_paths:
        if icon_path.exists():
            try:
                app.setWindowIcon(QIcon(str(icon_path)))
                break
            except Exception:
                continue
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

