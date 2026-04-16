"""
Tests for Rachinger correction (K-alpha stripping)
"""

import numpy as np
import pytest
from src.core.kalpha_stripping import (
    rachinger_correction,
    iterative_rachinger_correction,
    strip_kalpha
)


def test_rachinger_correction_shape():
    """Test that Rachinger correction returns arrays of same shape as input"""
    two_theta = np.linspace(10, 80, 1000)
    intensity = np.random.rand(1000) * 1000 + 100
    
    kalpha1, kalpha2 = rachinger_correction(two_theta, intensity)
    
    assert kalpha1.shape == intensity.shape
    assert kalpha2.shape == intensity.shape
    assert kalpha1.shape == two_theta.shape
    assert kalpha2.shape == two_theta.shape


def test_rachinger_correction_output_types():
    """Test that Rachinger correction returns numpy arrays"""
    two_theta = np.linspace(20, 60, 500)
    intensity = np.random.rand(500) * 500
    
    kalpha1, kalpha2 = rachinger_correction(two_theta, intensity)
    
    assert isinstance(kalpha1, np.ndarray)
    assert isinstance(kalpha2, np.ndarray)


def test_rachinger_correction_finite_values():
    """Test that Rachinger correction returns finite values"""
    two_theta = np.linspace(10, 80, 500)
    intensity = np.random.rand(500) * 1000
    
    kalpha1, kalpha2 = rachinger_correction(two_theta, intensity)
    
    assert np.all(np.isfinite(kalpha1))
    assert np.all(np.isfinite(kalpha2))


def test_rachinger_correction_parameters():
    """Test Rachinger correction with different parameters"""
    two_theta = np.linspace(20, 70, 300)
    intensity = np.random.rand(300) * 800
    
    # Test with default parameters
    kalpha1_default, kalpha2_default = rachinger_correction(two_theta, intensity)
    
    # Test with custom wavelength ratio
    kalpha1_custom, kalpha2_custom = rachinger_correction(
        two_theta, intensity, 
        wavelength_ratio=1.0023,  # Co Kα
        intensity_ratio=0.5
    )
    
    assert kalpha1_default.shape == kalpha1_custom.shape
    assert kalpha2_default.shape == kalpha2_custom.shape


def test_iterative_rachinger_correction_shape():
    """Test that iterative Rachinger correction returns arrays of same shape"""
    two_theta = np.linspace(15, 75, 800)
    intensity = np.random.rand(800) * 600
    
    kalpha1, kalpha2 = iterative_rachinger_correction(
        two_theta, intensity, 
        iterations=3
    )
    
    assert kalpha1.shape == intensity.shape
    assert kalpha2.shape == intensity.shape


def test_iterative_rachinger_correction_iterations():
    """Test iterative Rachinger with different iteration counts"""
    two_theta = np.linspace(20, 60, 400)
    intensity = np.random.rand(400) * 700
    
    kalpha1_3, kalpha2_3 = iterative_rachinger_correction(
        two_theta, intensity, iterations=3
    )
    
    kalpha1_5, kalpha2_5 = iterative_rachinger_correction(
        two_theta, intensity, iterations=5
    )
    
    assert kalpha1_3.shape == kalpha1_5.shape
    assert kalpha2_3.shape == kalpha2_5.shape


def test_strip_kalpha_rachinger():
    """Test strip_kalpha function with rachinger method"""
    two_theta = np.linspace(10, 80, 600)
    intensity = np.random.rand(600) * 900
    
    kalpha1, kalpha2 = strip_kalpha(
        two_theta, intensity, 
        method='rachinger'
    )
    
    assert kalpha1.shape == intensity.shape
    assert kalpha2.shape == intensity.shape


def test_strip_kalpha_iterative():
    """Test strip_kalpha function with iterative_rachinger method"""
    two_theta = np.linspace(15, 70, 500)
    intensity = np.random.rand(500) * 800
    
    kalpha1, kalpha2 = strip_kalpha(
        two_theta, intensity, 
        method='iterative_rachinger',
        iterations=3
    )
    
    assert kalpha1.shape == intensity.shape
    assert kalpha2.shape == intensity.shape


def test_strip_kalpha_auto_wavelength():
    """Test strip_kalpha with auto wavelength detection"""
    two_theta = np.linspace(20, 65, 400)
    intensity = np.random.rand(400) * 750
    
    # Test with Cu Kα wavelength
    kalpha1, kalpha2 = strip_kalpha(
        two_theta, intensity,
        method='rachinger',
        wavelength=1.54056  # Cu Kα1
    )
    
    assert kalpha1.shape == intensity.shape
    assert kalpha2.shape == intensity.shape


def test_strip_kalpha_invalid_method():
    """Test that strip_kalpha raises error for invalid method"""
    two_theta = np.linspace(20, 60, 300)
    intensity = np.random.rand(300) * 500
    
    with pytest.raises(ValueError, match="Unknown method"):
        strip_kalpha(two_theta, intensity, method='invalid_method')


def test_rachinger_correction_edge_cases():
    """Test Rachinger correction with edge cases"""
    # Test with very small array
    two_theta_small = np.array([20.0, 40.0, 60.0])
    intensity_small = np.array([100, 200, 150])
    
    kalpha1, kalpha2 = rachinger_correction(two_theta_small, intensity_small)
    assert kalpha1.shape == intensity_small.shape
    
    # Test with constant intensity
    two_theta_const = np.linspace(20, 60, 100)
    intensity_const = np.ones(100) * 500
    
    kalpha1_const, kalpha2_const = rachinger_correction(
        two_theta_const, intensity_const
    )
    assert kalpha1_const.shape == intensity_const.shape
    assert kalpha2_const.shape == intensity_const.shape

