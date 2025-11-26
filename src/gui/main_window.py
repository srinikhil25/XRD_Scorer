"""
Main Window for XRD Scorer Application

Provides the main user interface with file loading, processing, and visualization
"""

import sys
import numpy as np
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QLabel, QComboBox,
                             QSpinBox, QDoubleSpinBox, QGroupBox, QMessageBox,
                             QSplitter, QStatusBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

from ..core.file_parser import parse_xrd_file, XRDData
from ..core.background_subtraction import subtract_background
from ..core.kalpha_stripping import strip_kalpha
from ..core.reference_pattern import ReferenceDatabase, ReferencePattern
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
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel: Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Visualization
        right_panel = self.create_visualization_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        splitter.setSizes([300, 1100])
        
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
        layout.addWidget(self.plotter.get_canvas())
        
        return panel
    
    def open_file(self):
        """Open XRD file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open XRD File",
            "",
            "XRD Files (*.xrdml *.dat *.asc *.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                self.current_data = parse_xrd_file(file_path)
                self.processed_data = None
                self.file_label.setText(f"Loaded: {Path(file_path).name}")
                self.statusBar.showMessage(f"Loaded file: {Path(file_path).name}")
                self.update_plot()
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
            
            self.statusBar.showMessage(f"Background subtracted using {method}")
            self.update_plot()
            
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
            
            self.statusBar.showMessage(f"K-alpha stripping applied using {method}")
            self.update_plot()
            
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
        
        patterns = self.reference_db.search(search_text)
        if not patterns:
            QMessageBox.warning(self, "Warning", f"No patterns found matching: {search_text}")
            return
        
        # Use first match
        pattern = patterns[0]
        
        # Get two-theta range from current data
        tt_min = np.min(self.current_data.two_theta)
        tt_max = np.max(self.current_data.two_theta)
        
        # Generate continuous pattern
        tt_ref, int_ref = pattern.get_continuous_pattern((tt_min, tt_max))
        
        # Normalize to match current data scale
        if len(int_ref) > 0:
            max_current = np.max(self.current_data.intensity)
            max_ref = np.max(int_ref)
            if max_ref > 0:
                int_ref = (int_ref / max_ref) * max_current * 0.5  # Scale to 50% of max
        
        # Store for plotting
        self.current_ref_pattern = (tt_ref, int_ref, pattern.name)
        
        self.statusBar.showMessage(f"Overlaying reference: {pattern.name}")
        self.update_plot()
    
    def reset_data(self):
        """Reset to original data"""
        self.processed_data = None
        self.current_ref_pattern = None
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
        
        # Plot original data
        self.plotter.plot_spectrum(
            self.current_data.two_theta,
            self.current_data.intensity,
            label='Original',
            color='blue',
            show_negative=False
        )
        
        # Plot processed data if available
        if self.processed_data is not None:
            self.plotter.plot_spectrum(
                self.processed_data.two_theta,
                self.processed_data.intensity,
                label='Processed',
                color='red',
                show_negative=True
            )
        
        # Plot reference pattern if available
        if hasattr(self, 'current_ref_pattern') and self.current_ref_pattern:
            tt_ref, int_ref, name = self.current_ref_pattern
            self.plotter.plot_reference_pattern(
                tt_ref, int_ref,
                label=f'Reference: {name}',
                color='green'
            )
        
        self.plotter.set_labels()
        self.plotter.set_title("XRD Spectrum")
        self.plotter.finalize()
        self.plotter.get_canvas().draw()
    
    def load_reference_database(self):
        """Load default reference database"""
        db_path = Path(__file__).parent.parent.parent / "data" / "examples" / "reference_patterns"
        if db_path.exists():
            try:
                self.reference_db = ReferenceDatabase(str(db_path))
                self.statusBar.showMessage(f"Loaded {len(self.reference_db)} reference patterns")
                
                # Populate search combo
                self.ref_search_combo.clear()
                for pattern in self.reference_db.get_all():
                    self.ref_search_combo.addItem(pattern.name or pattern.id)
            except Exception as e:
                print(f"Warning: Could not load reference database: {e}")
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
                self.reference_db = ReferenceDatabase(db_path)
                self.statusBar.showMessage(f"Loaded {len(self.reference_db)} reference patterns")
                
                # Populate search combo
                self.ref_search_combo.clear()
                for pattern in self.reference_db.get_all():
                    self.ref_search_combo.addItem(pattern.name or pattern.id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load database:\n{str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About XRD Scorer",
            "XRD Scorer v1.0.0\n\n"
            "Desktop application for X-ray Diffraction data analysis.\n\n"
            "Features:\n"
            "- Multi-format file support (XRDML, DAT, ASC, TXT)\n"
            "- Background subtraction\n"
            "- K-alpha stripping\n"
            "- Reference pattern matching\n"
            "- Interactive visualization"
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

