# Peak Detection and Reference Pattern Matching Guide

## How Reference Patterns Work

### Current Implementation

**Reference Pattern Overlay:**
- Reference patterns are loaded from JSON files (ICDD and Materials Project formats)
- When you overlay a reference pattern, it generates a continuous spectrum from discrete peaks
- The reference pattern is displayed as a green dashed line overlaid on your experimental data
- This allows **visual comparison** to see if peaks align

**Reference Pattern Matching:**
- After detecting peaks in your experimental data, you can match them with reference patterns
- The system compares detected peak positions with reference peak positions
- It calculates a **match score** (percentage of reference peaks that were matched)
- Matched peaks are highlighted in purple, unmatched peaks in orange

## Recommended Workflow

### Option 1: Visual Comparison First (Current Approach)
1. **Load XRD file**
2. **Apply background subtraction** (recommended)
3. **Apply K-alpha stripping** (optional, but recommended for Cu radiation)
4. **Overlay reference pattern** - Visually compare to see if patterns match
5. **Detect peaks** - Identify peaks in your processed data
6. **Match peaks with reference** - Get quantitative match score

**When to use:** When you want to quickly see if a reference pattern matches visually before doing quantitative analysis.

### Option 2: Peak Detection First (Quantitative Approach)
1. **Load XRD file**
2. **Apply background subtraction** (recommended)
3. **Apply K-alpha stripping** (optional)
4. **Detect peaks** - Identify all peaks in your data first
5. **Match peaks with reference** - Compare detected peaks with reference patterns
6. **Overlay reference pattern** - Visual confirmation of matches

**When to use:** When you want quantitative analysis first, then visual confirmation.

## Peak Detection Methods

### 1. Prominence (Recommended)
- Uses peak prominence (height relative to surrounding baseline)
- Most robust method, handles noise well
- **Parameters:**
  - **Min Prominence**: Minimum peak prominence as % of maximum intensity (default: 5%)
  - Lower values = more peaks detected (including noise)
  - Higher values = only strong peaks detected

### 2. Threshold
- Simple intensity threshold
- Detects all peaks above a certain intensity
- Good for clean data with clear peaks

### 3. Derivative
- Uses first derivative (zero-crossing method)
- Detects peaks where derivative changes from positive to negative
- Good for sharp, well-separated peaks

### 4. Savitzky-Golay
- Applies smoothing filter first, then detects peaks
- Good for noisy data
- Smoothes data before peak detection

## Peak Matching

### How It Works

1. **Detect peaks** in your experimental data
2. **Select a reference pattern** from the database
3. **Click "Match Peaks with Reference"**
4. The system:
   - Compares each detected peak with reference peaks
   - Matches peaks within tolerance (default: 0.2° 2θ)
   - Calculates match score: `(matched_peaks / total_reference_peaks) × 100%`

### Match Score Interpretation

- **90-100%**: Excellent match - likely the same phase
- **70-90%**: Good match - may be the same phase with some impurities
- **50-70%**: Moderate match - may be related phase or mixture
- **<50%**: Poor match - likely different phase

### Visual Indicators

- **Orange triangles (▼)**: All detected peaks
- **Purple stars (★)**: Matched peaks (found in both experimental and reference)
- **Green dashed line**: Reference pattern overlay

## Best Practices

### For Accurate Peak Detection:

1. **Always apply background subtraction first**
   - Removes baseline, making peaks more distinct
   - Reduces false positives from background noise

2. **Apply K-alpha stripping for Cu radiation**
   - Removes Kα2 component
   - Results in sharper, single peaks instead of doublets

3. **Adjust prominence threshold**
   - Start with default (5%)
   - If too many peaks detected (including noise): increase threshold
   - If missing real peaks: decrease threshold

4. **Use appropriate method**
   - **Prominence**: Best for most cases
   - **Savitzky-Golay**: For very noisy data
   - **Threshold**: For clean data with known intensity levels

### For Reference Pattern Matching:

1. **Detect peaks on processed data** (after background subtraction and K-alpha stripping)

2. **Use appropriate tolerance**
   - Default 0.2° is good for most cases
   - For high-resolution data: can use 0.1°
   - For low-resolution data: may need 0.3-0.5°

3. **Check match score AND visual alignment**
   - High match score + good visual alignment = confident identification
   - High match score + poor visual alignment = check for systematic errors

4. **Compare multiple reference patterns**
   - Try different phases to find best match
   - Mixtures will have lower match scores

## Example Workflow

```
1. Load XRD file → See raw spectrum
2. Apply background subtraction → Cleaner spectrum, negative values visible
3. Apply K-alpha stripping → Sharper peaks
4. Detect peaks → Orange triangles show all detected peaks
5. Search for "Ti3AlC2" in reference patterns
6. Click "Match Peaks with Reference" → 
   - Match score: 85% (17/20 peaks matched)
   - Purple stars show matched peaks
   - Green line shows reference pattern
7. Visual inspection confirms good alignment
8. Conclusion: Sample likely contains Ti3AlC2 phase
```

## Troubleshooting

**Problem: Too many peaks detected**
- Solution: Increase prominence threshold (try 10-15%)

**Problem: Missing real peaks**
- Solution: Decrease prominence threshold (try 2-3%)

**Problem: Low match score but visual alignment looks good**
- Solution: Check if wavelength matches (Cu Kα1 = 1.54056 Å)
- Solution: Try adjusting tolerance (may need higher for systematic offset)

**Problem: Reference pattern doesn't overlay correctly**
- Solution: Check wavelength in reference pattern matches your data
- Solution: Reference patterns use Cu Kα by default

## Technical Details

### Peak Detection Algorithm (Prominence Method)

1. Calculates peak prominence for each local maximum
2. Prominence = peak height - height of lowest point between peak and higher peak
3. Filters peaks by minimum prominence threshold
4. Ensures minimum distance between peaks

### Peak Matching Algorithm

1. For each detected peak, finds closest reference peak within tolerance
2. One-to-one matching (each peak matched only once)
3. Calculates match score as percentage of reference peaks matched
4. Returns matched pairs, unmatched detected peaks, and unmatched reference peaks

