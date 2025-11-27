import numpy as np
from pathlib import Path

raw_path = Path("input_data/20250520/Ti2AlC3.raw")
data = raw_path.read_bytes()

found = False
for dtype, step, upper in [
    ("<u2", 2, 10000),
    ("<i2", 2, 10000),
    ("<i4", 4, 1000000),
    ("<f4", 4, 1000000),
]:
    for offset in range(0, len(data) - 4000, step):
        arr = np.frombuffer(data[offset : offset + 4000], dtype=dtype)
        if arr.size < 1000:
            continue
        if not np.all(np.isfinite(arr)):
            continue
        min_val = float(arr.min())
        max_val = float(arr.max())
        if min_val >= 0 and max_val <= upper:
            print(f"Candidate dtype {dtype} at offset {offset}, sample {arr[:10]}")
            found = True
            break
    if found:
        break

if not found:
    print("No int32 block found")

