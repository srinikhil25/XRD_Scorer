"""Check RAW file data to understand structure"""
import struct
import numpy as np
from pathlib import Path

raw_file = Path('input_data/20251126/20251126/cMX-2.raw')
data = raw_file.read_bytes()
file_size = len(data)

print(f"File size: {file_size} bytes")

# Find count
count = None
for offset in range(0, min(10000, file_size - 4), 4):
    try:
        c = struct.unpack_from('<I', data, offset)[0]
        if 100 <= c <= 100000 and offset + 4 + c * 4 == file_size:
            count = c
            data_offset = offset + 4
            print(f"Found count: {count} at offset {offset}")
            print(f"Data starts at: {data_offset}")
            break
    except:
        pass

if count:
    intensities = np.frombuffer(data[data_offset:data_offset + count * 4], dtype='<f4')
    print(f"Intensities: {len(intensities)} points")
    print(f"Range: {intensities.min():.0f} to {intensities.max():.0f}")
    
    # Check where data actually ends (where intensities drop to near zero)
    # Find last significant data point
    threshold = intensities.max() * 0.01  # 1% of max
    significant = intensities > threshold
    last_significant = np.where(significant)[0]
    if len(last_significant) > 0:
        last_idx = last_significant[-1]
        print(f"Last significant data point at index: {last_idx} ({last_idx/count*100:.1f}% of data)")
        
        # Calculate what 2theta that would be
        # If step is 0.02 and start is 5.0
        step = 0.02
        start = 5.0
        actual_end = start + last_idx * step
        print(f"Actual data range: {start:.2f}° to {actual_end:.2f}° (if step={step})")
        
        # Try different steps
        for test_step in [0.01, 0.02, 0.05]:
            test_end = start + last_idx * test_step
            if 85 <= test_end <= 95:
                print(f"  Step {test_step}: range would be {start:.2f}° to {test_end:.2f}°")

