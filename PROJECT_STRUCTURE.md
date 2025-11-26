# Project Structure Documentation

## Overview

Each XRD file analysis is saved as a separate project folder containing all analysis data, visualizations, and metadata. This structure is designed for use with Agentic AI tools for materials science research.

## Project Folder Structure

```
projects/
  └── filename_YYYYMMDD_HHMMSS/
      ├── project_info.json          # Project metadata and summary
      ├── original_data/
      │   ├── raw_data.json          # Original XRD data (2θ, intensity)
      │   └── metadata.json          # File metadata (wavelength, source, etc.)
      ├── processed_data/
      │   ├── background_subtraction.json
      │   └── kalpha_stripping.json
      ├── analysis/
      │   ├── peaks_detected.json    # Peak detection results
      │   └── match_*.json           # Reference pattern match results
      ├── visualizations/
      │   ├── 01_original_spectrum.png
      │   ├── 02_background_subtracted.png
      │   ├── 03_kalpha_stripped.png
      │   ├── 04_peaks_detected.png
      │   ├── 05_reference_overlay_*.png
      │   └── 06_peaks_matched_*.png
      └── reference_patterns/
          └── *.json                  # Reference patterns used in analysis
```

## File Formats

### project_info.json
Contains project metadata and analysis summary:
```json
{
  "project_name": "Ti3AlC2_20250120_143022",
  "created_at": "2025-01-20T14:30:22",
  "source_file": "Ti3AlC2.dat",
  "source_file_path": "/path/to/file.dat",
  "original_data_points": 5000,
  "two_theta_range": [5.0, 85.0],
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

### raw_data.json
Original XRD data:
```json
{
  "two_theta": [5.0, 5.1, ...],
  "intensity": [100, 105, ...],
  "wavelength": 1.54056,
  "metadata": {
    "file_type": "DAT",
    "file_path": "/path/to/file.dat"
  },
  "saved_at": "2025-01-20T14:30:22"
}
```

### processed_data/*.json
Processed data after each step:
```json
{
  "step": "background_subtraction",
  "two_theta": [5.0, 5.1, ...],
  "intensity": [50, 55, ...],
  "parameters": {
    "method": "iterative_polynomial",
    "degree": 6
  },
  "saved_at": "2025-01-20T14:31:00"
}
```

### analysis/peaks_detected.json
Peak detection results:
```json
{
  "method": "prominence",
  "parameters": {
    "prominence_percent": 5.0,
    "prominence_absolute": 150.0
  },
  "peaks": [
    {
      "two_theta": 39.546,
      "intensity": 2500.0,
      "index": 3456,
      "width": 0.15,
      "prominence": 200.0
    }
  ],
  "peak_count": 25,
  "saved_at": "2025-01-20T14:32:00"
}
```

### analysis/match_*.json
Reference pattern matching results:
```json
{
  "reference_name": "Ti3AlC2",
  "match_score": 85.5,
  "matched_peaks_count": 17,
  "total_reference_peaks": 20,
  "matched_peaks": [
    {
      "detected_two_theta": 39.546,
      "detected_intensity": 2500.0,
      "reference_two_theta": 39.038,
      "reference_intensity": 100.0
    }
  ],
  "unmatched_detected": [...],
  "unmatched_reference": [...],
  "saved_at": "2025-01-20T14:33:00"
}
```

## Usage for AI/ML

### Data Loading
All data is in JSON format, making it easy to load for AI analysis:
- **Original data**: For baseline comparisons
- **Processed data**: For feature extraction
- **Peak data**: For pattern recognition
- **Match results**: For phase identification training

### Image Analysis
Visualizations are saved as PNG files (150 DPI) suitable for:
- Computer vision models
- Pattern recognition
- Visual comparison algorithms
- Report generation

### Metadata
Project info provides context for:
- Reproducibility
- Parameter optimization
- Analysis workflow tracking
- Dataset curation

## Project Management

### Creating Projects
Projects are automatically created when you:
1. Load an XRD file
2. The system creates a timestamped folder
3. Saves original data and initial visualization

### Saving Analysis Steps
Each analysis step automatically saves:
- Processed data (JSON)
- Visualization (PNG)
- Parameters and metadata

### Opening Projects
Use **Tools → Open Project** to:
- Load previous analyses
- Continue from saved state
- Review analysis history

### Viewing Projects
Use **Tools → View Projects** to:
- See all analysis projects
- View project summaries
- Open specific projects

## Benefits for Agentic AI

1. **Structured Data**: All analysis data in consistent JSON format
2. **Complete History**: Every step is saved with parameters
3. **Reproducibility**: Full analysis workflow can be reconstructed
4. **Visual Documentation**: Images at each step for visual analysis
5. **Metadata Rich**: All context needed for AI understanding
6. **Scalable**: Easy to batch process multiple projects

## Example Use Cases

### Training Data
- Collect projects from multiple samples
- Extract features from processed data
- Train models on peak patterns
- Learn from match scores

### Analysis Automation
- AI can load project data
- Replicate analysis workflows
- Compare results across projects
- Identify patterns in datasets

### Research Assistance
- AI can review analysis history
- Suggest optimal parameters
- Identify similar patterns
- Generate research insights

