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


class RAWParser:
    """Parser for RAW files (binary format, often from Rigaku/PANalytical)
    
    RAW files typically have:
    - A header section with metadata (start angle, end angle, step size, data count)
    - A data section with intensity values as float32 (little-endian)
    
    This parser uses multiple detection methods to handle different RAW file formats.
    """
    
    @staticmethod
    def parse(file_path: str) -> XRDData:
        """Parse RAW file using multiple detection strategies"""
        import struct
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        file_size = len(data)
        data_count = None
        data_offset = None
        start_angle = None
        end_angle = None
        step = None
        
        # Method 1: Look for data count that matches file structure
        # Common pattern: count (4 bytes) followed by data (count * 4 bytes) = file_size
        for offset in range(0, min(10000, file_size - 4), 4):
            try:
                count = struct.unpack_from('<I', data, offset)[0]
                expected_data_size = count * 4
                # Check if count + data fits exactly in file
                if 100 <= count <= 100000:
                    # Pattern 1: count at offset, data immediately after
                    if offset + 4 + expected_data_size == file_size:
                        data_count = count
                        data_offset = offset + 4
                        break
                    # Pattern 2: header + count + data
                    # Try if there's a reasonable header before count
                    if offset >= 100 and offset + 4 + expected_data_size <= file_size:
                        # Verify the data section looks valid (not all zeros, reasonable range)
                        test_data = np.frombuffer(
                            data[offset + 4:offset + 4 + min(100 * 4, expected_data_size)],
                            dtype='<f4'
                        )
                        if len(test_data) > 0:
                            # Check if values are reasonable (not all zeros, not NaN/Inf)
                            if (np.any(test_data > 0) and 
                                np.all(np.isfinite(test_data)) and 
                                np.all(test_data < 1e10)):
                                # This looks like valid data
                                data_count = count
                                data_offset = offset + 4
                                break
            except:
                continue
        
        # Method 2: Search for start/end/step values in header, then find matching count
        if data_count is None:
            found_start = None
            found_end = None
            found_step = None
            
            # Search for reasonable angle values in header
            for offset in range(0, min(10000, file_size - 4), 4):
                try:
                    val = struct.unpack_from('<f', data, offset)[0]
                    # Start angle typically 4-10 degrees
                    if found_start is None and 4.0 <= val <= 10.0:
                        found_start = (offset, val)
                    # End angle typically 80-100 degrees
                    if found_end is None and 80.0 <= val <= 100.0:
                        found_end = (offset, val)
                    # Step size typically 0.01-0.1 degrees
                    if found_step is None and 0.01 <= val <= 0.1:
                        found_step = (offset, val)
                except:
                    continue
            
            # If we found start, end, and step, calculate expected count
            if found_start and found_end and found_step:
                start_angle = found_start[1]
                end_angle = found_end[1]
                step = found_step[1]
                data_count = int((end_angle - start_angle) / step) + 1
                
                # Try to find where data starts (after header)
                # Common header sizes: 512, 1024, 2048, 3238, 4096 bytes
                for header_size in [3238, 2048, 4096, 1024, 512, 256, 128]:
                    if header_size + data_count * 4 <= file_size:
                        # Verify this location has valid data
                        test_data = np.frombuffer(
                            data[header_size:header_size + min(100 * 4, data_count * 4)],
                            dtype='<f4'
                        )
                        if len(test_data) > 0:
                            if (np.any(test_data > 0) and 
                                np.all(np.isfinite(test_data)) and 
                                np.all(test_data < 1e10)):
                                data_offset = header_size
                                break
        
        # Method 3: Assume data is at the end (last N float32 values)
        if data_count is None or data_offset is None:
            # Try to find count value near the end of header
            remaining = file_size % 4
            if remaining > 0:
                # Header has remainder, count might be at remainder position
                header_size = remaining
                if header_size + 4 <= file_size:
                    try:
                        count = struct.unpack_from('<I', data, header_size)[0]
                        if 100 <= count <= 100000:
                            expected_end = header_size + 4 + count * 4
                            if expected_end == file_size:
                                data_count = count
                                data_offset = header_size + 4
                    except:
                        pass
            
            # If still not found, try to find count by checking file structure
            if data_count is None:
                # Assume data is last N float32 values, where N is reasonable
                # Try different header sizes
                for header_size in [3238, 2048, 4096, 1024, 512, 256]:
                    potential_count = (file_size - header_size) // 4
                    if 100 <= potential_count <= 100000:
                        # Verify data looks valid
                        test_data = np.frombuffer(
                            data[header_size:header_size + min(100 * 4, potential_count * 4)],
                            dtype='<f4'
                        )
                        if len(test_data) > 0:
                            if (np.any(test_data > 0) and 
                                np.all(np.isfinite(test_data)) and 
                                np.all(test_data < 1e10)):
                                data_count = potential_count
                                data_offset = header_size
                                break
        
        # Method 4: Final fallback - use file size to estimate
        if data_count is None:
            # Assume reasonable header size and calculate data count
            estimated_header = min(4096, file_size // 4)  # Max 4KB header
            data_count = (file_size - estimated_header) // 4
            data_offset = estimated_header
            if data_count < 100:
                raise ValueError("RAW file too small or invalid structure")
        
        # Set defaults for angles if not found
        if start_angle is None:
            start_angle = 5.0
        if step is None:
            step = 0.02
        # Don't set default end_angle here - calculate it from data_count
        
        # Read intensity data
        if data_offset + data_count * 4 > file_size:
            raise ValueError(f"Invalid data structure: offset={data_offset}, count={data_count}, file_size={file_size}")
        
        intensities = np.frombuffer(
            data[data_offset:data_offset + data_count * 4],
            dtype='<f4'
        )
        
        # Don't filter values - keep all data as-is (negative values are valid after processing)
        # Only filter obviously corrupted data (NaN, Inf, or extremely large values)
        valid_mask = np.isfinite(intensities) & (intensities < 1e10)
        if np.any(valid_mask):
            if not np.all(valid_mask):
                # Some invalid values, but keep valid ones
                intensities = intensities[valid_mask]
                data_count = len(intensities)
        
        # Generate two-theta values using the actual start/end/step from header
        if data_count > 0:
            # Validate and calculate two-theta range
            # Priority: Always calculate from actual data count, validate header values
            if start_angle and step:
                # Calculate end angle from data count and step (most reliable)
                calculated_end = start_angle + (data_count - 1) * step
                
                # If we have an end_angle from header, validate it
                if end_angle:
                    # Calculate expected count from header values
                    expected_count = int((end_angle - start_angle) / step) + 1
                    
                    # Only use header end_angle if ALL conditions are met:
                    # 1. Expected count matches actual count (within 1)
                    # 2. End angle is reasonable (5-120 degrees typical for XRD)
                    # 3. Calculated end from data count is close to header end (within 5 degrees)
                    if (abs(expected_count - data_count) <= 1 and 
                        5.0 <= end_angle <= 120.0 and
                        abs(calculated_end - end_angle) < 5.0):
                        # Header values are valid, use them
                        two_thetas = np.linspace(start_angle, end_angle, data_count)
                        end_angle = end_angle  # Use header value
                    else:
                        # Header end_angle is wrong or unreasonable, use calculated
                        # But also check if calculated_end is reasonable
                        if calculated_end > 120.0:
                            # Calculated end is too large, likely step is wrong
                            # Try to infer correct step from common XRD ranges
                            # Most XRD scans are 5-90 degrees
                            if start_angle >= 4.0 and start_angle <= 6.0:
                                # Assume standard 5-90 degree range
                                inferred_end = 90.0
                                inferred_step = (inferred_end - start_angle) / (data_count - 1)
                                if 0.005 <= inferred_step <= 0.1:
                                    # Inferred step is reasonable, use it
                                    step = inferred_step
                                    end_angle = inferred_end
                                    two_thetas = np.linspace(start_angle, end_angle, data_count)
                                else:
                                    # Use calculated but cap at reasonable max
                                    end_angle = min(calculated_end, 120.0)
                                    two_thetas = np.linspace(start_angle, end_angle, data_count)
                            else:
                                # Use calculated but cap at reasonable max
                                end_angle = min(calculated_end, 120.0)
                                two_thetas = np.linspace(start_angle, end_angle, data_count)
                        else:
                            # Calculated end is reasonable, use it
                            end_angle = calculated_end
                            two_thetas = np.linspace(start_angle, end_angle, data_count)
                else:
                    # No end_angle from header, calculate from step
                    calculated_end = start_angle + (data_count - 1) * step
                    # Cap at reasonable maximum
                    if calculated_end > 120.0 and start_angle >= 4.0 and start_angle <= 6.0:
                        # Likely should be 5-90 range, recalculate step
                        inferred_end = 90.0
                        inferred_step = (inferred_end - start_angle) / (data_count - 1)
                        if 0.005 <= inferred_step <= 0.1:
                            step = inferred_step
                            end_angle = inferred_end
                            two_thetas = np.linspace(start_angle, end_angle, data_count)
                        else:
                            end_angle = min(calculated_end, 120.0)
                            two_thetas = np.linspace(start_angle, end_angle, data_count)
                    else:
                        end_angle = min(calculated_end, 120.0)
                        two_thetas = np.linspace(start_angle, end_angle, data_count)
            else:
                # Fallback: use defaults
                if start_angle is None:
                    start_angle = 5.0
                if step is None:
                    step = 0.02
                calculated_end = start_angle + (data_count - 1) * step
                end_angle = min(calculated_end, 90.0)  # Cap at 90 for default
                two_thetas = np.linspace(start_angle, end_angle, data_count)
        else:
            raise ValueError("No valid data found in RAW file")
        
        metadata = {
            'file_type': 'RAW',
            'file_path': file_path,
            'data_count': data_count,
            'start_angle': float(start_angle),
            'end_angle': float(end_angle),
            'step': float(step)
        }
        
        return XRDData(two_thetas, intensities, None, metadata)


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
    elif suffix == '.raw':
        return RAWParser.parse(file_path)
    else:
        # Try to detect format from content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if 'xrdml' in first_line.lower() or '<?xml' in first_line:
                    return XRDMLParser.parse(file_path)
                else:
                    # Default to TXT parser
                    return TXTParser.parse(file_path)
        except (UnicodeDecodeError, IsADirectoryError):
            # Binary file - try RAW parser
            if suffix == '' or path.name.lower().endswith('.raw'):
                return RAWParser.parse(file_path)
            raise ValueError(f"Unknown file format: {file_path}")

