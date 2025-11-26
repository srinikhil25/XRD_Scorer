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
        
        # Enable zoom and pan
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
    
    def _on_click(self, event):
        """Handle mouse clicks for zoom"""
        if event.inaxes != self.axes:
            return
        if event.button == 2:  # Middle mouse button to reset
            self.axes.relim()
            self.axes.autoscale()
            self.canvas.draw()
    
    def _on_scroll(self, event):
        """Handle mouse scroll for zoom"""
        if event.inaxes != self.axes:
            return
        
        # Zoom with scroll wheel
        cur_xlim = self.axes.get_xlim()
        cur_ylim = self.axes.get_ylim()
        
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
        
        if event.button == 'up':
            # Zoom in
            scale_factor = 0.9
        elif event.button == 'down':
            # Zoom out
            scale_factor = 1.1
        else:
            return
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        self.axes.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.axes.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.canvas.draw()
        
    def clear(self):
        """Clear the plot"""
        self.axes.clear()
    
    def plot_spectrum(self, two_theta: np.ndarray, intensity: np.ndarray,
                     label: str = 'Intensity', color: str = 'blue',
                     linewidth: float = 0.8, show_negative: bool = True,
                     smooth: bool = False):
        """
        Plot XRD spectrum
        
        Args:
            two_theta: Two-theta values
            intensity: Intensity values
            label: Label for the plot
            color: Line color
            linewidth: Line width (reduced for thinner lines)
            show_negative: Whether to show negative values (after background subtraction)
            smooth: Whether to apply smoothing
        """
        # Apply smoothing if requested
        if smooth and len(intensity) > 10:
            from scipy.ndimage import gaussian_filter1d
            intensity_plot = gaussian_filter1d(intensity, sigma=1.0)
        else:
            intensity_plot = intensity
        
        self.axes.plot(two_theta, intensity_plot, label=label, color=color, 
                      linewidth=linewidth)
        
        if show_negative:
            # Show negative values explicitly
            negative_mask = intensity < 0
            if np.any(negative_mask):
                # Make negative markers same visual thickness as the line
                # Use very small markersize to match linewidth appearance
                marker_size = max(0.5, linewidth * 0.6)  # Smaller markers to match thin line
                self.axes.plot(two_theta[negative_mask], intensity[negative_mask],
                             'o', color='red', markersize=marker_size, 
                             markeredgewidth=0.2, alpha=0.7,
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
                   marker: str = 'v', markersize: int = 8,
                   show_values: bool = True, value_format: str = 'intensity'):
        """
        Plot peak positions
        
        Args:
            two_theta: Peak two-theta positions
            intensity: Peak intensities
            label: Label for the plot
            color: Marker color
            marker: Marker style
            markersize: Marker size
            show_values: Whether to show peak values as text labels
            value_format: Format for values ('intensity', 'two_theta', or 'both')
        """
        self.axes.plot(two_theta, intensity, marker=marker, color=color,
                      markersize=markersize, linestyle='None', label=label)
        
        # Add text labels for peak values
        if show_values:
            for tt, inten in zip(two_theta, intensity):
                # Determine what to display
                if value_format == 'intensity':
                    text = f'{inten:.0f}'
                elif value_format == 'two_theta':
                    text = f'{tt:.2f}°'
                elif value_format == 'both':
                    text = f'{tt:.1f}°\n{inten:.0f}'
                else:
                    text = f'{inten:.0f}'
                
                # Position text above the peak marker
                # Offset by a small percentage of the y-axis range
                y_range = self.axes.get_ylim()[1] - self.axes.get_ylim()[0]
                y_offset = y_range * 0.03  # 3% of y-axis range
                
                self.axes.annotate(
                    text,
                    xy=(tt, inten),
                    xytext=(tt, inten + y_offset),
                    ha='center',
                    va='bottom',
                    fontsize=7,
                    color=color,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor=color, alpha=0.7, linewidth=0.5)
                )
    
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

