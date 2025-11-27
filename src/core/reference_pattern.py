"""
Reference Pattern Database Loader

Loads and processes reference patterns from ICDD and Materials Project (MP) databases
in JSON format.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class ReferencePattern:
    """Container for a reference XRD pattern"""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.id = data.get('id', '')
        self.name = data.get('name', '')
        # If both id and name are empty, try to use id as fallback
        if not self.name and self.id:
            self.name = self.id
        elif not self.id and self.name:
            self.id = self.name
        self.wavelength = self._extract_wavelength(data)
        self.two_theta = None
        self.intensity = None
        self.d_spacing = None
        self.hkl = None
        
        self._parse_pattern()
    
    def _extract_wavelength(self, data: Dict) -> Optional[float]:
        """Extract wavelength from data"""
        # MP format
        if 'wavelength' in data:
            wl_data = data['wavelength']
            if isinstance(wl_data, dict):
                return wl_data.get('in_angstroms')
            return wl_data
        
        # Default to Cu Kα1
        return 1.54056
    
    def _parse_pattern(self):
        """Parse pattern data from different formats"""
        # MP format: has 'pattern' array with [amplitude, hkl, two_theta, d_spacing]
        if 'pattern' in self.data:
            pattern = self.data['pattern']
            if pattern and len(pattern) > 0:
                amplitudes = []
                two_thetas = []
                d_spacings = []
                hkl_list = []
                
                for peak in pattern:
                    if len(peak) >= 4:
                        amplitudes.append(peak[0])
                        hkl_list.append(peak[1])
                        two_thetas.append(peak[2])
                        d_spacings.append(peak[3])
                
                self.intensity = np.array(amplitudes)
                self.two_theta = np.array(two_thetas)
                self.d_spacing = np.array(d_spacings)
                self.hkl = hkl_list
                
                # Normalize intensity to 0-100
                if len(self.intensity) > 0:
                    max_int = np.max(self.intensity)
                    if max_int > 0:
                        self.intensity = (self.intensity / max_int) * 100
        
        # Simple format: has 'peaks' array (ICDD format or similar)
        elif 'peaks' in self.data:
            peaks = self.data['peaks']
            d_spacings = []
            two_thetas = []
            intensities = []
            hkl_list = []
            
            for peak in peaks:
                if isinstance(peak, dict):
                    d_spacing = peak.get('d_spacing', 0)
                    two_theta = peak.get('two_theta', None)
                    intensity = peak.get('intensity', 0)
                    hkl = peak.get('hkl', '')
                    
                    d_spacings.append(d_spacing)
                    intensities.append(intensity)
                    hkl_list.append(hkl)
                    
                    # Use two_theta if provided, otherwise calculate from d_spacing
                    if two_theta is not None:
                        two_thetas.append(two_theta)
                    elif d_spacing > 0 and self.wavelength:
                        # Calculate from d-spacing using Bragg's law
                        two_theta_calc = 2 * np.rad2deg(np.arcsin(self.wavelength / (2 * d_spacing)))
                        two_thetas.append(two_theta_calc)
                    else:
                        two_thetas.append(0)
            
            self.d_spacing = np.array(d_spacings)
            self.intensity = np.array(intensities)
            self.hkl = hkl_list
            
            if len(two_thetas) > 0:
                self.two_theta = np.array(two_thetas)
            elif self.wavelength and len(self.d_spacing) > 0:
                # Fallback: Convert d-spacing to two-theta if not provided
                # Bragg's law: n*lambda = 2*d*sin(theta)
                # 2*theta = 2*arcsin(lambda/(2*d))
                self.two_theta = 2 * np.rad2deg(np.arcsin(self.wavelength / (2 * self.d_spacing)))
    
    def get_continuous_pattern(self, two_theta_range: Tuple[float, float], 
                              num_points: int = 1000, 
                              peak_width: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate continuous pattern from discrete peaks using Gaussian profiles
        
        Args:
            two_theta_range: (min, max) two-theta range
            num_points: Number of points in output
            peak_width: Width of Gaussian peaks (in degrees)
            
        Returns:
            Tuple of (two_theta, intensity)
        """
        if self.two_theta is None or self.intensity is None:
            raise ValueError("Pattern data not available")
        
        two_theta_out = np.linspace(two_theta_range[0], two_theta_range[1], num_points)
        intensity_out = np.zeros(num_points)
        
        for i, (tt, inten) in enumerate(zip(self.two_theta, self.intensity)):
            # Gaussian profile
            gaussian = inten * np.exp(-0.5 * ((two_theta_out - tt) / peak_width) ** 2)
            intensity_out += gaussian
        
        return two_theta_out, intensity_out


class ReferenceDatabase:
    """Manager for reference pattern database"""
    
    def __init__(self, database_path: Optional[str] = None):
        self.patterns: List[ReferencePattern] = []
        self.database_path = database_path
        
        if database_path:
            self.load_database(database_path)
    
    def load_database(self, database_path: str):
        """Load reference patterns from directory or file"""
        path = Path(database_path)
        
        if path.is_file():
            # Single file
            self._load_file(path)
        elif path.is_dir():
            # Directory - load all JSON files recursively
            for json_file in path.rglob('*.json'):
                try:
                    self._load_file(json_file)
                except Exception as e:
                    print(f"Warning: Could not load {json_file}: {e}")
    
    def load_multiple_databases(self, database_paths: List[str]):
        """Load reference patterns from multiple directories"""
        for db_path in database_paths:
            self.load_database(db_path)
    
    def _load_file(self, file_path: Path):
        """Load a single JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract filename for MP files that don't have id/name
        filename = file_path.stem  # filename without extension
        
        # Handle both single pattern and array of patterns
        if isinstance(data, list):
            for pattern_data in data:
                # For MP files, extract ID from filename if not present
                if 'pattern' in pattern_data and not pattern_data.get('id') and not pattern_data.get('name'):
                    # MP format: filename like "mp-3271_xrd_Cu" -> extract "mp-3271" or "3271"
                    if filename.startswith('mp-'):
                        mp_id = filename.split('_')[0]  # Get "mp-3271"
                        pattern_data['id'] = mp_id
                        pattern_data['name'] = mp_id  # Use ID as name if no name available
                        pattern_data['source'] = 'MP'
                pattern = ReferencePattern(pattern_data)
                self.patterns.append(pattern)
        else:
            # For MP files, extract ID from filename if not present
            if 'pattern' in data and not data.get('id') and not data.get('name'):
                # MP format: filename like "mp-3271_xrd_Cu" -> extract "mp-3271" or "3271"
                if filename.startswith('mp-'):
                    mp_id = filename.split('_')[0]  # Get "mp-3271"
                    data['id'] = mp_id
                    data['name'] = mp_id  # Use ID as name if no name available
                    data['source'] = 'MP'
            pattern = ReferencePattern(data)
            self.patterns.append(pattern)
    
    def add_pattern(self, pattern: ReferencePattern):
        """Add a pattern to the database"""
        self.patterns.append(pattern)
    
    def search(self, query: str) -> List[ReferencePattern]:
        """Search patterns by name or ID"""
        query_lower = query.lower().strip()
        results = []
        
        for pattern in self.patterns:
            pattern_name = (pattern.name or "").lower()
            pattern_id = (pattern.id or "").lower()
            
            # Check if query matches name, id, or is contained in either
            if (query_lower in pattern_name or 
                query_lower in pattern_id or
                pattern_name.startswith(query_lower) or
                pattern_id.startswith(query_lower)):
                results.append(pattern)
        
        return results
    
    def get_all(self) -> List[ReferencePattern]:
        """Get all patterns"""
        return self.patterns
    
    def __len__(self):
        return len(self.patterns)

