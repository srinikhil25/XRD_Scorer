"""
Tests for file parsers
"""

import numpy as np
import pytest
import tempfile
import os
from pathlib import Path
from src.core.file_parser import (
    XRDData,
    DATParser,
    ASCParser,
    TXTParser,
    parse_xrd_file
)


def create_test_dat_file(content):
    """Helper function to create a temporary DAT file"""
    fd, path = tempfile.mkstemp(suffix='.dat')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return path
    except:
        os.close(fd)
        os.unlink(path)
        raise


def test_dat_parser_basic():
    """Test that DAT parser doesn't crash on a valid .dat file"""
    # Create a simple valid DAT file
    content = """# Test data
20.0    100.0
30.0    200.0
40.0    300.0
50.0    250.0
60.0    150.0
"""
    file_path = create_test_dat_file(content)
    
    try:
        data = DATParser.parse(file_path)
        
        assert isinstance(data, XRDData)
        assert len(data.two_theta) > 0
        assert len(data.intensity) > 0
        assert len(data.two_theta) == len(data.intensity)
        assert data.metadata['file_type'] == 'DAT'
    finally:
        os.unlink(file_path)


def test_dat_parser_with_comments():
    """Test DAT parser with comments and headers"""
    content = """# Header line
# Another comment
20.0    100.0
30.0    200.0
# Inline comment
40.0    300.0
"""
    file_path = create_test_dat_file(content)
    
    try:
        data = DATParser.parse(file_path)
        assert len(data.two_theta) == 3
        assert np.allclose(data.two_theta, [20.0, 30.0, 40.0])
    finally:
        os.unlink(file_path)


def test_dat_parser_tab_separated():
    """Test DAT parser with tab-separated values"""
    content = """20.0\t100.0
30.0\t200.0
40.0\t300.0
"""
    file_path = create_test_dat_file(content)
    
    try:
        data = DATParser.parse(file_path)
        assert len(data.two_theta) == 3
    finally:
        os.unlink(file_path)


def test_dat_parser_comma_separated():
    """Test DAT parser with comma-separated values"""
    content = """20.0,100.0
30.0,200.0
40.0,300.0
"""
    file_path = create_test_dat_file(content)
    
    try:
        data = DATParser.parse(file_path)
        assert len(data.two_theta) == 3
    finally:
        os.unlink(file_path)


def test_dat_parser_empty_file():
    """Test DAT parser with empty file"""
    content = """# Only comments
# No data
"""
    file_path = create_test_dat_file(content)
    
    try:
        with pytest.raises(ValueError, match="No valid data"):
            DATParser.parse(file_path)
    finally:
        os.unlink(file_path)


def test_asc_parser_basic():
    """Test ASC parser with valid data"""
    content = """20.0    100.0
30.0    200.0
40.0    300.0
"""
    fd, path = tempfile.mkstemp(suffix='.asc')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        data = ASCParser.parse(path)
        assert len(data.two_theta) == 3
        assert data.metadata['file_type'] == 'ASC'
    finally:
        os.unlink(path)


def test_txt_parser_basic():
    """Test TXT parser with valid data"""
    content = """20.0    100.0
30.0    200.0
40.0    300.0
"""
    fd, path = tempfile.mkstemp(suffix='.txt')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        data = TXTParser.parse(path)
        assert len(data.two_theta) == 3
        assert data.metadata['file_type'] == 'TXT'
    finally:
        os.unlink(path)


def test_parse_xrd_file_dat():
    """Test parse_xrd_file with DAT file"""
    content = """20.0    100.0
30.0    200.0
40.0    300.0
"""
    file_path = create_test_dat_file(content)
    
    try:
        data = parse_xrd_file(file_path)
        assert isinstance(data, XRDData)
        assert len(data.two_theta) == 3
    finally:
        os.unlink(file_path)


def test_xrd_data_get_d_spacing():
    """Test XRDData.get_d_spacing method"""
    two_theta = np.array([20.0, 40.0, 60.0])
    intensity = np.array([100, 200, 300])
    wavelength = 1.54056
    
    data = XRDData(two_theta, intensity, wavelength=wavelength)
    d_spacing = data.get_d_spacing()
    
    assert len(d_spacing) == len(two_theta)
    assert np.all(d_spacing > 0)
    assert np.all(np.isfinite(d_spacing))


def test_xrd_data_metadata():
    """Test that XRDData stores metadata correctly"""
    two_theta = np.array([20.0, 30.0])
    intensity = np.array([100, 200])
    metadata = {'test_key': 'test_value'}
    
    data = XRDData(two_theta, intensity, metadata=metadata)
    
    assert data.metadata['test_key'] == 'test_value'


def test_dat_parser_large_file():
    """Test DAT parser with larger file"""
    # Generate test data
    two_theta = np.linspace(10, 80, 1000)
    intensity = np.random.rand(1000) * 1000
    
    content = '\n'.join([f'{tt:.2f}    {inten:.2f}' 
                        for tt, inten in zip(two_theta, intensity)])
    
    file_path = create_test_dat_file(content)
    
    try:
        data = DATParser.parse(file_path)
        assert len(data.two_theta) == 1000
        assert len(data.intensity) == 1000
    finally:
        os.unlink(file_path)

