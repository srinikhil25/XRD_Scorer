# Quick Start Guide

## Installation

1. **Install Python 3.8+** if not already installed

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run.py
   ```

## Basic Usage

### 1. Load an XRD File

- Click **"Load XRD File"** button or use **File → Open** (Ctrl+O)
- Supported formats: `.xrdml`, `.dat`, `.asc`, `.txt`
- The spectrum will appear in the plot window

### 2. Background Subtraction

1. Select a method from the **"Method"** dropdown:
   - **iterative_polynomial** (recommended) - Best for most cases
   - **polynomial** - Simple polynomial fit
   - **rolling_ball** - Morphological method
   - **tophat** - Top-hat transform
   - **snip** - SNIP algorithm

2. Adjust **Polynomial Degree** if using polynomial methods (default: 6)

3. Click **"Apply Background Subtraction"**

4. Negative values (if any) will be shown in red on the plot

### 3. K-alpha Stripping

1. Select method:
   - **rachinger** - Standard Rachinger correction
   - **iterative_rachinger** - Iterative version

2. Set **Wavelength** (default: 1.54056 Å for Cu Kα1)

3. Click **"Apply K-alpha Stripping"**

### 4. Reference Pattern Overlay

1. Type a search term in the **"Search"** box (e.g., "Ti3C2", "Cu")

2. Click **"Overlay Selected Pattern"**

3. The reference pattern will appear as a green dashed line

### 5. Reset

- Click **"Reset to Original"** to undo all processing and return to original data

## Tips

- **Negative values**: After background subtraction, negative values are shown in red. This is normal and indicates regions where the background was over-subtracted.

- **Reference patterns**: The application automatically loads patterns from `data/examples/reference_patterns/`. You can load additional databases via **Tools → Load Reference Database**.

- **File formats**: The parser tries to auto-detect format. If a file doesn't load correctly, check that it has two columns (2θ and Intensity).

- **Wavelength**: For accurate K-alpha stripping, ensure the wavelength matches your X-ray source (Cu Kα1 = 1.54056 Å, Co Kα = 1.79026 Å, Mo Kα = 0.70932 Å).

## Creating an Executable

To create a standalone executable for distribution:

```bash
pip install pyinstaller
python build_exe.py
```

The executable will be in the `dist` folder and can be distributed to other computers without requiring Python installation.

## Troubleshooting

- **Import errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`

- **File won't load**: Check file format. Try opening in a text editor to verify it contains two columns of numbers.

- **Plot not updating**: Click "Reset to Original" and try again.

- **Reference patterns not showing**: Make sure the JSON files are in the correct format (see README.md).

