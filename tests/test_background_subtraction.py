"""
Tests for background subtraction algorithms
"""

import numpy as np
import pytest
from src.core.background_subtraction import (
    polynomial_background,
    iterative_polynomial_background,
    rolling_ball_background,
    tophat_background,
    snip_background,
    subtract_background
)


def test_polynomial_background_shape():
    """Test that polynomial background returns arrays of same shape"""
    two_theta = np.linspace(10, 80, 1000)
    intensity = np.random.rand(1000) * 1000 + 100
    
    background, corrected = polynomial_background(two_theta, intensity, degree=6)
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_polynomial_background_degrees():
    """Test polynomial background with different degrees"""
    two_theta = np.linspace(20, 70, 500)
    intensity = np.random.rand(500) * 800
    
    for degree in [3, 6, 9]:
        background, corrected = polynomial_background(
            two_theta, intensity, degree=degree
        )
        assert background.shape == intensity.shape
        assert corrected.shape == intensity.shape


def test_iterative_polynomial_background_shape():
    """Test iterative polynomial background returns correct shapes"""
    two_theta = np.linspace(15, 75, 800)
    intensity = np.random.rand(800) * 900
    
    background, corrected = iterative_polynomial_background(
        two_theta, intensity, degree=6, iterations=10
    )
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_rolling_ball_background_shape():
    """Test rolling ball background returns correct shapes"""
    two_theta = np.linspace(10, 80, 600)
    intensity = np.random.rand(600) * 700
    
    background, corrected = rolling_ball_background(two_theta, intensity)
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_rolling_ball_background_custom_radius():
    """Test rolling ball with custom radius"""
    two_theta = np.linspace(20, 60, 400)
    intensity = np.random.rand(400) * 600
    
    background, corrected = rolling_ball_background(
        two_theta, intensity, ball_radius=100
    )
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_tophat_background_shape():
    """Test top-hat background returns correct shapes"""
    two_theta = np.linspace(15, 70, 500)
    intensity = np.random.rand(500) * 800
    
    background, corrected = tophat_background(two_theta, intensity)
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_snip_background_shape():
    """Test SNIP background returns correct shapes"""
    two_theta = np.linspace(20, 65, 400)
    intensity = np.random.rand(400) * 750
    
    background, corrected = snip_background(two_theta, intensity)
    
    assert background.shape == intensity.shape
    assert corrected.shape == intensity.shape


def test_subtract_background_all_methods():
    """Test subtract_background with all available methods"""
    two_theta = np.linspace(10, 80, 500)
    intensity = np.random.rand(500) * 1000
    
    methods = ['polynomial', 'iterative_polynomial', 'rolling_ball', 
               'tophat', 'snip']
    
    for method in methods:
        background, corrected = subtract_background(
            two_theta, intensity, method=method
        )
        assert background.shape == intensity.shape
        assert corrected.shape == intensity.shape


def test_subtract_background_invalid_method():
    """Test that subtract_background raises error for invalid method"""
    two_theta = np.linspace(20, 60, 300)
    intensity = np.random.rand(300) * 500
    
    with pytest.raises(ValueError, match="Unknown method"):
        subtract_background(two_theta, intensity, method='invalid_method')


def test_background_subtraction_finite_values():
    """Test that all background subtraction methods return finite values"""
    two_theta = np.linspace(15, 75, 400)
    intensity = np.random.rand(400) * 800
    
    methods = [
        polynomial_background,
        lambda tt, i: iterative_polynomial_background(tt, i),
        rolling_ball_background,
        tophat_background,
        snip_background
    ]
    
    for method in methods:
        background, corrected = method(two_theta, intensity)
        assert np.all(np.isfinite(background))
        assert np.all(np.isfinite(corrected))


def test_background_subtraction_edge_cases():
    """Test background subtraction with edge cases"""
    # Small array
    two_theta_small = np.array([20.0, 40.0, 60.0])
    intensity_small = np.array([100, 200, 150])
    
    background, corrected = polynomial_background(
        two_theta_small, intensity_small, degree=2
    )
    assert background.shape == intensity_small.shape
    
    # Constant intensity
    two_theta_const = np.linspace(20, 60, 100)
    intensity_const = np.ones(100) * 500
    
    background, corrected = polynomial_background(
        two_theta_const, intensity_const
    )
    assert background.shape == intensity_const.shape

