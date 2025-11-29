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

# Get icon path if it exists
icon_path = Path(__file__).parent / "assets" / "icons" / "app_icon.ico"
icon_args = []
assets_args = []

if icon_path.exists():
    # Add icon for executable file icon
    icon_args = [f'--icon={icon_path}']
    # Also include icon in the build so it can be loaded at runtime
    assets_dir = Path(__file__).parent / "assets"
    assets_path = str(assets_dir)
    assets_args = [f'--add-data={assets_path};assets']
    print(f"Using icon: {icon_path}")
    print(f"Including assets directory: {assets_path}")
else:
    print("Warning: No icon file found at assets/icons/app_icon.ico")
    print("The executable will use the default icon. To add an icon:")
    print("  1. Create a .ico file (256x256 or 512x512 pixels recommended)")
    print("  2. Place it at: assets/icons/app_icon.ico")
    print("  3. Rebuild the executable")

PyInstaller.__main__.run([
    'run.py',
    '--name=XRD_Scorer',
    '--windowed',  # No console window
    '--onefile',  # Single executable
    f'--add-data={data_path};data',  # Include data directory
    *assets_args,  # Include assets directory (for icon at runtime)
    *icon_args,  # Add icon for executable file
    '--clean',
])

