"""
Tests for d-spacing calculation
"""

import numpy as np
import pytest
from src.core.file_parser import XRDData


def test_get_d_spacing_basic():
    """Test that get_d_spacing returns correct values using Bragg's law"""
    # Test with known values
    # For Cu Kα1 (λ = 1.54056 Å) at 2θ = 43.3°, d should be ~2.09 Å
    wavelength = 1.54056  # Cu Kα1 in Angstroms
    two_theta = np.array([43.3])
    
    data = XRDData(two_theta, np.array([1000]), wavelength=wavelength)
    d_spacing = data.get_d_spacing()
    
    # Expected: d = λ / (2*sin(θ)) where θ = 2θ/2
    theta_rad = np.deg2rad(43.3 / 2)
    expected_d = wavelength / (2 * np.sin(theta_rad))
    
    assert len(d_spacing) == 1
    assert np.isclose(d_spacing[0], expected_d, rtol=1e-4)
    assert np.isclose(d_spacing[0], 2.09, rtol=0.01)  # Approximate known value


def test_get_d_spacing_multiple_values():
    """Test d-spacing calculation with multiple 2θ values"""
    wavelength = 1.54056  # Cu Kα1
    two_theta = np.array([20.0, 40.0, 60.0, 80.0])
    intensity = np.array([100, 200, 300, 400])
    
    data = XRDData(two_theta, intensity, wavelength=wavelength)
    d_spacing = data.get_d_spacing()
    
    assert len(d_spacing) == len(two_theta)
    
    # Verify each value using Bragg's law
    for i, tt in enumerate(two_theta):
        theta_rad = np.deg2rad(tt / 2)
        expected_d = wavelength / (2 * np.sin(theta_rad))
        assert np.isclose(d_spacing[i], expected_d, rtol=1e-5)


def test_get_d_spacing_no_wavelength():
    """Test that get_d_spacing raises error when wavelength is not set"""
    two_theta = np.array([20.0, 40.0])
    intensity = np.array([100, 200])
    
    data = XRDData(two_theta, intensity, wavelength=None)
    
    with pytest.raises(ValueError, match="Wavelength not set"):
        data.get_d_spacing()


def test_get_d_spacing_edge_cases():
    """Test d-spacing calculation with edge cases"""
    wavelength = 1.54056
    
    # Test with very small angle
    two_theta_small = np.array([5.0])
    data_small = XRDData(two_theta_small, np.array([100]), wavelength=wavelength)
    d_small = data_small.get_d_spacing()
    assert d_small[0] > 0
    assert np.isfinite(d_small[0])
    
    # Test with large angle
    two_theta_large = np.array([120.0])
    data_large = XRDData(two_theta_large, np.array([100]), wavelength=wavelength)
    d_large = data_large.get_d_spacing()
    assert d_large[0] > 0
    assert np.isfinite(d_large[0])
    assert d_large[0] < d_small[0]  # Larger angle = smaller d-spacing


def test_get_d_spacing_array_shape():
    """Test that d-spacing array has same shape as input"""
    wavelength = 1.54056
    two_theta = np.linspace(10, 80, 100)
    intensity = np.random.rand(100) * 1000
    
    data = XRDData(two_theta, intensity, wavelength=wavelength)
    d_spacing = data.get_d_spacing()
    
    assert d_spacing.shape == two_theta.shape
    assert len(d_spacing) == len(two_theta)

