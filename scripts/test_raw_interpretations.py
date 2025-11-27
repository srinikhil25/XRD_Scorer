"""Test different interpretations of RAW file data"""
import struct
import numpy as np
from pathlib import Path

raw_file = Path('input_data/20250520/Ti2AlC3.raw')
data = raw_file.read_bytes()
file_size = len(data)

# Known header values
count = struct.unpack_from('<I', data, 3234)[0]
start = struct.unpack_from('<f', data, 3010)[0]
end = struct.unpack_from('<f', data, 3014)[0]
step = struct.unpack_from('<f', data, 3018)[0]

print(f"Header info: count={count}, start={start:.2f}°, end={end:.2f}°, step={step:.4f}°")
print(f"File size: {file_size} bytes")
print(f"Expected data size: {count * 4} bytes")
print(f"Data offset: 3238")
print()

# Read ASC file second column for comparison
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
asc_col2 = np.array(asc_col2[:count])  # Match count

# Current interpretation (intensities only)
intensities_current = np.frombuffer(data[3238:3238+count*4], dtype='<f4')
print("Current interpretation (intensities only):")
print(f"  First 10: {intensities_current[:10]}")
print(f"  At 12.5° (index ~375): {intensities_current[375]:.0f}")
print(f"  At 37° (index ~1600): {intensities_current[1600]:.0f}")
print(f"  Max intensity: {intensities_current.max():.0f} at index {intensities_current.argmax()}")
print()

# Try interpreting as pairs (2theta, intensity)
if (file_size - 3238) >= count * 8:
    print("Trying as pairs (2theta, intensity) - 8 bytes per point:")
    pairs = np.frombuffer(data[3238:3238+count*8], dtype=[('theta', '<f4'), ('intensity', '<f4')])
    print(f"  First 5 thetas: {pairs['theta'][:5]}")
    print(f"  First 5 intensities: {pairs['intensity'][:5]}")
    print(f"  Theta range: {pairs['theta'].min():.2f}° to {pairs['theta'].max():.2f}°")
    print(f"  Intensity range: {pairs['intensity'].min():.0f} to {pairs['intensity'].max():.0f}")
    print()

# Try big-endian
print("Trying big-endian float32:")
intensities_be = np.frombuffer(data[3238:3238+count*4], dtype='>f4')
print(f"  First 10: {intensities_be[:10]}")
print(f"  Range: {intensities_be.min():.0f} to {intensities_be.max():.0f}")
print()

# Try reading from a different offset
print("Checking if data might be at different locations:")
for test_offset in [0, 1024, 2048, 3010, 3238]:
    if test_offset + count * 4 <= file_size:
        test_data = np.frombuffer(data[test_offset:test_offset+count*4], dtype='<f4')
        if np.all(test_data >= 0) and np.all(test_data < 1e6):
            print(f"  Offset {test_offset}: valid range {test_data.min():.0f} to {test_data.max():.0f}")
            if len(test_data) > 375:
                print(f"    At index 375: {test_data[375]:.0f}")
            if len(test_data) > 1600:
                print(f"    At index 1600: {test_data[1600]:.0f}")

print()
print("ASC file column 2 (for comparison):")
print(f"  First 10: {asc_col2[:10]}")
print(f"  At index 375: {asc_col2[375]:.0f}")
print(f"  At index 1600: {asc_col2[1600]:.0f}")
print(f"  Max: {asc_col2.max():.0f} at index {asc_col2.argmax()}")

