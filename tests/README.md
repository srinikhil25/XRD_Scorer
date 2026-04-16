# XRD Scorer Test Suite

This directory contains comprehensive tests for the XRD Scorer application.

## Running Tests

To run all tests:
```bash
pytest
```

To run specific test files:
```bash
pytest tests/test_d_spacing.py
pytest tests/test_rachinger.py
pytest tests/test_file_parser.py
```

To run with verbose output:
```bash
pytest -v
```

To run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Test Structure

- `test_d_spacing.py`: Tests for d-spacing calculation using Bragg's law
- `test_rachinger.py`: Tests for Rachinger correction (K-alpha stripping)
- `test_background_subtraction.py`: Tests for all background subtraction methods
- `test_peak_detection.py`: Tests for peak detection algorithms
- `test_file_parser.py`: Tests for file parsers (DAT, ASC, TXT, etc.)
- `conftest.py`: Pytest fixtures and configuration
- `test_data/`: Sample test data files

## Test Coverage

The test suite covers:
- ✅ d-spacing calculation (`calculate_d_spacing`)
- ✅ Rachinger correction (shape preservation)
- ✅ All background subtraction methods
- ✅ All peak detection methods
- ✅ File parsers (DAT, ASC, TXT)
- ✅ Edge cases and error handling

## Requirements

Install test dependencies:
```bash
pip install pytest
```

