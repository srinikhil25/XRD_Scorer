"""
Main entry point for XRD Scorer application
"""

import sys
from PyQt6.QtWidgets import QApplication
from .gui.main_window import MainWindow


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

