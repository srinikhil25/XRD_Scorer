"""
Background Subtraction Algorithms for XRD Data

Implements verified algorithms for background removal:
- Polynomial fitting
- Iterative polynomial fitting (Sonneveld-Visser method)
- Rolling ball algorithm
- Top-hat transform
"""

import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
from typing import Tuple, Optional


def polynomial_background(two_theta: np.ndarray, intensity: np.ndarray, 
                         degree: int = 6) -> Tuple[np.ndarray, np.ndarray]:
    """
    Subtract background using polynomial fitting
    
    This is a simple and commonly used method where a polynomial is fitted
    to the entire spectrum and subtracted.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        degree: Polynomial degree (default: 6)
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    # Fit polynomial
    coeffs = np.polyfit(two_theta, intensity, degree)
    background = np.polyval(coeffs, two_theta)
    
    # Subtract background (allow negative values)
    corrected = intensity - background
    
    return background, corrected


def iterative_polynomial_background(two_theta: np.ndarray, intensity: np.ndarray,
                                   degree: int = 6, iterations: int = 10,
                                   threshold: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Iterative polynomial background subtraction (Sonneveld-Visser method)
    
    This method iteratively fits a polynomial, but excludes points that are
    significantly above the fitted background (peaks) from subsequent fits.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        degree: Polynomial degree
        iterations: Number of iterations
        threshold: Threshold for peak exclusion (as fraction of intensity)
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    # Start with all points
    mask = np.ones(len(intensity), dtype=bool)
    background = np.zeros_like(intensity)
    
    for i in range(iterations):
        # Fit polynomial to non-excluded points
        coeffs = np.polyfit(two_theta[mask], intensity[mask], degree)
        background = np.polyval(coeffs, two_theta)
        
        # Exclude points significantly above background
        if i < iterations - 1:  # Don't update mask on last iteration
            residual = intensity - background
            threshold_value = threshold * np.max(intensity)
            mask = residual < threshold_value
    
    corrected = intensity - background
    
    return background, corrected


def rolling_ball_background(two_theta: np.ndarray, intensity: np.ndarray,
                           ball_radius: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Rolling ball background subtraction
    
    This method uses a morphological opening operation (rolling ball) to estimate
    the background. The ball radius should be larger than typical peak widths
    but smaller than background variations.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        ball_radius: Radius of rolling ball in data points (auto if None)
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    if ball_radius is None:
        # Auto-determine: use ~5% of data points, minimum 50
        ball_radius = max(50, int(len(intensity) * 0.05))
    
    # Create structuring element (ball)
    structure = np.ones(ball_radius)
    
    # Morphological opening: erosion followed by dilation
    # This removes peaks and keeps background
    background = ndimage.grey_opening(intensity, structure=structure)
    
    # Smooth the background
    background = ndimage.gaussian_filter1d(background, sigma=ball_radius/10)
    
    corrected = intensity - background
    
    return background, corrected


def tophat_background(two_theta: np.ndarray, intensity: np.ndarray,
                     structure_size: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Top-hat transform for background subtraction
    
    The top-hat transform is the difference between the original image
    and its morphological opening, which effectively removes the background.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        structure_size: Size of structuring element (auto if None)
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    if structure_size is None:
        structure_size = max(50, int(len(intensity) * 0.05))
    
    # Create structuring element
    structure = np.ones(structure_size)
    
    # Morphological opening
    opened = ndimage.grey_opening(intensity, structure=structure)
    
    # Background is the opened image
    background = opened
    
    # Top-hat: original - opened
    corrected = intensity - background
    
    return background, corrected


def snip_background(two_theta: np.ndarray, intensity: np.ndarray,
                   iterations: int = 100, reduction_factor: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    SNIP (Sensitive Nonlinear Iterative Peak) background subtraction
    
    This is a robust method that iteratively clips the spectrum to remove peaks.
    It's particularly good for noisy data.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        iterations: Number of iterations
        reduction_factor: Factor for reducing clipping window
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    background = intensity.copy()
    
    # Iterative clipping
    for i in range(iterations):
        # Window size decreases with iterations
        window = max(1, int(len(intensity) * reduction_factor ** i))
        
        if window < 3:
            break
        
        # Clip: take minimum in moving window
        for j in range(len(background)):
            start = max(0, j - window // 2)
            end = min(len(background), j + window // 2 + 1)
            background[j] = min(background[j], np.min(background[start:end]))
    
    corrected = intensity - background
    
    return background, corrected


def subtract_background(two_theta: np.ndarray, intensity: np.ndarray,
                       method: str = 'iterative_polynomial', **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    Main function for background subtraction
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        method: Method to use ('polynomial', 'iterative_polynomial', 'rolling_ball', 
                'tophat', 'snip')
        **kwargs: Additional parameters for the selected method
        
    Returns:
        Tuple of (background, corrected_intensity)
    """
    methods = {
        'polynomial': polynomial_background,
        'iterative_polynomial': iterative_polynomial_background,
        'rolling_ball': rolling_ball_background,
        'tophat': tophat_background,
        'snip': snip_background
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method](two_theta, intensity, **kwargs)

