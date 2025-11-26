"""
XRD Data Plotting Module

Provides plotting functionality using matplotlib for interactive graphs
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from typing import Optional, List, Tuple, Dict, Any


class XRDPlotter:
    """Plotter for XRD data"""
    
    def __init__(self, figure: Optional[Figure] = None):
        if figure is None:
            self.figure = Figure(figsize=(10, 6))
        else:
            self.figure = figure
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        
    def clear(self):
        """Clear the plot"""
        self.axes.clear()
    
    def plot_spectrum(self, two_theta: np.ndarray, intensity: np.ndarray,
                     label: str = 'Intensity', color: str = 'blue',
                     linewidth: float = 1.0, show_negative: bool = True):
        """
        Plot XRD spectrum
        
        Args:
            two_theta: Two-theta values
            intensity: Intensity values
            label: Label for the plot
            color: Line color
            linewidth: Line width
            show_negative: Whether to show negative values (after background subtraction)
        """
        self.axes.plot(two_theta, intensity, label=label, color=color, 
                      linewidth=linewidth)
        
        if show_negative:
            # Show negative values explicitly
            negative_mask = intensity < 0
            if np.any(negative_mask):
                self.axes.plot(two_theta[negative_mask], intensity[negative_mask],
                             'o', color='red', markersize=3, alpha=0.5,
                             label='Negative values')
    
    def plot_reference_pattern(self, two_theta: np.ndarray, intensity: np.ndarray,
                              label: str = 'Reference', color: str = 'green',
                              linestyle: str = '--', linewidth: float = 1.5,
                              alpha: float = 0.7):
        """
        Plot reference pattern overlay
        
        Args:
            two_theta: Two-theta values
            intensity: Intensity values
            label: Label for the plot
            color: Line color
            linestyle: Line style
            linewidth: Line width
            alpha: Transparency
        """
        self.axes.plot(two_theta, intensity, label=label, color=color,
                      linestyle=linestyle, linewidth=linewidth, alpha=alpha)
    
    def plot_peaks(self, two_theta: np.ndarray, intensity: np.ndarray,
                   label: str = 'Peaks', color: str = 'red',
                   marker: str = 'v', markersize: int = 8):
        """
        Plot peak positions
        
        Args:
            two_theta: Peak two-theta positions
            intensity: Peak intensities
            label: Label for the plot
            color: Marker color
            marker: Marker style
            markersize: Marker size
        """
        self.axes.plot(two_theta, intensity, marker=marker, color=color,
                      markersize=markersize, linestyle='None', label=label)
    
    def plot_background(self, two_theta: np.ndarray, background: np.ndarray,
                       label: str = 'Background', color: str = 'orange',
                       linestyle: str = '-', linewidth: float = 1.0,
                       alpha: float = 0.6):
        """
        Plot background line
        
        Args:
            two_theta: Two-theta values
            background: Background values
            label: Label for the plot
            color: Line color
            linestyle: Line style
            linewidth: Line width
            alpha: Transparency
        """
        self.axes.plot(two_theta, background, label=label, color=color,
                      linestyle=linestyle, linewidth=linewidth, alpha=alpha)
    
    def set_labels(self, xlabel: str = '2θ (degrees)', 
                   ylabel: str = 'Intensity (counts)'):
        """Set axis labels"""
        self.axes.set_xlabel(xlabel, fontsize=12)
        self.axes.set_ylabel(ylabel, fontsize=12)
    
    def set_title(self, title: str):
        """Set plot title"""
        self.axes.set_title(title, fontsize=14, fontweight='bold')
    
    def set_limits(self, xlim: Optional[Tuple[float, float]] = None,
                  ylim: Optional[Tuple[float, float]] = None):
        """Set axis limits"""
        if xlim:
            self.axes.set_xlim(xlim)
        if ylim:
            self.axes.set_ylim(ylim)
    
    def add_grid(self, alpha: float = 0.3):
        """Add grid to plot"""
        self.axes.grid(True, alpha=alpha)
    
    def add_legend(self, loc: str = 'upper right'):
        """Add legend to plot"""
        self.axes.legend(loc=loc, fontsize=9)
    
    def finalize(self):
        """Finalize plot with standard formatting"""
        self.axes.grid(True, alpha=0.3)
        self.axes.legend(loc='upper right', fontsize=9)
        self.figure.tight_layout()
    
    def get_canvas(self):
        """Get the canvas for embedding in GUI"""
        return self.canvas

