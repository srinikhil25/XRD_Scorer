"""
Peak Detection Module for XRD Data

Implements various peak detection algorithms:
- Simple threshold-based detection
- Peak prominence detection (scipy)
- Derivative-based detection
- Savitzky-Golay filter based detection
"""

import numpy as np
from scipy.signal import find_peaks, savgol_filter
from scipy.ndimage import maximum_filter1d
from typing import List, Tuple, Optional, Dict


class DetectedPeak:
    """Container for a detected peak"""
    
    def __init__(self, two_theta: float, intensity: float, index: int, 
                 width: Optional[float] = None, prominence: Optional[float] = None):
        self.two_theta = two_theta
        self.intensity = intensity
        self.index = index
        self.width = width
        self.prominence = prominence
    
    def __repr__(self):
        return f"Peak(2θ={self.two_theta:.2f}°, I={self.intensity:.1f})"


def detect_peaks_threshold(two_theta: np.ndarray, intensity: np.ndarray,
                          threshold: Optional[float] = None,
                          min_distance: int = 5) -> List[DetectedPeak]:
    """
    Simple threshold-based peak detection
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        threshold: Intensity threshold (if None, uses 10% of max)
        min_distance: Minimum distance between peaks (in data points)
        
    Returns:
        List of DetectedPeak objects
    """
    if threshold is None:
        threshold = np.max(intensity) * 0.1
    
    # Find local maxima
    peaks = []
    for i in range(min_distance, len(intensity) - min_distance):
        if intensity[i] > threshold:
            # Check if it's a local maximum
            is_peak = True
            for j in range(max(0, i - min_distance), min(len(intensity), i + min_distance + 1)):
                if j != i and intensity[j] >= intensity[i]:
                    is_peak = False
                    break
            
            if is_peak:
                peaks.append(DetectedPeak(two_theta[i], intensity[i], i))
    
    return peaks


def detect_peaks_prominence(two_theta: np.ndarray, intensity: np.ndarray,
                            prominence: Optional[float] = None,
                            height: Optional[float] = None,
                            distance: Optional[int] = None,
                            width: Optional[int] = None) -> List[DetectedPeak]:
    """
    Peak detection using prominence (scipy.find_peaks)
    
    This is the recommended method as it's robust and handles noise well.
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        prominence: Minimum peak prominence (if None, uses 5% of max)
        height: Minimum peak height (optional)
        distance: Minimum distance between peaks in data points
        width: Minimum peak width in data points (optional)
        
    Returns:
        List of DetectedPeak objects
    """
    if prominence is None:
        prominence = np.max(intensity) * 0.05
    
    if distance is None:
        # Auto-determine: ~0.1 degree spacing
        if len(two_theta) > 1:
            spacing = two_theta[1] - two_theta[0]
            distance = max(1, int(0.1 / spacing))
        else:
            distance = 5
    
    # Find peaks using scipy
    peak_indices, properties = find_peaks(
        intensity,
        prominence=prominence,
        height=height,
        distance=distance,
        width=width
    )
    
    peaks = []
    for idx in peak_indices:
        peak = DetectedPeak(
            two_theta[idx],
            intensity[idx],
            idx,
            width=properties.get('widths', [None])[list(peak_indices).index(idx)] if 'widths' in properties else None,
            prominence=properties.get('prominences', [None])[list(peak_indices).index(idx)] if 'prominences' in properties else None
        )
        peaks.append(peak)
    
    return peaks


def detect_peaks_derivative(two_theta: np.ndarray, intensity: np.ndarray,
                           threshold: Optional[float] = None,
                           min_distance: int = 5) -> List[DetectedPeak]:
    """
    Peak detection using first derivative (zero-crossing method)
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        threshold: Minimum intensity for peak (if None, uses 10% of max)
        min_distance: Minimum distance between peaks (in data points)
        
    Returns:
        List of DetectedPeak objects
    """
    if threshold is None:
        threshold = np.max(intensity) * 0.1
    
    # Calculate first derivative
    dy = np.diff(intensity)
    
    # Find zero crossings (where derivative changes from positive to negative)
    peaks = []
    for i in range(1, len(dy)):
        if dy[i-1] > 0 and dy[i] < 0:  # Zero crossing (peak)
            if intensity[i] > threshold:
                # Check minimum distance
                if not peaks or (i - peaks[-1].index) >= min_distance:
                    peaks.append(DetectedPeak(two_theta[i], intensity[i], i))
    
    return peaks


def detect_peaks_savgol(two_theta: np.ndarray, intensity: np.ndarray,
                        window_length: int = 11,
                        poly_order: int = 3,
                        prominence: Optional[float] = None,
                        distance: Optional[int] = None) -> List[DetectedPeak]:
    """
    Peak detection using Savitzky-Golay filter for smoothing
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        window_length: Window length for Savitzky-Golay filter (must be odd)
        poly_order: Polynomial order for filter
        prominence: Minimum peak prominence
        distance: Minimum distance between peaks
        
    Returns:
        List of DetectedPeak objects
    """
    # Smooth the data
    if window_length % 2 == 0:
        window_length += 1
    
    if window_length > len(intensity):
        window_length = len(intensity) if len(intensity) % 2 == 1 else len(intensity) - 1
    
    if window_length < 3:
        window_length = 3
    
    smoothed = savgol_filter(intensity, window_length, poly_order)
    
    # Use prominence-based detection on smoothed data
    return detect_peaks_prominence(two_theta, smoothed, prominence, distance=distance)


def detect_peaks(two_theta: np.ndarray, intensity: np.ndarray,
                method: str = 'prominence', **kwargs) -> List[DetectedPeak]:
    """
    Main function for peak detection
    
    Args:
        two_theta: Two-theta values
        intensity: Intensity values
        method: Method to use ('prominence', 'threshold', 'derivative', 'savgol')
        **kwargs: Additional parameters for the selected method
        
    Returns:
        List of DetectedPeak objects
    """
    methods = {
        'prominence': detect_peaks_prominence,
        'threshold': detect_peaks_threshold,
        'derivative': detect_peaks_derivative,
        'savgol': detect_peaks_savgol
    }
    
    if method not in methods:
        raise ValueError(f"Unknown method: {method}. Available: {list(methods.keys())}")
    
    return methods[method](two_theta, intensity, **kwargs)


def match_peaks_with_reference(detected_peaks: List[DetectedPeak],
                               reference_pattern,
                               tolerance: float = 0.2) -> Dict:
    """
    Match detected peaks with reference pattern peaks
    
    Args:
        detected_peaks: List of detected peaks from experimental data
        reference_pattern: ReferencePattern object
        tolerance: Tolerance for matching (in degrees 2θ)
        
    Returns:
        Dictionary with matching information:
        - matched_peaks: List of (detected_peak, reference_peak) tuples
        - unmatched_detected: List of unmatched detected peaks
        - unmatched_reference: List of unmatched reference peaks
        - match_score: Percentage of reference peaks matched
    """
    if reference_pattern.two_theta is None:
        return {
            'matched_peaks': [],
            'unmatched_detected': detected_peaks,
            'unmatched_reference': [],
            'match_score': 0.0
        }
    
    matched_peaks = []
    matched_ref_indices = set()
    
    # Match each detected peak with closest reference peak
    for det_peak in detected_peaks:
        best_match = None
        best_distance = tolerance
        
        for i, ref_tt in enumerate(reference_pattern.two_theta):
            if i in matched_ref_indices:
                continue
            
            distance = abs(det_peak.two_theta - ref_tt)
            if distance < best_distance:
                best_distance = distance
                best_match = (i, ref_tt, reference_pattern.intensity[i] if reference_pattern.intensity is not None else 0)
        
        if best_match:
            matched_peaks.append((det_peak, best_match))
            matched_ref_indices.add(best_match[0])
    
    # Find unmatched peaks
    unmatched_detected = [p for p in detected_peaks 
                         if not any(p == mp[0] for mp in matched_peaks)]
    
    unmatched_ref_indices = set(range(len(reference_pattern.two_theta))) - matched_ref_indices
    unmatched_reference = [(reference_pattern.two_theta[i], 
                           reference_pattern.intensity[i] if reference_pattern.intensity is not None else 0)
                          for i in unmatched_ref_indices]
    
    # Calculate match score
    total_ref_peaks = len(reference_pattern.two_theta)
    match_score = (len(matched_peaks) / total_ref_peaks * 100) if total_ref_peaks > 0 else 0.0
    
    return {
        'matched_peaks': matched_peaks,
        'unmatched_detected': unmatched_detected,
        'unmatched_reference': unmatched_reference,
        'match_score': match_score
    }

