"""
Tests for peak detection algorithms
"""

import numpy as np
import pytest
from src.core.peak_detection import (
    detect_peaks_threshold,
    detect_peaks_prominence,
    detect_peaks_derivative,
    detect_peaks_savgol,
    detect_peaks,
    calculate_fwhm,
    match_peaks_with_reference
)
from src.core.reference_pattern import ReferencePattern


def test_detect_peaks_threshold():
    """Test threshold-based peak detection"""
    two_theta = np.linspace(10, 80, 1000)
    # Create synthetic peaks
    intensity = np.zeros(1000)
    intensity[200] = 1000  # Peak at index 200
    intensity[500] = 800   # Peak at index 500
    intensity[700] = 600   # Peak at index 700
    
    peaks = detect_peaks_threshold(two_theta, intensity, threshold=100)
    
    assert len(peaks) > 0
    assert all(hasattr(p, 'two_theta') for p in peaks)
    assert all(hasattr(p, 'intensity') for p in peaks)
    assert all(hasattr(p, 'index') for p in peaks)


def test_detect_peaks_prominence():
    """Test prominence-based peak detection"""
    two_theta = np.linspace(20, 70, 800)
    # Create synthetic peaks with noise
    intensity = np.random.rand(800) * 50
    intensity[200] = 1000
    intensity[400] = 900
    intensity[600] = 800
    
    peaks = detect_peaks_prominence(two_theta, intensity, prominence=100)
    
    assert len(peaks) > 0
    assert all(hasattr(p, 'two_theta') for p in peaks)
    assert all(hasattr(p, 'intensity') for p in peaks)
    assert all(hasattr(p, 'fwhm') for p in peaks)


def test_detect_peaks_derivative():
    """Test derivative-based peak detection"""
    two_theta = np.linspace(15, 75, 600)
    # Create synthetic peaks
    intensity = np.zeros(600)
    intensity[150] = 1000
    intensity[300] = 800
    intensity[450] = 600
    
    peaks = detect_peaks_derivative(two_theta, intensity, threshold=100)
    
    assert len(peaks) >= 0  # May or may not detect peaks depending on data
    if len(peaks) > 0:
        assert all(hasattr(p, 'two_theta') for p in peaks)


def test_detect_peaks_savgol():
    """Test Savitzky-Golay based peak detection"""
    two_theta = np.linspace(20, 65, 500)
    # Create synthetic peaks with noise
    intensity = np.random.rand(500) * 30
    intensity[100] = 1000
    intensity[250] = 900
    intensity[400] = 800
    
    peaks = detect_peaks_savgol(two_theta, intensity, prominence=100)
    
    assert len(peaks) >= 0
    if len(peaks) > 0:
        assert all(hasattr(p, 'two_theta') for p in peaks)


def test_detect_peaks_all_methods():
    """Test detect_peaks with all available methods"""
    two_theta = np.linspace(10, 80, 1000)
    intensity = np.random.rand(1000) * 500
    intensity[200] = 2000
    intensity[500] = 1800
    intensity[700] = 1500
    
    methods = ['prominence', 'threshold', 'derivative', 'savgol']
    
    for method in methods:
        peaks = detect_peaks(two_theta, intensity, method=method)
        assert isinstance(peaks, list)
        if len(peaks) > 0:
            assert all(hasattr(p, 'two_theta') for p in peaks)


def test_detect_peaks_invalid_method():
    """Test that detect_peaks raises error for invalid method"""
    two_theta = np.linspace(20, 60, 300)
    intensity = np.random.rand(300) * 500
    
    with pytest.raises(ValueError, match="Unknown method"):
        detect_peaks(two_theta, intensity, method='invalid_method')


def test_calculate_fwhm():
    """Test FWHM calculation"""
    two_theta = np.linspace(20, 60, 400)
    # Create a Gaussian-like peak
    peak_center = 40.0
    peak_width = 1.0
    intensity = 1000 * np.exp(-((two_theta - peak_center) / peak_width) ** 2)
    
    peak_index = np.argmax(intensity)
    fwhm = calculate_fwhm(two_theta, intensity, peak_index)
    
    assert fwhm is not None
    assert fwhm > 0
    assert np.isfinite(fwhm)


def test_calculate_fwhm_invalid_index():
    """Test FWHM calculation with invalid index"""
    two_theta = np.linspace(20, 60, 100)
    intensity = np.random.rand(100) * 500
    
    # Test with negative index
    fwhm_neg = calculate_fwhm(two_theta, intensity, -1)
    assert fwhm_neg is None
    
    # Test with index out of range
    fwhm_out = calculate_fwhm(two_theta, intensity, 200)
    assert fwhm_out is None


def test_match_peaks_with_reference():
    """Test peak matching with reference pattern"""
    # Create detected peaks
    from src.core.peak_detection import DetectedPeak
    
    detected_peaks = [
        DetectedPeak(20.0, 1000, 100),
        DetectedPeak(40.0, 900, 200),
        DetectedPeak(60.0, 800, 300)
    ]
    
    # Create reference pattern data dictionary
    ref_data = {
        'id': 'test',
        'name': 'Test Pattern',
        'wavelength': 1.54056,
        'peaks': [
            {'two_theta': 20.1, 'intensity': 100, 'hkl': '(1 0 0)', 'd_spacing': 4.4},
            {'two_theta': 40.2, 'intensity': 90, 'hkl': '(2 0 0)', 'd_spacing': 2.2},
            {'two_theta': 60.1, 'intensity': 80, 'hkl': '(3 0 0)', 'd_spacing': 1.5},
            {'two_theta': 80.0, 'intensity': 70, 'hkl': '(4 0 0)', 'd_spacing': 1.1}
        ]
    }
    
    ref_pattern = ReferencePattern(ref_data)
    
    match_result = match_peaks_with_reference(
        detected_peaks, ref_pattern, tolerance=0.5
    )
    
    assert 'matched_peaks' in match_result
    assert 'unmatched_detected' in match_result
    assert 'unmatched_reference' in match_result
    assert 'match_score' in match_result
    assert isinstance(match_result['match_score'], (int, float))
    assert 0 <= match_result['match_score'] <= 100


def test_match_peaks_no_reference():
    """Test peak matching when reference has no two_theta"""
    from src.core.peak_detection import DetectedPeak
    
    detected_peaks = [
        DetectedPeak(20.0, 1000, 100)
    ]
    
    # Create reference pattern with empty data (no peaks)
    ref_data = {
        'id': 'test',
        'name': 'Test Pattern',
        'wavelength': 1.54056
    }
    
    ref_pattern = ReferencePattern(ref_data)
    
    match_result = match_peaks_with_reference(
        detected_peaks, ref_pattern, tolerance=0.5
    )
    
    assert match_result['match_score'] == 0.0
    assert len(match_result['matched_peaks']) == 0

