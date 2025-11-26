"""
Script to build executable using PyInstaller
Run: python build_exe.py
"""

import PyInstaller.__main__
import sys
from pathlib import Path

# Get the data directory path
data_dir = Path(__file__).parent / "data"
data_path = str(data_dir)

PyInstaller.__main__.run([
    'run.py',
    '--name=XRD_Scorer',
    '--windowed',  # No console window
    '--onefile',  # Single executable
    f'--add-data={data_path};data',  # Include data directory
    '--icon=NONE',  # Add icon file path if you have one
    '--clean',
])

