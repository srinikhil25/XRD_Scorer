"""
Main Window for XRD Scorer Application

Provides the main user interface with file loading, processing, and visualization
"""

import sys
import re
import json
import numpy as np
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QLabel, QComboBox,
                             QSpinBox, QDoubleSpinBox, QGroupBox, QMessageBox,
                             QSplitter, QStatusBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
try:
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
except ImportError:
    # Fallback for older matplotlib versions
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from ..core.file_parser import parse_xrd_file, XRDData
from ..core.background_subtraction import subtract_background
from ..core.kalpha_stripping import strip_kalpha
from ..core.reference_pattern import ReferenceDatabase, ReferencePattern
from ..core.peak_detection import detect_peaks, match_peaks_with_reference, DetectedPeak
from ..core.project_manager import ProjectManager
from ..visualization.plotter import XRDPlotter


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_data: Optional[XRDData] = None
        self.processed_data: Optional[XRDData] = None
        self.reference_db: Optional[ReferenceDatabase] = None
        self.plotter: Optional[XRDPlotter] = None
        self.current_ref_pattern = None
        self.detected_peaks: List[DetectedPeak] = []
        self.peak_match_result = None
        self.project_manager = ProjectManager()
        self.current_file_path: Optional[str] = None
        
        self.init_ui()
        self.load_reference_database()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("XRD Scorer - X-ray Diffraction Data Analysis")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel: Controls
        self.left_panel = self.create_control_panel()
        self.splitter.addWidget(self.left_panel)
        
        # Right panel: Visualization
        right_panel = self.create_visualization_panel()
        self.splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        self.splitter.setSizes([300, 1100])
        
        # Store original left panel width for collapse/expand
        self.left_panel_min_width = 50  # Minimum width when collapsed (10%)
        self.left_panel_max_width = 400  # Maximum width when expanded
        self.is_collapsed = False
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_action = QAction('Open XRD File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        load_db_action = QAction('Load Reference Database...', self)
        load_db_action.triggered.connect(self.load_reference_database_dialog)
        tools_menu.addAction(load_db_action)
        
        tools_menu.addSeparator()
        
        view_projects_action = QAction('View Projects...', self)
        view_projects_action.triggered.connect(self.view_projects)
        tools_menu.addAction(view_projects_action)
        
        open_project_action = QAction('Open Project...', self)
        open_project_action.triggered.connect(self.open_project)
        tools_menu.addAction(open_project_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Add collapse/expand button at the top
        collapse_btn = QPushButton("◄ Collapse")
        collapse_btn.setMaximumWidth(100)
        collapse_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(collapse_btn)
        self.collapse_btn = collapse_btn
        
        # File loading section
        file_group = QGroupBox("File Loading")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        load_btn = QPushButton("Load XRD File")
        load_btn.clicked.connect(self.open_file)
        file_layout.addWidget(load_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Background subtraction section
        bg_group = QGroupBox("Background Subtraction")
        bg_layout = QVBoxLayout()
        
        self.bg_method_combo = QComboBox()
        self.bg_method_combo.addItems([
            'iterative_polynomial',
            'polynomial',
            'rolling_ball',
            'tophat',
            'snip'
        ])
        bg_layout.addWidget(QLabel("Method:"))
        bg_layout.addWidget(self.bg_method_combo)
        
        self.bg_degree_spin = QSpinBox()
        self.bg_degree_spin.setRange(2, 12)
        self.bg_degree_spin.setValue(6)
        bg_layout.addWidget(QLabel("Polynomial Degree:"))
        bg_layout.addWidget(self.bg_degree_spin)
        
        self.bg_show_checkbox = QLabel("Show negative values: Yes")
        bg_layout.addWidget(self.bg_show_checkbox)
        
        apply_bg_btn = QPushButton("Apply Background Subtraction")
        apply_bg_btn.clicked.connect(self.apply_background_subtraction)
        bg_layout.addWidget(apply_bg_btn)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
        # K-alpha stripping section
        ka_group = QGroupBox("K-alpha Stripping")
        ka_layout = QVBoxLayout()
        
        self.ka_method_combo = QComboBox()
        self.ka_method_combo.addItems(['rachinger', 'iterative_rachinger'])
        ka_layout.addWidget(QLabel("Method:"))
        ka_layout.addWidget(self.ka_method_combo)
        
        self.ka_wavelength_spin = QDoubleSpinBox()
        self.ka_wavelength_spin.setRange(0.5, 3.0)
        self.ka_wavelength_spin.setValue(1.54056)
        self.ka_wavelength_spin.setDecimals(5)
        self.ka_wavelength_spin.setSingleStep(0.00001)
        ka_layout.addWidget(QLabel("Wavelength (Å):"))
        ka_layout.addWidget(self.ka_wavelength_spin)
        
        apply_ka_btn = QPushButton("Apply K-alpha Stripping")
        apply_ka_btn.clicked.connect(self.apply_kalpha_stripping)
        ka_layout.addWidget(apply_ka_btn)
        
        ka_group.setLayout(ka_layout)
        layout.addWidget(ka_group)
        
        # Peak detection section
        peak_group = QGroupBox("Peak Detection")
        peak_layout = QVBoxLayout()
        
        self.peak_method_combo = QComboBox()
        self.peak_method_combo.addItems(['prominence', 'threshold', 'derivative', 'savgol'])
        peak_layout.addWidget(QLabel("Method:"))
        peak_layout.addWidget(self.peak_method_combo)
        
        self.peak_prominence_spin = QDoubleSpinBox()
        self.peak_prominence_spin.setRange(0.1, 100.0)
        self.peak_prominence_spin.setValue(5.0)
        self.peak_prominence_spin.setSuffix("%")
        peak_layout.addWidget(QLabel("Min Prominence (% of max):"))
        peak_layout.addWidget(self.peak_prominence_spin)
        
        detect_peaks_btn = QPushButton("Detect Peaks")
        detect_peaks_btn.clicked.connect(self.detect_peaks)
        peak_layout.addWidget(detect_peaks_btn)
        
        self.peak_count_label = QLabel("Peaks detected: 0")
        peak_layout.addWidget(self.peak_count_label)
        
        # Show filtered peaks info
        self.filtered_peaks_label = QLabel("")
        self.filtered_peaks_label.setStyleSheet("color: #888; font-size: 8pt;")
        self.filtered_peaks_label.setWordWrap(True)
        peak_layout.addWidget(self.filtered_peaks_label)
        
        peak_group.setLayout(peak_layout)
        layout.addWidget(peak_group)
        
        # Reference patterns section
        ref_group = QGroupBox("Reference Patterns")
        ref_layout = QVBoxLayout()
        
        self.ref_search_combo = QComboBox()
        self.ref_search_combo.setEditable(True)
        self.ref_search_combo.setPlaceholderText("Search reference patterns...")
        ref_layout.addWidget(QLabel("Search:"))
        ref_layout.addWidget(self.ref_search_combo)
        
        self.ref_overlay_checkbox = QLabel("Overlay: Off")
        ref_layout.addWidget(self.ref_overlay_checkbox)
        
        overlay_ref_btn = QPushButton("Overlay Selected Pattern")
        overlay_ref_btn.clicked.connect(self.overlay_reference_pattern)
        ref_layout.addWidget(overlay_ref_btn)
        
        match_peaks_btn = QPushButton("Match Peaks with Reference")
        match_peaks_btn.clicked.connect(self.match_peaks_with_reference)
        ref_layout.addWidget(match_peaks_btn)
        
        self.match_score_label = QLabel("Match Score: -")
        ref_layout.addWidget(self.match_score_label)
        
        ref_group.setLayout(ref_layout)
        layout.addWidget(ref_group)
        
        # Processing options
        process_group = QGroupBox("Processing Options")
        process_layout = QVBoxLayout()
        
        reset_btn = QPushButton("Reset to Original")
        reset_btn.clicked.connect(self.reset_data)
        process_layout.addWidget(reset_btn)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        layout.addStretch()
        
        return panel
    
    def create_visualization_panel(self) -> QWidget:
        """Create the visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create plotter
        self.plotter = XRDPlotter()
        
        # Add navigation toolbar for zoom/pan
        toolbar = NavigationToolbar(self.plotter.get_canvas(), panel)
        layout.addWidget(toolbar)
        
        # Add canvas
        layout.addWidget(self.plotter.get_canvas())
        
        return panel
    
    def open_file(self):
        """Open XRD file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open XRD File",
            "",
            "XRD Files (*.xrdml *.dat *.asc *.txt *.raw);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_data = parse_xrd_file(file_path)
                self.processed_data = None
                self.current_file_path = file_path
                
                # Create new project for this analysis
                project_path = self.project_manager.create_project(
                    Path(file_path).name,
                    file_path
                )
                
                # Save original data
                self.project_manager.save_original_data(
                    self.current_data.two_theta,
                    self.current_data.intensity,
                    self.current_data.wavelength,
                    self.current_data.metadata
                )
                
                # Save initial visualization
                self.update_plot()
                if self.plotter:
                    self.project_manager.save_visualization(
                        "01_original_spectrum",
                        self.plotter.figure
                    )
                
                self.file_label.setText(f"Loaded: {Path(file_path).name}")
                self.statusBar.showMessage(
                    f"Loaded file: {Path(file_path).name} | Project: {project_path.name}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def apply_background_subtraction(self):
        """Apply background subtraction"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "Please load a file first")
            return
        
        try:
            method = self.bg_method_combo.currentText()
            degree = self.bg_degree_spin.value()
            
            kwargs = {}
            if 'polynomial' in method:
                kwargs['degree'] = degree
            
            background, corrected = subtract_background(
                self.current_data.two_theta,
                self.current_data.intensity,
                method=method,
                **kwargs
            )
            
            # Update processed data
            if self.processed_data is None:
                self.processed_data = XRDData(
                    self.current_data.two_theta.copy(),
                    self.current_data.intensity.copy(),
                    self.current_data.wavelength,
                    self.current_data.metadata.copy()
                )
            
            self.processed_data.intensity = corrected
            
            # Save processed data
            self.project_manager.save_processed_data(
                "background_subtraction",
                self.processed_data.two_theta,
                self.processed_data.intensity,
                {"method": method, "degree": degree, **kwargs}
            )
            
            # Save visualization
            self.update_plot()
            if self.plotter:
                self.project_manager.save_visualization(
                    "02_background_subtracted",
                    self.plotter.figure
                )
            
            self.statusBar.showMessage(f"Background subtracted using {method}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Background subtraction failed:\n{str(e)}")
    
    def apply_kalpha_stripping(self):
        """Apply K-alpha stripping"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "Please load a file first")
            return
        
        try:
            method = self.ka_method_combo.currentText()
            wavelength = self.ka_wavelength_spin.value()
            
            # Use processed data if available, otherwise original
            data_to_use = self.processed_data if self.processed_data else self.current_data
            
            kalpha1, kalpha2 = strip_kalpha(
                data_to_use.two_theta,
                data_to_use.intensity,
                method=method,
                wavelength=wavelength
            )
            
            # Update processed data
            if self.processed_data is None:
                self.processed_data = XRDData(
                    self.current_data.two_theta.copy(),
                    self.current_data.intensity.copy(),
                    self.current_data.wavelength,
                    self.current_data.metadata.copy()
                )
            
            self.processed_data.intensity = kalpha1
            
            # Save processed data
            self.project_manager.save_processed_data(
                "kalpha_stripping",
                self.processed_data.two_theta,
                self.processed_data.intensity,
                {"method": method, "wavelength": wavelength}
            )
            
            # Save visualization
            self.update_plot()
            if self.plotter:
                self.project_manager.save_visualization(
                    "03_kalpha_stripped",
                    self.plotter.figure
                )
            
            self.statusBar.showMessage(f"K-alpha stripping applied using {method}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"K-alpha stripping failed:\n{str(e)}")
    
    def overlay_reference_pattern(self):
        """Overlay reference pattern on plot"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "Please load a file first")
            return
        
        if self.reference_db is None or len(self.reference_db) == 0:
            QMessageBox.warning(self, "Warning", "No reference database loaded")
            return
        
        search_text = self.ref_search_combo.currentText()
        if not search_text:
            QMessageBox.warning(self, "Warning", "Please enter a search term")
            return
        
        # Strip source suffix like "(ICDD)" or "(MP)" from search text
        search_text_clean = re.sub(r'\s*\([^)]+\)\s*$', '', search_text).strip()
        
        patterns = self.reference_db.search(search_text_clean)
        if not patterns:
            QMessageBox.warning(self, "Warning", f"No patterns found matching: {search_text_clean}")
            return
        
        # Use first match
        pattern = patterns[0]
        
        # Get two-theta range from current data
        tt_min = np.min(self.current_data.two_theta)
        tt_max = np.max(self.current_data.two_theta)
        
        # Use discrete peaks (not continuous) for publication-ready stick plot
        # Filter peaks within the two-theta range
        if pattern.two_theta is not None and pattern.intensity is not None:
            mask = (pattern.two_theta >= tt_min) & (pattern.two_theta <= tt_max)
            tt_ref = pattern.two_theta[mask]
            int_ref = pattern.intensity[mask]
            
            # Normalize intensity to match current data scale (30% of max for visibility)
            if len(int_ref) > 0:
                max_current = np.max(self.current_data.intensity)
                max_ref = np.max(int_ref)
                if max_ref > 0:
                    # Scale to 30% of max intensity for clear visibility without overwhelming
                    int_ref = (int_ref / max_ref) * max_current * 0.3
        else:
            # Fallback: generate continuous pattern if discrete peaks not available
            tt_ref, int_ref = pattern.get_continuous_pattern((tt_min, tt_max))
            if len(int_ref) > 0:
                max_current = np.max(self.current_data.intensity)
                max_ref = np.max(int_ref)
                if max_ref > 0:
                    int_ref = (int_ref / max_ref) * max_current * 0.3
        
        # Store for plotting
        self.current_ref_pattern = (tt_ref, int_ref, pattern.name)
        
        # Save visualization with reference overlay
        self.update_plot()
        if self.plotter:
            safe_name = pattern.name.replace(" ", "_").replace("/", "_")
            self.project_manager.save_visualization(
                f"05_reference_overlay_{safe_name}",
                self.plotter.figure
            )
        
        self.statusBar.showMessage(f"Overlaying reference: {pattern.name}")
    
    def detect_peaks(self):
        """Detect peaks in the current data"""
        data_to_use = self.processed_data if self.processed_data else self.current_data
        
        if data_to_use is None:
            QMessageBox.warning(self, "Warning", "Please load a file first")
            return
        
        try:
            method = self.peak_method_combo.currentText()
            prominence_pct = self.peak_prominence_spin.value()
            
            # Calculate prominence as absolute value
            max_intensity = np.max(data_to_use.intensity)
            prominence = max_intensity * (prominence_pct / 100.0)
            
            # Detect peaks
            self.detected_peaks = detect_peaks(
                data_to_use.two_theta,
                data_to_use.intensity,
                method=method,
                prominence=prominence
            )
            
            self.peak_count_label.setText(f"Peaks detected: {len(self.detected_peaks)}")
            
            # Show filtered peaks (peaks that were missed) for prominence method
            if method == 'prominence':
                from ..core.peak_detection import get_filtered_peaks
                
                # Auto-calculate distance if needed
                if len(data_to_use.two_theta) > 1:
                    spacing = data_to_use.two_theta[1] - data_to_use.two_theta[0]
                    distance = max(1, int(0.1 / spacing))
                else:
                    distance = 5
                
                filtered_peaks = get_filtered_peaks(
                    data_to_use.two_theta,
                    data_to_use.intensity,
                    prominence,
                    distance=distance
                )
                
                if filtered_peaks and len(filtered_peaks) > 0:
                    filtered_count = len(filtered_peaks)
                    # Show a few examples
                    examples = filtered_peaks[:3]
                    example_text = ", ".join([f"{p['intensity']:.0f}@{p['two_theta']:.1f}°" 
                                             for p in examples])
                    if filtered_count > 3:
                        example_text += f" (+{filtered_count-3} more)"
                    
                    self.filtered_peaks_label.setText(
                        f"⚠ {filtered_count} valid peaks filtered\n"
                        f"(prominence < {prominence:.0f} counts)\n"
                        f"Examples: {example_text}\n"
                        f"💡 Lower prominence to 1-2% to detect them"
                    )
                else:
                    self.filtered_peaks_label.setText("")
            else:
                self.filtered_peaks_label.setText("")
            
            # Save peak detection results
            self.project_manager.save_peak_detection(
                self.detected_peaks,
                method,
                {"prominence_percent": prominence_pct, "prominence_absolute": prominence}
            )
            
            # Save visualization
            self.update_plot()
            if self.plotter:
                self.project_manager.save_visualization(
                    "04_peaks_detected",
                    self.plotter.figure
                )
            
            self.statusBar.showMessage(f"Detected {len(self.detected_peaks)} peaks using {method}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Peak detection failed:\n{str(e)}")
    
    def match_peaks_with_reference(self):
        """Match detected peaks with reference pattern"""
        if len(self.detected_peaks) == 0:
            QMessageBox.warning(self, "Warning", "Please detect peaks first")
            return
        
        if self.reference_db is None or len(self.reference_db) == 0:
            QMessageBox.warning(self, "Warning", "No reference database loaded")
            return
        
        search_text = self.ref_search_combo.currentText()
        if not search_text:
            QMessageBox.warning(self, "Warning", "Please select a reference pattern")
            return
        
        # Strip source suffix like "(ICDD)" or "(MP)" from search text
        search_text_clean = re.sub(r'\s*\([^)]+\)\s*$', '', search_text).strip()
        
        patterns = self.reference_db.search(search_text_clean)
        if not patterns:
            QMessageBox.warning(self, "Warning", f"No patterns found matching: {search_text_clean}")
            return
        
        # Use first match
        pattern = patterns[0]
        
        # Match peaks
        self.peak_match_result = match_peaks_with_reference(
            self.detected_peaks,
            pattern,
            tolerance=0.2  # 0.2 degree tolerance
        )
        
        match_score = self.peak_match_result['match_score']
        matched_count = len(self.peak_match_result['matched_peaks'])
        total_ref_peaks = len(pattern.two_theta) if pattern.two_theta is not None else 0
        
        self.match_score_label.setText(
            f"Match Score: {match_score:.1f}% ({matched_count}/{total_ref_peaks} peaks matched)"
        )
        
        # Save match results
        pattern_data = {
            "id": pattern.id,
            "name": pattern.name,
            "source": pattern.data.get("source"),
            "two_theta": pattern.two_theta.tolist() if pattern.two_theta is not None else [],
            "intensity": pattern.intensity.tolist() if pattern.intensity is not None else []
        }
        self.project_manager.save_reference_match(
            pattern.name,
            self.peak_match_result,
            pattern_data
        )
        
        # Also overlay the reference pattern
        self.overlay_reference_pattern()
        
        # Save visualization with matched peaks
        self.update_plot()
        if self.plotter:
            safe_name = pattern.name.replace(" ", "_").replace("/", "_")
            self.project_manager.save_visualization(
                f"06_peaks_matched_{safe_name}",
                self.plotter.figure
            )
        
        self.statusBar.showMessage(
            f"Matched {matched_count} peaks with {pattern.name} (Score: {match_score:.1f}%)"
        )
    
    def toggle_sidebar(self):
        """Toggle sidebar collapse/expand"""
        current_sizes = self.splitter.sizes()
        total_width = sum(current_sizes)
        
        if self.is_collapsed:
            # Expand: restore to ~30% of total width
            new_left_width = int(total_width * 0.3)
            self.splitter.setSizes([new_left_width, total_width - new_left_width])
            self.collapse_btn.setText("◄ Collapse")
            self.is_collapsed = False
        else:
            # Collapse: reduce to ~10% of total width
            new_left_width = int(total_width * 0.1)
            self.splitter.setSizes([new_left_width, total_width - new_left_width])
            self.collapse_btn.setText("► Expand")
            self.is_collapsed = True
    
    def reset_data(self):
        """Reset to original data - clears all processing, peaks, and reference patterns"""
        # Clear processed data
        self.processed_data = None
        
        # Clear reference pattern overlay
        self.current_ref_pattern = None
        
        # Clear peak detection results
        self.detected_peaks = []
        self.peak_match_result = None
        
        # Reset UI labels
        if hasattr(self, 'peak_count_label'):
            self.peak_count_label.setText("Peaks detected: 0")
        if hasattr(self, 'filtered_peaks_label'):
            self.filtered_peaks_label.setText("")
        if hasattr(self, 'match_score_label'):
            self.match_score_label.setText("Match Score: -")
        if hasattr(self, 'ref_overlay_checkbox'):
            self.ref_overlay_checkbox.setText("Overlay: Off")
        
        # Update plot (will clear all overlays)
        self.statusBar.showMessage("Reset to original data")
        self.update_plot()
    
    def update_plot(self):
        """Update the plot with current data"""
        if self.plotter is None:
            return
        
        self.plotter.clear()
        
        if self.current_data is None:
            self.plotter.set_title("No data loaded")
            self.plotter.set_labels()
            self.plotter.get_canvas().draw()
            return
        
        # Only plot processed data if available, otherwise plot original
        # Don't show both original and processed at the same time
        if self.processed_data is not None:
            # Plot processed data only
            self.plotter.plot_spectrum(
                self.processed_data.two_theta,
                self.processed_data.intensity,
                label='Processed',
                color='red',
                show_negative=True,
                smooth=True,  # Enable smoothing
                linewidth=0.8  # Thinner lines
            )
        else:
            # Plot original data only when no processing has been done
            self.plotter.plot_spectrum(
                self.current_data.two_theta,
                self.current_data.intensity,
                label='Original',
                color='blue',
                show_negative=False,
                smooth=True,  # Enable smoothing
                linewidth=0.8  # Thinner lines
            )
        
        # Adjust y-axis limits to accommodate reference pattern if present
        # This must be done before plotting reference pattern
        if hasattr(self, 'current_ref_pattern') and self.current_ref_pattern:
            if self.plotter and self.plotter.axes:
                # Get current y-limits after data is plotted
                y_min, y_max = self.plotter.axes.get_ylim()
                y_range = y_max - y_min
                # Extend y-axis downward by 25% to create space for reference pattern
                new_y_min = y_min - y_range * 0.25
                self.plotter.axes.set_ylim(bottom=new_y_min)
        
        # Plot reference pattern if available (as vertical sticks)
        if hasattr(self, 'current_ref_pattern') and self.current_ref_pattern:
            tt_ref, int_ref, name = self.current_ref_pattern
            # Get updated y-axis limits after adjustment
            if self.plotter and self.plotter.axes:
                y_min, y_max = self.plotter.axes.get_ylim()
                y_range = y_max - y_min
                # Position reference pattern in the bottom 20% of the extended range
                # This creates clear visual separation from experimental data
                ref_offset = y_min + y_range * 0.05  # 5% from bottom
                ref_height = y_range * 0.15  # Use 15% of range for reference pattern height
            else:
                ref_offset = 0.0
                ref_height = None
            
            # Add a horizontal separator line for visual clarity (before plotting reference)
            if self.plotter and self.plotter.axes:
                # Separator at 12% from bottom (between data and reference)
                separator_y = y_min + y_range * 0.12
                self.plotter.axes.axhline(
                    y=separator_y,
                    color='#888888',  # Medium gray
                    linestyle='--',
                    linewidth=1.0,
                    alpha=0.6,
                    zorder=1,  # Behind other elements
                    label=''  # Don't add to legend
                )
            
            self.plotter.plot_reference_pattern(
                tt_ref, int_ref,
                label=f'Reference: {name}',
                color='#2E7D32',  # Dark green for publication
                linewidth=1.2,
                alpha=0.85,
                offset=ref_offset,
                max_height=ref_height
            )
        
        # Plot detected peaks
        # If reference pattern is active, only show matched peaks for better readability
        has_ref_pattern = hasattr(self, 'current_ref_pattern') and self.current_ref_pattern
        has_match_result = self.peak_match_result and self.peak_match_result.get('matched_peaks')
        
        if has_ref_pattern and has_match_result:
            # Only show matched peaks when reference pattern is displayed
            matched_tt = [mp[0].two_theta for mp in self.peak_match_result['matched_peaks']]
            matched_int = [mp[0].intensity for mp in self.peak_match_result['matched_peaks']]
            if len(matched_tt) > 0:
                self.plotter.plot_peaks(
                    np.array(matched_tt),
                    np.array(matched_int),
                    label=f'Matched Peaks ({len(matched_tt)})',
                    color='#7B1FA2',  # Purple for matched peaks
                    marker='*',
                    markersize=8,
                    show_values=True,
                    value_format='intensity'
                )
        elif len(self.detected_peaks) > 0:
            # Show all detected peaks when no reference pattern is active
            peak_tt = [p.two_theta for p in self.detected_peaks]
            peak_int = [p.intensity for p in self.detected_peaks]
            self.plotter.plot_peaks(
                np.array(peak_tt),
                np.array(peak_int),
                label=f'Detected Peaks ({len(self.detected_peaks)})',
                color='orange',
                marker='v',
                markersize=6,
                show_values=True,
                value_format='intensity'  # Show intensity values
            )
            
            # Highlight matched peaks if available (but no reference pattern shown)
            if has_match_result:
                matched_tt = [mp[0].two_theta for mp in self.peak_match_result['matched_peaks']]
                matched_int = [mp[0].intensity for mp in self.peak_match_result['matched_peaks']]
                if len(matched_tt) > 0:
                    self.plotter.plot_peaks(
                        np.array(matched_tt),
                        np.array(matched_int),
                        label=f'Matched Peaks ({len(matched_tt)})',
                        color='purple',
                        marker='*',
                        markersize=8
                    )
        
        self.plotter.set_labels()
        self.plotter.set_title("XRD Spectrum")
        self.plotter.finalize()
        self.plotter.get_canvas().draw()
    
    def load_reference_database(self):
        """Load default reference databases from multiple locations"""
        base_path = Path(__file__).parent.parent.parent / "data"
        
        # List of database directories to load
        db_paths = [
            base_path / "examples" / "reference_patterns",  # MP database
            base_path / "databases" / "json"  # ICDD database
        ]
        
        self.reference_db = ReferenceDatabase()
        
        # Load from all database locations
        for db_path in db_paths:
            if db_path.exists():
                try:
                    self.reference_db.load_database(str(db_path))
                except Exception as e:
                    print(f"Warning: Could not load database from {db_path}: {e}")
        
        # Update status and populate search combo
        pattern_count = len(self.reference_db)
        if pattern_count > 0:
            self.statusBar.showMessage(f"Loaded {pattern_count} reference patterns")
            
            # Populate search combo
            self.ref_search_combo.clear()
            for pattern in self.reference_db.get_all():
                display_name = pattern.name or pattern.id
                if pattern.data.get('source'):
                    display_name += f" ({pattern.data.get('source')})"
                self.ref_search_combo.addItem(display_name)
        else:
            self.statusBar.showMessage("No reference patterns loaded")
            self.reference_db = ReferenceDatabase()
    
    def load_reference_database_dialog(self):
        """Load reference database from dialog"""
        db_path = QFileDialog.getExistingDirectory(
            self,
            "Select Reference Database Directory",
            ""
        )
        
        if db_path:
            try:
                # Add the selected directory to existing database
                if self.reference_db is None:
                    self.reference_db = ReferenceDatabase()
                
                self.reference_db.load_database(db_path)
                pattern_count = len(self.reference_db)
                self.statusBar.showMessage(f"Loaded {pattern_count} reference patterns")
                
                # Repopulate search combo with all patterns
                self.ref_search_combo.clear()
                for pattern in self.reference_db.get_all():
                    display_name = pattern.name or pattern.id
                    if pattern.data.get('source'):
                        display_name += f" ({pattern.data.get('source')})"
                    self.ref_search_combo.addItem(display_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load database:\n{str(e)}")
    
    def view_projects(self):
        """View all projects"""
        projects = self.project_manager.list_projects()
        
        if not projects:
            QMessageBox.information(self, "Projects", "No projects found.")
            return
        
        # Create a simple dialog showing projects
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Projects")
        dialog.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for project in projects:
            item_text = f"{project['name']}\n"
            item_text += f"  Source: {project['source_file']}\n"
            item_text += f"  Created: {project['created_at']}\n"
            item_text += f"  Steps: {project['analysis_steps']}"
            list_widget.addItem(item_text)
        
        layout.addWidget(list_widget)
        
        open_btn = QPushButton("Open Selected Project")
        open_btn.clicked.connect(lambda: self.open_project_from_list(list_widget, projects, dialog))
        layout.addWidget(open_btn)
        
        dialog.exec()
    
    def open_project_from_list(self, list_widget, projects, dialog):
        """Open project from list selection"""
        current_row = list_widget.currentRow()
        if current_row >= 0:
            project = projects[current_row]
            self.open_project_path(project['path'])
            dialog.accept()
    
    def open_project(self):
        """Open project dialog"""
        project_path = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(self.project_manager.projects_root)
        )
        
        if project_path:
            self.open_project_path(project_path)
    
    def open_project_path(self, project_path: str):
        """Open a project from path"""
        try:
            project_info = self.project_manager.load_project(project_path)
            
            # Load original data
            data_path = Path(project_path) / "original_data" / "raw_data.json"
            if data_path.exists():
                with open(data_path, 'r') as f:
                    data = json.load(f)
                
                self.current_data = XRDData(
                    np.array(data['two_theta']),
                    np.array(data['intensity']),
                    data.get('wavelength'),
                    data.get('metadata', {})
                )
                
                self.current_file_path = project_info.get('source_file_path', '')
                self.file_label.setText(f"Project: {project_info.get('source_file', 'Unknown')}")
                
                # Try to load latest processed data
                processed_dir = Path(project_path) / "processed_data"
                if processed_dir.exists():
                    processed_files = sorted(processed_dir.glob("*.json"), reverse=True)
                    if processed_files:
                        with open(processed_files[0], 'r') as f:
                            proc_data = json.load(f)
                        self.processed_data = XRDData(
                            np.array(proc_data['two_theta']),
                            np.array(proc_data['intensity']),
                            self.current_data.wavelength,
                            self.current_data.metadata
                        )
                
                self.update_plot()
                self.statusBar.showMessage(f"Opened project: {Path(project_path).name}")
            else:
                QMessageBox.warning(self, "Warning", "Project data not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About XRD Scorer",
            "XRD Scorer v1.0.0\n\n"
            "Desktop application for X-ray Diffraction data analysis.\n\n"
            "Features:\n"
            "- Multi-format file support (XRDML, DAT, ASC, TXT, RAW)\n"
            "- Background subtraction\n"
            "- K-alpha stripping\n"
            "- Reference pattern matching\n"
            "- Interactive visualization\n"
            "- Project-based data management"
        )


def main():
    """Main entry point"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

