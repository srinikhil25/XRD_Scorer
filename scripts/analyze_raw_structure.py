"""Analyze RAW file structure to find correct data location"""
import struct
import numpy as np
from pathlib import Path

raw_file = Path('input_data/20250520/Ti2AlC3.raw')
data = raw_file.read_bytes()
file_size = len(data)

print(f"File size: {file_size} bytes")
print(f"\nKnown values:")
print(f"  Count at 3234: {struct.unpack_from('<I', data, 3234)[0]}")
print(f"  Start at 3010: {struct.unpack_from('<f', data, 3010)[0]:.2f}")
print(f"  End at 3014: {struct.unpack_from('<f', data, 3014)[0]:.2f}")
print(f"  Step at 3018: {struct.unpack_from('<f', data, 3018)[0]:.4f}")

# Check if data matches expected location
count = struct.unpack_from('<I', data, 3234)[0]
data_start = 3238
data_end = data_start + count * 4

print(f"\nCurrent data block:")
print(f"  Starts at: {data_start}")
print(f"  Ends at: {data_end}")
print(f"  Size: {count * 4} bytes")
print(f"  Remaining after: {file_size - data_end} bytes")

# Read current intensities
intensities_current = np.frombuffer(data[data_start:data_end], dtype='<f4')
print(f"\nCurrent data:")
print(f"  Count: {len(intensities_current)}")
print(f"  Range: {intensities_current.min():.0f} to {intensities_current.max():.0f}")
print(f"  First 10: {intensities_current[:10]}")
print(f"  At index 350 (12°): {intensities_current[350]:.0f}")
print(f"  At index 1600 (37°): {intensities_current[1600]:.0f}")

# Check if there's a second data block
if file_size > data_end:
    remaining = file_size - data_end
    print(f"\nRemaining bytes: {remaining}")
    if remaining >= count * 4:
        print(f"  Could be a second data block!")
        intensities_second = np.frombuffer(data[data_end:data_end + count * 4], dtype='<f4')
        print(f"  Second block count: {len(intensities_second)}")
        print(f"  Range: {intensities_second.min():.0f} to {intensities_second.max():.0f}")
        print(f"  First 10: {intensities_second[:10]}")
        print(f"  At index 350 (12°): {intensities_second[350]:.0f}")
        print(f"  At index 1600 (37°): {intensities_second[1600]:.0f}")

# Compare with ASC file second column
print(f"\nComparing with ASC file second column:")
from src.core.file_parser import ASCParser
asc = ASCParser.parse('input_data/20250520/Ti2AlC3.ASC')

# Read ASC file manually to get second column
asc_lines = Path('input_data/20250520/Ti2AlC3.ASC').read_text().split('\n')
import re
asc_col2 = []
for line in asc_lines[1:]:
    parts = re.split(r'\s+', line.strip())
    if len(parts) >= 4:
        try:
            asc_col2.append(float(parts[3]))
        except:
            pass

if len(asc_col2) > 0:
    asc_col2 = np.array(asc_col2)
    print(f"  ASC column 2 count: {len(asc_col2)}")
    print(f"  Range: {asc_col2.min():.0f} to {asc_col2.max():.0f}")
    print(f"  First 10: {asc_col2[:10]}")
    if len(asc_col2) > 350:
        print(f"  At index 350 (12°): {asc_col2[350]:.0f}")
    if len(asc_col2) > 1600:
        print(f"  At index 1600 (37°): {asc_col2[1600]:.0f}")

