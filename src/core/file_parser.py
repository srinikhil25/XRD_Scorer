"""
XRD File Parser Module
Supports multiple file formats: XRDML, DAT, ASC, TXT
"""

import numpy as np
import re
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import xml.etree.ElementTree as ET


class XRDData:
    """Container for XRD data"""
    
    def __init__(self, two_theta: np.ndarray, intensity: np.ndarray, 
                 wavelength: Optional[float] = None, metadata: Optional[Dict] = None):
        self.two_theta = np.array(two_theta)
        self.intensity = np.array(intensity)
        self.wavelength = wavelength  # in Angstroms
        self.metadata = metadata or {}
        
    def __len__(self):
        return len(self.two_theta)
    
    def get_d_spacing(self) -> np.ndarray:
        """Calculate d-spacing from two-theta and wavelength"""
        if self.wavelength is None:
            raise ValueError("Wavelength not set. Cannot calculate d-spacing.")
        # Bragg's law: n*lambda = 2*d*sin(theta)
        # d = lambda / (2*sin(theta))
        theta_rad = np.deg2rad(self.two_theta / 2)
        return self.wavelength / (2 * np.sin(theta_rad))


class XRDMLParser:
    """Parser for XRDML files (Bruker/PANalytical format)"""
    
    @staticmethod
    def parse(file_path: str) -> XRDData:
        """Parse XRDML file"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract namespace
        ns = {'xrdml': 'http://www.xrdml.com/XRDMeasurement/1.5'}
        
        # Find wavelength
        wavelength = None
        wavelength_elem = root.find('.//xrdml:usedWavelength/xrdml:kAlpha1', ns)
        if wavelength_elem is not None:
            wavelength = float(wavelength_elem.text)
        
        # Find intensity data
        intensities = []
        two_thetas = []
        
        # Try to find data in different possible locations
        scan_points = root.findall('.//xrdml:scan/xrdml:dataPoints/xrdml:positions/xrdml:listPositions', ns)
        intensity_points = root.findall('.//xrdml:scan/xrdml:dataPoints/xrdml:counts', ns)
        
        if scan_points and intensity_points:
            # Extract positions (two-theta values)
            for positions in scan_points:
                pos_text = positions.text
                if pos_text:
                    two_thetas.extend([float(x) for x in pos_text.split()])
            
            # Extract intensities
            for counts in intensity_points:
                count_text = counts.text
                if count_text:
                    intensities.extend([float(x) for x in count_text.split()])
        
        # Alternative: look for data in xrdml:positions and xrdml:counts directly
        if not two_thetas:
            positions = root.findall('.//xrdml:positions/xrdml:listPositions', ns)
            counts = root.findall('.//xrdml:counts', ns)
            
            if positions and counts:
                for pos in positions:
                    if pos.text:
                        two_thetas.extend([float(x) for x in pos.text.split()])
                for count in counts:
                    if count.text:
                        intensities.extend([float(x) for x in count.text.split()])
        
        if not two_thetas or not intensities:
            raise ValueError("Could not extract data from XRDML file")
        
        # Ensure arrays are same length
        min_len = min(len(two_thetas), len(intensities))
        two_thetas = np.array(two_thetas[:min_len])
        intensities = np.array(intensities[:min_len])
        
        metadata = {
            'file_type': 'XRDML',
            'file_path': file_path
        }
        
        return XRDData(two_thetas, intensities, wavelength, metadata)


class DATParser:
    """Parser for DAT files (common text format)"""
    
    @staticmethod
    def parse(file_path: str) -> XRDData:
        """Parse DAT file"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Try to parse as space/tab separated values
                parts = re.split(r'[\s\t,]+', line)
                if len(parts) >= 2:
                    try:
                        two_theta = float(parts[0])
                        intensity = float(parts[1])
                        data.append((two_theta, intensity))
                    except ValueError:
                        continue
        
        if not data:
            raise ValueError("No valid data found in DAT file")
        
        two_thetas, intensities = zip(*data)
        
        metadata = {
            'file_type': 'DAT',
            'file_path': file_path
        }
        
        return XRDData(np.array(two_thetas), np.array(intensities), None, metadata)


class ASCParser:
    """Parser for ASC files (ASCII format, often from PANalytical)"""
    
    @staticmethod
    def parse(file_path: str) -> XRDData:
        """Parse ASC file"""
        two_thetas = []
        intensities = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # ASC files typically have: 2theta, intensity
                parts = re.split(r'[\s\t,;]+', line)
                if len(parts) >= 2:
                    try:
                        two_theta = float(parts[0])
                        intensity = float(parts[1])
                        two_thetas.append(two_theta)
                        intensities.append(intensity)
                    except ValueError:
                        continue
        
        if not two_thetas:
            raise ValueError("No valid data found in ASC file")
        
        metadata = {
            'file_type': 'ASC',
            'file_path': file_path
        }
        
        return XRDData(np.array(two_thetas), np.array(intensities), None, metadata)


class TXTParser:
    """Parser for TXT files (generic text format)"""
    
    @staticmethod
    def parse(file_path: str) -> XRDData:
        """Parse TXT file - tries multiple formats"""
        two_thetas = []
        intensities = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Try to detect header
        start_idx = 0
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if re.match(r'^\s*[\d\.]+\s+[\d\.]', line):
                start_idx = i
                break
        
        for line in lines[start_idx:]:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try various separators
            parts = re.split(r'[\s\t,;|]+', line)
            if len(parts) >= 2:
                try:
                    two_theta = float(parts[0])
                    intensity = float(parts[1])
                    two_thetas.append(two_theta)
                    intensities.append(intensity)
                except ValueError:
                    continue
        
        if not two_thetas:
            raise ValueError("No valid data found in TXT file")
        
        metadata = {
            'file_type': 'TXT',
            'file_path': file_path
        }
        
        return XRDData(np.array(two_thetas), np.array(intensities), None, metadata)


def parse_xrd_file(file_path: str) -> XRDData:
    """
    Universal parser that detects file format and parses accordingly
    
    Args:
        file_path: Path to XRD data file
        
    Returns:
        XRDData object containing two_theta and intensity arrays
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.xrdml':
        return XRDMLParser.parse(file_path)
    elif suffix == '.dat':
        return DATParser.parse(file_path)
    elif suffix == '.asc':
        return ASCParser.parse(file_path)
    elif suffix == '.txt':
        return TXTParser.parse(file_path)
    else:
        # Try to detect format from content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            if 'xrdml' in first_line.lower() or '<?xml' in first_line:
                return XRDMLParser.parse(file_path)
            else:
                # Default to TXT parser
                return TXTParser.parse(file_path)

