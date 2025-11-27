# XRD Scorer v1.0.0 - Technical Documentation

**Version:** 1.0.0  
**Date:** 27 November 2025  
**Document Type:** Technical Specification and User Manual

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [File Format Support](#file-format-support)
4. [Background Subtraction Algorithms](#background-subtraction-algorithms)
5. [K-alpha Stripping Algorithms](#k-alpha-stripping-algorithms)
6. [Peak Detection Algorithms](#peak-detection-algorithms)
7. [Reference Pattern Matching](#reference-pattern-matching)
8. [Data Visualization](#data-visualization)
9. [Project Management System](#project-management-system)
10. [User Interface](#user-interface)
11. [Mathematical Formulations](#mathematical-formulations)
12. [Implementation Details](#implementation-details)
13. [References](#references)

---

## 1. Executive Summary

XRD Scorer is a desktop application designed for comprehensive X-ray Diffraction (XRD) data analysis. The software provides advanced processing capabilities including background subtraction, K-alpha stripping, peak detection, and reference pattern matching. Version 1.0.0 supports multiple file formats, implements verified algorithms from the literature, and provides publication-ready visualizations.

### Key Features

- **Multi-format File Support**: XRDML, DAT, ASC, TXT, and RAW binary formats
- **Background Subtraction**: Five verified algorithms
- **K-alpha Stripping**: Rachinger correction methods
- **Peak Detection**: Four different algorithms with prominence-based filtering
- **Reference Pattern Matching**: ICDD and Materials Project database support
- **Project Management**: Automatic saving of all analysis steps for AI integration
- **Publication-Ready Visualization**: Professional graphs with HKL-labeled reference patterns

---

## 2. System Overview

### 2.1 Architecture

XRD Scorer follows a modular architecture:

```
XRD_Scorer/
├── src/
│   ├── core/              # Core processing algorithms
│   │   ├── file_parser.py          # File format parsers
│   │   ├── background_subtraction.py  # Background removal
│   │   ├── kalpha_stripping.py      # Kα2 removal
│   │   ├── peak_detection.py        # Peak identification
│   │   ├── reference_pattern.py     # Reference database
│   │   └── project_manager.py        # Project persistence
│   ├── gui/               # User interface
│   │   └── main_window.py
│   ├── visualization/     # Plotting and visualization
│   │   └── plotter.py
│   └── main.py            # Application entry point
├── data/                  # Reference pattern databases
└── projects/              # Analysis project storage
```

### 2.2 Technology Stack

- **Python 3.8+**: Core language
- **PyQt6**: Graphical user interface framework
- **NumPy**: Numerical computations
- **SciPy**: Scientific algorithms (signal processing, optimization)
- **Matplotlib**: Data visualization
- **PyInstaller**: Executable packaging

### 2.3 Data Flow

1. **File Loading**: Parse XRD data file → Extract 2θ and intensity arrays
2. **Processing**: Apply background subtraction → Apply K-alpha stripping (optional)
3. **Analysis**: Detect peaks → Match with reference patterns
4. **Visualization**: Plot processed data with overlays
5. **Persistence**: Save all steps to project folder

---

## 3. File Format Support

### 3.1 Supported Formats

XRD Scorer supports five file formats:

1. **XRDML** (.xrdml): XML-based format from Bruker/PANalytical instruments
2. **DAT** (.dat): Space/tab-separated text format
3. **ASC** (.asc): ASCII format from PANalytical instruments
4. **TXT** (.txt): Generic text format
5. **RAW** (.raw): Binary format from Rigaku/PANalytical instruments

### 3.2 File Parsing Implementation

#### 3.2.1 XRDML Format

XRDML files are XML-based and contain structured data with namespaces. The parser:

1. Parses XML using ElementTree
2. Extracts wavelength from `<kAlpha1>` element
3. Extracts two-theta values from `<listPositions>` elements
4. Extracts intensity values from `<counts>` elements

**Namespace:** `http://www.xrdml.com/XRDMeasurement/1.5`

#### 3.2.2 Text Formats (DAT, ASC, TXT)

Text formats are parsed by:
1. Reading file line-by-line
2. Skipping header lines (starting with `#` or non-numeric)
3. Splitting lines by whitespace/tabs/commas
4. Extracting first column as 2θ, second column as intensity
5. Validating numeric values

**Format:** `2θ_value  intensity_value`

#### 3.2.3 RAW Binary Format

RAW files are binary and require special parsing:

**Structure:**
- Header section (metadata, typically 3-4 KB)
- Data count (4-byte unsigned integer, little-endian)
- Intensity data (float32 array, little-endian)

**Parsing Algorithm:**

1. **Method 1: Known Structure Detection**
   - Look for data count at offset where `offset + 4 + count*4 = file_size`
   - Validate count is reasonable (100-100,000 points)
   - Extract start/end/step angles from header (offsets 3010, 3014, 3018)

2. **Method 2: Header Value Search**
   - Search for start angle (4-10°), end angle (5-120°), step (0.01-0.1°)
   - Calculate expected data count: `count = (end - start) / step + 1`
   - Try common header sizes (512, 1024, 2048, 3238, 4096 bytes)

3. **Method 3: End-of-File Detection**
   - Assume data is last N float32 values
   - Calculate from file size and header remainder

4. **Method 4: Validation and Correction**
   - If calculated end angle > 120°, likely incorrect
   - For standard 5-90° scans, recalculate step: `step = (90 - start) / (count - 1)`
   - Cap unreasonable values at 120°

**Two-Theta Calculation:**

```python
# If header values are valid:
two_theta = np.linspace(start_angle, end_angle, data_count)

# If header values are invalid:
calculated_end = start_angle + (data_count - 1) * step
# Validate and correct if needed
if calculated_end > 120.0 and start_angle in [4.0, 6.0]:
    # Assume standard 5-90° range
    inferred_step = (90.0 - start_angle) / (data_count - 1)
    two_theta = np.linspace(start_angle, 90.0, data_count)
```

---

## 4. Background Subtraction Algorithms

Background subtraction removes the continuous background signal from XRD spectra, leaving only the diffraction peaks. XRD Scorer implements five verified algorithms.

### 4.1 Polynomial Fitting

**Method:** Simple polynomial regression to entire spectrum

**Mathematical Formulation:**

A polynomial of degree `n` is fitted to the data:

\[
P_n(2θ) = \sum_{i=0}^{n} a_i (2θ)^i
\]

where \(a_i\) are polynomial coefficients determined by least-squares fitting:

\[
\min_{a_i} \sum_{j=1}^{N} \left[ I(2θ_j) - P_n(2θ_j) \right]^2
\]

**Background:** \(B(2θ) = P_n(2θ)\)

**Corrected Intensity:** \(I_{corr}(2θ) = I(2θ) - B(2θ)\)

**Implementation:**
- Uses `numpy.polyfit()` for coefficient calculation
- Default degree: 6
- Negative values are preserved (not clipped to zero)

**Reference:** Standard polynomial regression method

### 4.2 Iterative Polynomial Fitting (Sonneveld-Visser Method)

**Method:** Iteratively fits polynomial while excluding peak regions

**Algorithm:**

1. Initialize mask: \(M^{(0)} = \{1, 1, ..., 1\}\) (all points included)
2. For iteration \(k = 1, 2, ..., N_{iter}\):
   - Fit polynomial \(P_n^{(k)}(2θ)\) to points where \(M^{(k-1)} = 1\)
   - Calculate residuals: \(R^{(k)}(2θ) = I(2θ) - P_n^{(k)}(2θ)\)
   - Update mask: \(M^{(k)}[j] = 1\) if \(R^{(k)}(2θ_j) < τ \cdot I_{max}\), else 0
3. Final background: \(B(2θ) = P_n^{(N_{iter})}(2θ)\)

**Parameters:**
- `degree`: Polynomial degree (default: 6)
- `iterations`: Number of iterations (default: 10)
- `threshold`: Exclusion threshold as fraction of max intensity (default: 0.1)

**Mathematical Formulation:**

\[
M^{(k)}[j] = \begin{cases}
1 & \text{if } R^{(k)}(2θ_j) < τ \cdot \max(I) \\
0 & \text{otherwise}
\end{cases}
\]

\[
P_n^{(k)}(2θ) = \arg\min_{P} \sum_{j: M^{(k-1)}[j]=1} \left[ I(2θ_j) - P(2θ_j) \right]^2
\]

**Reference:** Sonneveld, E. J., & Visser, J. W. (1975). Automatic collection of powder data from photographs. *Journal of Applied Crystallography*, 8(1), 1-7.

### 4.3 Rolling Ball Algorithm

**Method:** Morphological opening operation using a rolling ball (structuring element)

**Mathematical Formulation:**

The rolling ball algorithm uses morphological opening:

\[
B(2θ) = (I \ominus S) \oplus S
\]

where:
- \(\ominus\) is erosion: \((I \ominus S)[j] = \min_{i \in S} I[j+i]\)
- \(\oplus\) is dilation: \((I \oplus S)[j] = \max_{i \in S} I[j+i]\)
- \(S\) is the structuring element (ball) of radius \(r\)

**Implementation:**
- Ball radius: Auto-determined as `max(50, 5% of data points)`
- Uses `scipy.ndimage.grey_opening()` for morphological opening
- Additional Gaussian smoothing: \(B_{smooth} = G_\sigma * B\), where \(\sigma = r/10\)

**Corrected Intensity:** \(I_{corr}(2θ) = I(2θ) - B_{smooth}(2θ)\)

**Reference:** Sternberg, S. R. (1983). Biomedical image processing. *Computer*, 16(1), 22-34.

### 4.4 Top-Hat Transform

**Method:** Difference between original and morphological opening

**Mathematical Formulation:**

\[
B(2θ) = (I \ominus S) \oplus S
\]

\[
I_{corr}(2θ) = I(2θ) - B(2θ)
\]

This is equivalent to the top-hat transform:

\[
I_{corr}(2θ) = I(2θ) - \text{opening}(I, S)
\]

**Implementation:**
- Structure size: Auto-determined as `max(50, 5% of data points)`
- Uses `scipy.ndimage.grey_opening()`

**Reference:** Mathematical morphology operations in image processing

### 4.5 SNIP (Sensitive Nonlinear Iterative Peak) Algorithm

**Method:** Iterative clipping algorithm that progressively removes peaks

**Algorithm:**

1. Initialize: \(B^{(0)}(2θ) = I(2θ)\)
2. For iteration \(k = 1, 2, ..., N_{iter}\):
   - Window size: \(w_k = \lfloor N \cdot f^k \rfloor\) where \(f\) is reduction factor
   - For each point \(j\):
     \[
     B^{(k)}[j] = \min\left(B^{(k-1)}[j], \min_{i \in [j-w_k/2, j+w_k/2]} B^{(k-1)}[i]\right)
     \]
3. Background: \(B(2θ) = B^{(N_{iter})}(2θ)\)

**Parameters:**
- `iterations`: Number of iterations (default: 100)
- `reduction_factor`: Window reduction factor (default: 0.5)

**Mathematical Formulation:**

\[
B^{(k)}[j] = \min\left(B^{(k-1)}[j], \min_{i \in W_k(j)} B^{(k-1)}[i]\right)
\]

where \(W_k(j) = \{j - w_k/2, ..., j + w_k/2\}\) is the window around point \(j\).

**Reference:** Ryan, C. G., Clayton, E., Griffin, W. L., Sie, S. H., & Cousens, D. R. (1988). SNIP, a statistics-sensitive background treatment for the quantitative analysis of PIXE spectra in geoscience applications. *Nuclear Instruments and Methods in Physics Research Section B: Beam Interactions with Materials and Atoms*, 34(3), 396-402.

### 4.6 Algorithm Selection

**Default:** Iterative polynomial (Sonneveld-Visser method) - recommended for most cases

**Selection Guide:**
- **Polynomial**: Fast, simple, good for smooth backgrounds
- **Iterative Polynomial**: Best for most cases, handles peaks well
- **Rolling Ball**: Good for varying background levels
- **Top-Hat**: Similar to rolling ball, morphological approach
- **SNIP**: Excellent for noisy data, robust against outliers

---

## 5. K-alpha Stripping Algorithms

K-alpha stripping removes the Kα2 component from XRD data, leaving only Kα1 peaks. This is essential for accurate peak analysis as Kα1 and Kα2 create doublet peaks.

### 5.1 Rachinger Correction

**Method:** Standard Rachinger correction for Kα2 removal

**Physical Background:**

For Cu Kα radiation:
- Kα1 wavelength: \(\lambda_1 = 1.54056\) Å
- Kα2 wavelength: \(\lambda_2 = 1.54439\) Å
- Wavelength ratio: \(R_\lambda = \lambda_2 / \lambda_1 = 1.0025\)
- Intensity ratio: \(R_I = I_2 / I_1 = 0.5\)

**Mathematical Formulation:**

The angular separation between Kα1 and Kα2 peaks is calculated from Bragg's law:

\[
n\lambda = 2d\sin\theta
\]

For small differences:

\[
\Delta(2θ) ≈ 2\tan\theta \cdot (R_\lambda - 1)
\]

More precisely:

\[
\theta_1 = \arcsin\left(\frac{\lambda_1}{2d}\right)
\]

\[
\theta_2 = \arcsin\left(\frac{\lambda_2}{2d}\right)
\]

\[
\Delta(2θ) = 2(\theta_2 - \theta_1) = 2\left[\arcsin\left(\frac{\lambda_2}{2d}\right) - \arcsin\left(\frac{\lambda_1}{2d}\right)\right]
\]

Using the relationship \(d = \lambda_1 / (2\sin\theta_1)\):

\[
\Delta(2θ) = 2\left[\arcsin\left(R_\lambda \sin\theta_1\right) - \theta_1\right]
\]

For small angles, this simplifies to:

\[
\Delta(2θ) = 2\arctan\left[\tan\theta_1 \cdot (R_\lambda - 1)\right]
\]

**Algorithm:**

1. Calculate angular shift for each 2θ value:
   \[
   \theta = \frac{2θ}{2} \quad \text{(convert to θ)}
   \]
   \[
   \Delta(2θ) = 2 \cdot \arctan\left[\tan(\theta) \cdot (R_\lambda - 1)\right]
   \]

2. Calculate Kα2 two-theta positions:
   \[
   2θ_{Kα2} = 2θ - \Delta(2θ)
   \]

3. Interpolate Kα2 intensities:
   \[
   I_{Kα2}(2θ) = R_I \cdot I(2θ_{Kα2})
   \]

4. Subtract Kα2 from original:
   \[
   I_{Kα1}(2θ) = I(2θ) - I_{Kα2}(2θ)
   \]

**Implementation:**
- Uses linear interpolation for shifted positions
- Handles edge cases (out-of-range values set to 0)
- Preserves negative values (not clipped)

**Reference:** Rachinger, W. A. (1948). A correction for the α1α2 doublet in the measurement of widths of X-ray diffraction lines. *Journal of Scientific Instruments*, 25(7), 254-255.

### 5.2 Iterative Rachinger Correction

**Method:** Applies Rachinger correction iteratively for better Kα2 removal

**Algorithm:**

1. Initialize: \(I^{(0)}(2θ) = I(2θ)\)
2. For iteration \(k = 1, 2, ..., N_{iter}\):
   - Apply Rachinger correction to \(I^{(k-1)}(2θ)\)
   - Update: \(I^{(k)}(2θ) = I_{Kα1}^{(k)}(2θ)\)
3. Final Kα1: \(I_{Kα1}(2θ) = I^{(N_{iter})}(2θ)\)

**Parameters:**
- `iterations`: Number of iterations (default: 3)
- `wavelength_ratio`: \(R_\lambda\) (default: 1.0025 for Cu)
- `intensity_ratio`: \(R_I\) (default: 0.5 for Cu)

**Reference:** Enhanced Rachinger method for overlapping peaks

### 5.3 Wavelength Auto-Detection

The system automatically determines wavelength ratios for common X-ray sources:

| Source | λ (Å) | R_λ | R_I |
|--------|-------|-----|-----|
| Cu Kα1 | 1.54056 | 1.0025 | 0.5 |
| Cu Kα  | 1.54184 | 1.0025 | 0.5 |
| Cu Kα2 | 1.54439 | 1.0025 | 0.5 |
| Co Kα  | 1.79026 | 1.0023 | 0.5 |
| Mo Kα  | 0.70932 | 1.0018 | 0.5 |

---

## 6. Peak Detection Algorithms

Peak detection identifies diffraction peaks in XRD spectra. Four algorithms are implemented, with prominence-based detection recommended.

### 6.1 Prominence-Based Detection (Recommended)

**Method:** Uses peak prominence to identify significant peaks

**Peak Prominence Definition:**

The prominence of a peak is the minimum vertical distance that must be descended on either side of the peak to reach a higher peak or the signal boundary.

**Mathematical Formulation:**

For a peak at index \(i\) with intensity \(I_i\):

\[
\text{Prominence} = I_i - \max\left(\max_{j < i} I_j, \max_{j > i} I_j\right)
\]

where the maxima are taken over the intervals until a higher peak is encountered.

**Algorithm:**

1. Auto-determine distance parameter:
   \[
   d = \max\left(1, \left\lfloor\frac{0.1°}{\Delta(2θ)}\right\rfloor\right)
   \]
   where \(\Delta(2θ)\) is the angular spacing between data points.

2. Auto-determine prominence threshold:
   \[
   P_{min} = 0.05 \cdot \max(I)
   \]

3. Find peaks using `scipy.signal.find_peaks()`:
   - `prominence ≥ P_{min}`
   - `distance ≥ d`
   - Optional: `height`, `width` constraints

4. Calculate FWHM for each detected peak

**Implementation:**
- Uses `scipy.signal.find_peaks()` with prominence filtering
- Auto-calculates distance from angular spacing
- Calculates FWHM using interpolation method

**Reference:** SciPy documentation: `scipy.signal.find_peaks`

### 6.2 Threshold-Based Detection

**Method:** Simple threshold with local maximum detection

**Algorithm:**

1. Set threshold: \(T = 0.1 \cdot \max(I)\) (if not specified)
2. For each point \(i\):
   - If \(I_i > T\):
     - Check if \(I_i > I_j\) for all \(j \in [i-d, i+d]\) (local maximum)
     - If yes, add as peak

**Mathematical Formulation:**

\[
\text{Peak at } i \text{ if: } I_i > T \text{ and } I_i = \max_{j \in [i-d, i+d]} I_j
\]

**Parameters:**
- `threshold`: Minimum intensity (default: 10% of max)
- `min_distance`: Minimum distance between peaks in data points (default: 5)

### 6.3 Derivative-Based Detection

**Method:** Zero-crossing of first derivative

**Mathematical Formulation:**

A peak occurs where the first derivative changes from positive to negative:

\[
\frac{dI}{d(2θ)}[i-1] > 0 \text{ and } \frac{dI}{d(2θ)}[i] < 0
\]

**Algorithm:**

1. Calculate first derivative:
   \[
   \frac{dI}{d(2θ)}[i] = I[i+1] - I[i]
   \]

2. Find zero crossings:
   - If \(\frac{dI}{d(2θ)}[i-1] > 0\) and \(\frac{dI}{d(2θ)}[i] < 0\): peak at \(i\)

3. Filter by threshold: \(I_i > T\)

**Implementation:**
- Uses `numpy.diff()` for derivative calculation
- Checks sign change in derivative

### 6.4 Savitzky-Golay Filter Based Detection

**Method:** Smooth data first, then detect peaks

**Savitzky-Golay Filter:**

The Savitzky-Golay filter fits a polynomial to a local window and uses the polynomial value at the center point as the smoothed value.

**Mathematical Formulation:**

For a window of size \(2m+1\) centered at point \(i\):

\[
I_{smooth}[i] = \sum_{j=-m}^{m} c_j I[i+j]
\]

where \(c_j\) are coefficients determined by polynomial fitting of order \(p\).

**Algorithm:**

1. Apply Savitzky-Golay filter:
   - Window length: \(w\) (must be odd, default: 11)
   - Polynomial order: \(p\) (default: 3)
   - Uses `scipy.signal.savgol_filter()`

2. Apply prominence-based detection to smoothed data

**Parameters:**
- `window_length`: Filter window size (default: 11, must be odd)
- `poly_order`: Polynomial order (default: 3, must be < window_length)

**Reference:** Savitzky, A., & Golay, M. J. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry*, 36(8), 1627-1639.

### 6.5 Full Width at Half Maximum (FWHM) Calculation

FWHM is a measure of peak broadening, important for crystallite size and strain analysis.

**Mathematical Formulation:**

\[
\text{FWHM} = 2θ_{right} - 2θ_{left}
\]

where \(2θ_{left}\) and \(2θ_{right}\) are the angles where intensity equals half the peak maximum:

\[
I(2θ_{left}) = I(2θ_{right}) = \frac{I_{peak}}{2}
\]

**Algorithm:**

1. Find peak intensity: \(I_{peak} = I[i_{peak}]\)
2. Calculate half-maximum: \(I_{HM} = I_{peak} / 2\)
3. Find left half-max point:
   - Search left from peak: find \(i_{left}\) where \(I[i_{left}] ≤ I_{HM}\)
   - Linear interpolation:
     \[
     2θ_{left} = 2θ[i_{left}] + \frac{I_{HM} - I[i_{left}]}{I[i_{left}+1] - I[i_{left}]} \cdot (2θ[i_{left}+1] - 2θ[i_{left}])
     \]
4. Find right half-max point (similar interpolation)
5. Calculate: \(\text{FWHM} = 2θ_{right} - 2θ_{left}\)

**Applications:**
- **Crystallite Size (Scherrer Equation):**
  \[
  D = \frac{K\lambda}{\beta\cos\theta}
  \]
  where \(\beta = \text{FWHM}\) (in radians), \(K ≈ 0.9\) (shape factor)

- **Strain Analysis:** Peak broadening due to microstrain

**Reference:** Scherrer, P. (1918). Bestimmung der Größe und der inneren Struktur von Kolloidteilchen mittels Röntgenstrahlen. *Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, Mathematisch-Physikalische Klasse*, 1918, 98-100.

---

## 7. Reference Pattern Matching

Reference pattern matching compares experimental peaks with known crystal structures from databases.

### 7.1 Reference Pattern Formats

#### 7.1.1 Materials Project (MP) Format

```json
{
  "wavelength": {
    "element": "Cu",
    "in_angstroms": 1.54184
  },
  "pattern": [
    [amplitude, [h, k, l], two_theta, d_spacing],
    ...
  ]
}
```

- **Amplitude**: Peak intensity (normalized to 0-100)
- **HKL**: Miller indices as array `[h, k, l]`
- **Two-theta**: Diffraction angle in degrees
- **D-spacing**: Interplanar spacing in Ångstroms

#### 7.1.2 ICDD Format

```json
{
  "id": "Ti3AlC2_0875",
  "name": "Ti3AlC2",
  "source": "ICDD",
  "wavelength": 1.54056,
  "peaks": [
    {
      "d_spacing": 2.30544,
      "two_theta": 39.038,
      "intensity": 100.0,
      "hkl": "1 0 4"
    },
    ...
  ]
}
```

### 7.2 Pattern Loading and Parsing

**MP Format Parsing:**
1. Extract wavelength from `wavelength.in_angstroms`
2. Parse pattern array: `[amplitude, hkl, two_theta, d_spacing]`
3. Normalize intensities: \(I_{norm} = (I / I_{max}) \times 100\)
4. Extract ID/name from filename if not present: `mp-3271_xrd_Cu.json` → `mp-3271`

**ICDD Format Parsing:**
1. Extract two-theta directly if available
2. If not, calculate from d-spacing using Bragg's law:
   \[
   2θ = 2 \arcsin\left(\frac{\lambda}{2d}\right)
   \]
3. Extract HKL values (string format: "1 0 4")

### 7.3 Reference Pattern Visualization

**Publication-Ready Format:**
- Vertical sticks (bars) at each peak position
- HKL labels in bracket format: `(1 0 1)`
- Labels rotated 90° to prevent overlapping
- Positioned below experimental data with visual separator
- Scaled to 30% of maximum experimental intensity

**Mathematical Scaling:**

\[
I_{ref,scaled}(2θ) = \frac{I_{ref}(2θ)}{I_{ref,max}} \times I_{exp,max} \times 0.3
\]

### 7.4 Peak Matching Algorithm

**Method:** Nearest-neighbor matching with tolerance

**Algorithm:**

1. For each detected peak at \(2θ_{det}\):
   - Find closest reference peak:
     \[
     \text{Match} = \arg\min_{2θ_{ref}} |2θ_{det} - 2θ_{ref}|
     \]
   - If \(|2θ_{det} - 2θ_{ref}| < \tau\): match found
   - Mark reference peak as matched (one-to-one matching)

2. Calculate match score:
   \[
   \text{Match Score} = \frac{N_{matched}}{N_{ref}} \times 100\%
   \]

**Parameters:**
- `tolerance`: Angular tolerance in degrees (default: 0.2°)

**Output:**
- `matched_peaks`: List of (detected_peak, reference_peak) tuples
- `unmatched_detected`: Detected peaks without matches
- `unmatched_reference`: Reference peaks without matches
- `match_score`: Percentage of reference peaks matched

---

## 8. Data Visualization

### 8.1 Plot Styling

**Line Properties:**
- Line width: 0.8 pixels (thin, publication-ready)
- Smoothing: Gaussian filter with σ = 1.0
- Colors:
  - Original data: Blue
  - Processed data: Red
  - Reference pattern: Dark green (#2E7D32)
  - Detected peaks: Orange triangles
  - Matched peaks: Purple stars

**Negative Values:**
- Displayed as red dots after background subtraction/K-alpha stripping
- Marker size: `max(0.5, linewidth * 0.6)` pixels
- Edge width: 0.2 pixels
- Preserved for visualization (not clipped to zero)

### 8.2 Interactive Features

**Zoom and Pan:**
- Mouse scroll: Zoom in/out (scale factor: 0.9/1.1)
- Middle mouse button: Reset zoom
- Navigation toolbar: Standard matplotlib controls

**Reference Pattern Display:**
- Vertical sticks with HKL labels
- Labels formatted as `(h k l)` in brackets
- Rotated 90° (vertical) to prevent overlap
- Positioned 5-20% from bottom of extended y-axis
- Horizontal separator line at 12% from bottom

### 8.3 Peak Visualization

**When Reference Pattern Active:**
- Only matched peaks are displayed (for clarity)
- Purple star markers with intensity labels

**When No Reference Pattern:**
- All detected peaks displayed
- Orange triangle markers
- Matched peaks highlighted separately (if matching was performed)

---

## 9. Project Management System

### 9.1 Project Structure

Each analysis session creates a project folder:

```
projects/
└── filename_YYYYMMDD_HHMMSS/
    ├── project_info.json          # Metadata and summary
    ├── original_data/
    │   ├── raw_data.json          # Original 2θ, intensity arrays
    │   └── metadata.json          # File metadata
    ├── processed_data/
    │   ├── background_subtraction.json
    │   └── kalpha_stripping.json
    ├── analysis/
    │   ├── peaks_detected.json    # Peak detection results
    │   └── match_*.json           # Reference pattern matches
    ├── visualizations/
    │   ├── 01_original_spectrum.png
    │   ├── 02_background_subtracted.png
    │   ├── 03_kalpha_stripped.png
    │   ├── 04_peaks_detected.png
    │   ├── 05_reference_overlay_*.png
    │   └── 06_peaks_matched_*.png
    └── reference_patterns/
        └── *.json                  # Reference patterns used
```

### 9.2 Data Persistence

**Automatic Saving:**
- Original data: Saved on file load
- Processed data: Saved after each processing step
- Visualizations: Saved after each plot update
- Analysis results: Saved after peak detection and matching

**JSON Format:**
All data saved in JSON format for:
- Human readability
- Easy parsing by AI/ML tools
- Cross-platform compatibility
- Version control friendly

### 9.3 Project Information Schema

```json
{
  "project_name": "Ti3AlC2_20250120_143022",
  "created_at": "2025-01-20T14:30:22",
  "source_file": "Ti3AlC2.dat",
  "source_file_path": "/path/to/file.dat",
  "original_data_points": 5000,
  "two_theta_range": [5.0, 90.0],
  "analysis_steps": [
    {
      "step": "background_subtraction",
      "timestamp": "2025-01-20T14:31:00",
      "parameters": {"method": "iterative_polynomial", "degree": 6}
    }
  ],
  "peak_detection": {
    "method": "prominence",
    "parameters": {"prominence_percent": 5.0},
    "peak_count": 25,
    "timestamp": "2025-01-20T14:32:00"
  },
  "reference_patterns_used": [
    {
      "name": "Ti3AlC2",
      "match_score": 85.5,
      "timestamp": "2025-01-20T14:33:00"
    }
  ],
  "match_results": {
    "Ti3AlC2": {
      "match_score": 85.5,
      "matched_peaks": 17
    }
  }
}
```

---

## 10. User Interface

### 10.1 Layout

**Fixed Sidebar (12.5% of screen width):**
- File loading controls
- Background subtraction controls
- K-alpha stripping controls
- Peak detection controls
- Reference pattern search and overlay
- Processing options (reset)

**Main Visualization Area (87.5% of screen width):**
- Interactive matplotlib plot
- Navigation toolbar (zoom/pan)
- Legend
- Grid

### 10.2 Control Sections

#### 10.2.1 File Loading
- "Load File" button
- File format filter: `*.xrdml *.dat *.asc *.txt *.raw`
- Displays loaded filename

#### 10.2.2 Background Subtraction
- Method dropdown: `iterative_polynomial`, `polynomial`, `rolling_ball`, `tophat`, `snip`
- Polynomial degree spinner (for polynomial methods)
- "Apply Background Subtraction" button

#### 10.2.3 K-alpha Stripping
- Method dropdown: `rachinger`, `iterative_rachinger`
- Wavelength input (default: 1.54056 Å)
- "Apply K-alpha Stripping" button

#### 10.2.4 Peak Detection
- Method dropdown: `prominence`, `threshold`, `derivative`, `savgol`
- Prominence percentage spinner (default: 5%)
- Height threshold spinner (optional)
- Distance spinner (auto-calculated)
- "Detect Peaks" button
- Peak count display
- Filtered peaks information

#### 10.2.5 Reference Patterns
- Search combo box (editable, autocomplete)
- "Overlay Selected Pattern" button
- "Match Peaks with Reference" button
- Match score display
- Overlay status indicator

### 10.3 Menu Bar

**File Menu:**
- Open XRD File (Ctrl+O)
- Exit (Ctrl+Q)

**Tools Menu:**
- Load Reference Database...
- View Projects...
- Open Project...

**Help Menu:**
- About

---

## 11. Mathematical Formulations

### 11.1 Bragg's Law

Fundamental equation for X-ray diffraction:

\[
n\lambda = 2d\sin\theta
\]

where:
- \(n\): Order of reflection (typically 1)
- \(\lambda\): X-ray wavelength (Å)
- \(d\): Interplanar spacing (Å)
- \(\theta\): Bragg angle (degrees)

**Two-theta relationship:**

\[
2θ = 2\arcsin\left(\frac{\lambda}{2d}\right)
\]

**D-spacing calculation:**

\[
d = \frac{\lambda}{2\sin\theta} = \frac{\lambda}{2\sin(2θ/2)}
\]

### 11.2 Peak Prominence

For a peak at position \(i\) with intensity \(I_i\):

\[
P_i = I_i - \max\left(\max_{j \in L(i)} I_j, \max_{j \in R(i)} I_j\right)
\]

where:
- \(L(i)\): Left interval until higher peak or boundary
- \(R(i)\): Right interval until higher peak or boundary

### 11.3 Gaussian Peak Profile

For reference pattern generation:

\[
I(2θ) = I_0 \exp\left(-\frac{1}{2}\left(\frac{2θ - 2θ_0}{\sigma}\right)^2\right)
\]

where:
- \(I_0\): Peak intensity
- \(2θ_0\): Peak position
- \(\sigma\): Peak width parameter (default: 0.1°)

### 11.4 Linear Interpolation

For FWHM calculation and data interpolation:

\[
y(x) = y_1 + \frac{y_2 - y_1}{x_2 - x_1}(x - x_1)
\]

### 11.5 Polynomial Fitting

Least-squares polynomial of degree \(n\):

\[
P_n(x) = \sum_{i=0}^{n} a_i x^i
\]

Coefficients determined by minimizing:

\[
\min_{a_i} \sum_{j=1}^{N} \left[y_j - P_n(x_j)\right]^2
\]

Solution via normal equations or QR decomposition.

---

## 12. Implementation Details

### 12.1 Data Structures

**XRDData Class:**
```python
class XRDData:
    two_theta: np.ndarray    # Two-theta values in degrees
    intensity: np.ndarray   # Intensity values
    wavelength: float        # X-ray wavelength in Å
    metadata: dict          # File metadata
```

**DetectedPeak Class:**
```python
class DetectedPeak:
    two_theta: float        # Peak position in degrees
    intensity: float        # Peak intensity
    index: int              # Data point index
    width: float            # Peak width in data points
    prominence: float      # Peak prominence
    fwhm: float            # Full Width at Half Maximum in degrees
```

**ReferencePattern Class:**
```python
class ReferencePattern:
    id: str                 # Pattern identifier
    name: str               # Pattern name
    two_theta: np.ndarray   # Peak positions
    intensity: np.ndarray   # Peak intensities
    d_spacing: np.ndarray   # D-spacings
    hkl: List               # Miller indices
    wavelength: float       # X-ray wavelength
```

### 12.2 Error Handling

- File parsing errors: Graceful fallback to alternative parsers
- Invalid data: Validation and error messages
- Missing dependencies: Clear error messages
- Out-of-range values: Clipping with warnings

### 12.3 Performance Considerations

- NumPy vectorization for array operations
- Efficient interpolation using scipy
- Lazy loading of reference databases
- Project data saved incrementally (not all at once)

### 12.4 Code Quality

- Type hints for all functions
- Comprehensive docstrings
- Modular design for extensibility
- Consistent naming conventions

---

## 13. References

### 13.1 Background Subtraction

1. Sonneveld, E. J., & Visser, J. W. (1975). Automatic collection of powder data from photographs. *Journal of Applied Crystallography*, 8(1), 1-7.

2. Sternberg, S. R. (1983). Biomedical image processing. *Computer*, 16(1), 22-34.

3. Ryan, C. G., Clayton, E., Griffin, W. L., Sie, S. H., & Cousens, D. R. (1988). SNIP, a statistics-sensitive background treatment for the quantitative analysis of PIXE spectra in geoscience applications. *Nuclear Instruments and Methods in Physics Research Section B: Beam Interactions with Materials and Atoms*, 34(3), 396-402.

### 13.2 K-alpha Stripping

4. Rachinger, W. A. (1948). A correction for the α1α2 doublet in the measurement of widths of X-ray diffraction lines. *Journal of Scientific Instruments*, 25(7), 254-255.

### 13.3 Peak Detection

5. Savitzky, A., & Golay, M. J. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry*, 36(8), 1627-1639.

6. SciPy Development Team. (2024). *scipy.signal.find_peaks*. SciPy Documentation. https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html

### 13.4 X-ray Diffraction Theory

7. Cullity, B. D., & Stock, S. R. (2001). *Elements of X-ray Diffraction* (3rd ed.). Prentice Hall.

8. Klug, H. P., & Alexander, L. E. (1974). *X-ray Diffraction Procedures: For Polycrystalline and Amorphous Materials* (2nd ed.). Wiley-Interscience.

9. Pecharsky, V. K., & Zavalij, P. Y. (2009). *Fundamentals of Powder Diffraction and Structural Characterization of Materials* (2nd ed.). Springer.

### 13.5 Crystallite Size Analysis

10. Scherrer, P. (1918). Bestimmung der Größe und der inneren Struktur von Kolloidteilchen mittels Röntgenstrahlen. *Nachrichten von der Gesellschaft der Wissenschaften zu Göttingen, Mathematisch-Physikalische Klasse*, 1918, 98-100.

11. Langford, J. I., & Wilson, A. J. C. (1978). Scherrer after sixty years: A survey and some new results in the determination of crystallite size. *Journal of Applied Crystallography*, 11(2), 102-113.

### 13.6 Software and Libraries

12. NumPy Development Team. (2024). *NumPy*. https://numpy.org/

13. SciPy Development Team. (2024). *SciPy*. https://scipy.org/

14. Matplotlib Development Team. (2024). *Matplotlib*. https://matplotlib.org/

15. PyQt6 Development Team. (2024). *PyQt6*. https://www.riverbankcomputing.com/software/pyqt/

16. PyInstaller Development Team. (2024). *PyInstaller*. https://www.pyinstaller.org/

### 13.7 File Format Specifications

17. Bruker AXS. (2024). *XRDML File Format Specification*. Bruker Corporation.

18. PANalytical. (2024). *XRD Data File Formats*. Malvern Panalytical.

19. Materials Project. (2024). *Materials Project Database*. https://materialsproject.org/

20. ICDD. (2024). *PDF Database*. International Centre for Diffraction Data. https://www.icdd.com/

---

## Appendix A: Default Parameters

### Background Subtraction
- **Iterative Polynomial**: degree=6, iterations=10, threshold=0.1
- **Polynomial**: degree=6
- **Rolling Ball**: ball_radius=5% of data points (min 50)
- **Top-Hat**: structure_size=5% of data points (min 50)
- **SNIP**: iterations=100, reduction_factor=0.5

### K-alpha Stripping
- **Wavelength Ratio**: 1.0025 (Cu Kα)
- **Intensity Ratio**: 0.5 (Cu Kα)
- **Iterations**: 3 (iterative method)

### Peak Detection
- **Prominence**: 5% of maximum intensity
- **Distance**: Auto-calculated from 0.1° spacing
- **Height**: Optional, not set by default
- **Width**: Optional, not set by default

### Reference Pattern Matching
- **Tolerance**: 0.2° (angular matching)
- **Scaling**: 30% of maximum experimental intensity
- **Label Format**: `(h k l)` in brackets, rotated 90°

---

## Appendix B: File Format Examples

### XRDML Example Structure
```xml
<xrdMeas>
  <usedWavelength>
    <kAlpha1>1.54056</kAlpha1>
  </usedWavelength>
  <scan>
    <dataPoints>
      <positions>
        <listPositions>5.0 5.02 5.04 ...</listPositions>
      </positions>
      <counts>100 105 110 ...</counts>
    </dataPoints>
  </scan>
</xrdMeas>
```

### DAT/TXT Example
```
5.00    100
5.02    105
5.04    110
...
```

### RAW Binary Format
- Header: ~3-4 KB (metadata, angles, count)
- Count: 4-byte unsigned integer (little-endian)
- Data: Float32 array (little-endian), intensity values

---

## Appendix C: Troubleshooting

### Common Issues

1. **RAW file shows wrong x-axis range**
   - Solution: Parser validates and corrects unreasonable end angles (>120°)
   - Automatically recalculates step for standard 5-90° scans

2. **MP reference patterns not detected**
   - Solution: ID/name extracted from filename
   - Format: `mp-XXXX_xrd_Cu.json` → ID: `mp-XXXX`

3. **Peaks not detected**
   - Solution: Lower prominence threshold (1-2% recommended for small peaks)
   - Check filtered peaks information in UI

4. **Reference pattern labels overlapping**
   - Solution: Labels rotated 90° (vertical) to prevent overlap

---

## Document Information

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Author:** XRD Scorer Development Team  
**License:** [To be specified]

---

**End of Documentation**

