"""
Pytest configuration and fixtures
"""

import numpy as np
import pytest


@pytest.fixture
def sample_two_theta():
    """Fixture providing sample two-theta array"""
    return np.linspace(10, 80, 1000)


@pytest.fixture
def sample_intensity():
    """Fixture providing sample intensity array"""
    # Create synthetic data with some peaks
    intensity = np.random.rand(1000) * 100 + 50
    intensity[200] = 1000  # Peak
    intensity[500] = 800   # Peak
    intensity[700] = 600   # Peak
    return intensity


@pytest.fixture
def sample_xrd_data():
    """Fixture providing sample XRDData object"""
    from src.core.file_parser import XRDData
    
    two_theta = np.linspace(20, 70, 500)
    intensity = np.random.rand(500) * 1000
    wavelength = 1.54056  # Cu Kα1
    
    return XRDData(two_theta, intensity, wavelength=wavelength)

