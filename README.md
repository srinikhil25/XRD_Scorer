# XRD Scorer

A desktop application for X-ray Diffraction (XRD) data analysis with support for multiple file formats, background subtraction, K-alpha stripping, and reference pattern matching.

## Features

- **Multi-format Support**: Load XRD data from various file formats:
  - XRDML (Bruker/PANalytical)
  - DAT (text format)
  - ASC (ASCII format)
  - TXT (generic text format)

- **Background Subtraction**: Multiple verified algorithms:
  - Iterative polynomial fitting (Sonneveld-Visser method)
  - Polynomial fitting
  - Rolling ball algorithm
  - Top-hat transform
  - SNIP (Sensitive Nonlinear Iterative Peak)

- **K-alpha Stripping**: Remove Kα2 component using:
  - Rachinger correction method
  - Iterative Rachinger correction

- **Reference Pattern Matching**: 
  - Load reference patterns from ICDD and Materials Project databases
  - Overlay reference patterns on experimental data
  - Support for JSON format reference patterns

- **Interactive Visualization**:
  - Real-time plotting with matplotlib
  - Show negative values after background subtraction
  - Overlay multiple patterns
  - Zoom and pan capabilities

- **User-Friendly Interface**:
  - Modern PyQt6 GUI
  - Intuitive controls
  - Extensible architecture for adding new features

## Installation

### Requirements

- Python 3.8 or higher
- See `requirements.txt` for dependencies

### Install from Source

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

### Create Executable (for distribution)

To create a standalone executable that can be installed on other desktops:

#### Using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --name="XRD Scorer" --windowed --onefile --add-data "data;data" run.py
```

The executable will be in the `dist` folder.

#### Using cx_Freeze:

```bash
pip install cx_Freeze
python setup.py build
```

## Usage

1. **Load XRD File**: Click "Load XRD File" or use File → Open to load your XRD data file

2. **Background Subtraction**:
   - Select a method from the dropdown
   - Adjust parameters (e.g., polynomial degree)
   - Click "Apply Background Subtraction"
   - Negative values will be shown in red

3. **K-alpha Stripping**:
   - Select method (Rachinger or Iterative Rachinger)
   - Set wavelength (default: 1.54056 Å for Cu Kα1)
   - Click "Apply K-alpha Stripping"

4. **Reference Pattern Overlay**:
   - Search for a reference pattern in the database
   - Click "Overlay Selected Pattern" to see it on your data

5. **Reset**: Click "Reset to Original" to undo all processing

## File Formats

### Supported Input Formats

- **XRDML**: XML-based format from Bruker and PANalytical instruments
- **DAT**: Space/tab-separated two-column format (2θ, Intensity)
- **ASC**: ASCII format from PANalytical instruments
- **TXT**: Generic text format with two columns

### Reference Pattern Format

Reference patterns should be in JSON format. Two formats are supported:

**Materials Project format:**
```json
{
  "wavelength": {"element": "Cu", "in_angstroms": 1.54184},
  "pattern": [[amplitude, [h, k, l], two_theta, d_spacing], ...]
}
```

**Simple format:**
```json
{
  "id": "pattern_id",
  "name": "Pattern Name",
  "peaks": [
    {"d_spacing": 3.247, "intensity": 100, "hkl": "110"},
    ...
  ]
}
```

## Project Structure

```
XRD_Scorer/
├── src/
│   ├── core/           # Core processing modules
│   │   ├── file_parser.py
│   │   ├── background_subtraction.py
│   │   ├── kalpha_stripping.py
│   │   └── reference_pattern.py
│   ├── gui/            # GUI modules
│   │   └── main_window.py
│   ├── visualization/  # Plotting modules
│   │   └── plotter.py
│   └── main.py
├── data/               # Reference pattern databases
├── run.py             # Application entry point
├── setup.py           # Installation script
└── requirements.txt   # Dependencies
```

## Adding New Features

The application is designed to be extensible. To add new features:

1. **New Processing Algorithm**: Add to `src/core/` with a consistent interface
2. **New File Format**: Add parser to `src/core/file_parser.py`
3. **New GUI Component**: Add widget to `src/gui/main_window.py` or create new module
4. **New Visualization**: Extend `src/visualization/plotter.py`

## Background Subtraction Algorithms

The application implements several verified background subtraction methods:

- **Iterative Polynomial**: Recommended for most cases, iteratively excludes peaks from fitting
- **Polynomial**: Simple polynomial fit to entire spectrum
- **Rolling Ball**: Morphological opening operation
- **Top-hat**: Difference between original and morphological opening
- **SNIP**: Sensitive Nonlinear Iterative Peak clipping

## K-alpha Stripping

The Rachinger correction method is used to remove the Kα2 component:

- Calculates angular separation between Kα1 and Kα2 peaks
- Subtracts scaled and shifted spectrum
- Default wavelength ratio: 1.0025 (Cu radiation)
- Default intensity ratio: 0.5 (Cu radiation)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues, questions, or feature requests, please [add contact information or issue tracker link].

