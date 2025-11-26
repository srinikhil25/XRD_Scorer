"""
K-alpha Stripping (Kα2 Removal) Algorithms

Implements the Rachinger correction method for removing Kα2 component
from XRD data, leaving only Kα1 peaks.
"""

import numpy as np
from scipy.interpolate import interp1d
from typing import Tuple, Optional


def rachinger_correction(two_theta: np.ndarray, intensity: np.ndarray,
                        wavelength_ratio: float = 1.0025,
                        intensity_ratio: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Rachinger correction for Kα2 stripping
    
    This is the standard method for removing Kα2 component from XRD data.
    The method works by:
    1. Calculating the angular separation between Kα1 and Kα2 peaks
    2. Subtracting a scaled and shifted version of the spectrum
    
    The wavelength ratio λ(Kα2)/λ(Kα1) is typically ~1.0025 for Cu radiation.
    The intensity ratio I(Kα2)/I(Kα1) is typically ~0.5 for Cu radiation.
    
    Args:
        two_theta: Two-theta values in degrees
        intensity: Intensity values
        wavelength_ratio: Ratio λ(Kα2)/λ(Kα1), default 1.0025 for Cu
        intensity_ratio: Ratio I(Kα2)/I(Kα1), default 0.5 for Cu
        
    Returns:
        Tuple of (kalpha1_intensity, kalpha2_intensity)
    """
    # Calculate angular shift for Kα2
    # From Bragg's law: 2θ(Kα2) = 2 * arcsin(λ(Kα2) * sin(θ(Kα1)) / λ(Kα1))
    # For small differences: Δ(2θ) ≈ 2 * tan(θ) * (λ(Kα2)/λ(Kα1) - 1)
    
    theta = np.deg2rad(two_theta / 2)
    delta_two_theta = 2 * np.rad2deg(np.arctan(np.tan(theta) * (wavelength_ratio - 1)))
    
    # Create interpolated function for original spectrum
    # We need to handle edge cases where shifted values go out of range
    interp_func = interp1d(two_theta, intensity, kind='linear', 
                          bounds_error=False, fill_value=0.0)
    
    # Calculate shifted two-theta positions for Kα2
    two_theta_kalpha2 = two_theta - delta_two_theta
    
    # Get Kα2 intensities at shifted positions
    kalpha2_intensity = interp_func(two_theta_kalpha2) * intensity_ratio
    
    # Subtract Kα2 from original to get Kα1
    kalpha1_intensity = intensity - kalpha2_intensity
    
    # Ensure non-negative (though some methods allow negative)
    kalpha1_intensity = np.maximum(kalpha1_intensity, 0)
    
    return kalpha1_intensity, kalpha2_intensity


def iterative_rachinger_correction(two_theta: np.ndarray, intensity: np.ndarray,
                                  wavelength_ratio: float = 1.0025,
                                  intensity_ratio: float = 0.5,
                                  iterations: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Iterative Rachinger correction
    
    This method applies the Rachinger correction iteratively to better
    remove Kα2 components, especially in regions with overlapping peaks.
    
    Args:
        two_theta: Two-theta values in degrees
        intensity: Intensity values
        wavelength_ratio: Ratio λ(Kα2)/λ(Kα1)
        intensity_ratio: Ratio I(Kα2)/I(Kα1)
        iterations: Number of iterations
        
    Returns:
        Tuple of (kalpha1_intensity, kalpha2_intensity)
    """
    current_intensity = intensity.copy()
    
    for i in range(iterations):
        kalpha1, kalpha2 = rachinger_correction(
            two_theta, current_intensity, 
            wavelength_ratio, intensity_ratio
        )
        current_intensity = kalpha1
    
    # Final calculation
    kalpha1_final, kalpha2_final = rachinger_correction(
        two_theta, intensity,
        wavelength_ratio, intensity_ratio
    )
    
    return kalpha1_final, kalpha2_final


def strip_kalpha(two_theta: np.ndarray, intensity: np.ndarray,
                method: str = 'rachinger',
                wavelength: Optional[float] = None,
                **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Main function for K-alpha stripping
    
    Args:
        two_theta: Two-theta values in degrees
        intensity: Intensity values
        method: Method to use ('rachinger' or 'iterative_rachinger')
        wavelength: Wavelength in Angstroms (for auto-determining ratios)
        **kwargs: Additional parameters
        
    Returns:
        Tuple of (kalpha1_intensity, kalpha2_intensity)
    """
    # Auto-determine wavelength ratio if wavelength is provided
    if wavelength is not None:
        # Common wavelength ratios for different sources
        wavelength_ratios = {
            1.54184: 1.0025,  # Cu Kα
            1.54056: 1.0025,  # Cu Kα1
            1.54439: 1.0025,  # Cu Kα2
            1.79026: 1.0023,  # Co Kα
            0.70932: 1.0018,  # Mo Kα
        }
        
        # Find closest wavelength
        closest_wl = min(wavelength_ratios.keys(), key=lambda x: abs(x - wavelength))
        if 'wavelength_ratio' not in kwargs:
            kwargs['wavelength_ratio'] = wavelength_ratios[closest_wl]
    
    methods = {
        'rachinger': rachinger_correction,
        'iterative_rachinger': iterative_rachinger_correction
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method](two_theta, intensity, **kwargs)

