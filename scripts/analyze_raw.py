import re
from pathlib import Path

asc_path = Path("input_data/20250520/Ti2AlC3.ASC")
lines = asc_path.read_text().splitlines()
two_theta = []
intensity = []
skipped = 0

for idx, line in enumerate(lines[:20]):
    print(repr(line))

for line in lines:
    line = line.strip()
    if not line or line.lower().startswith("deg"):
        skipped += 1
        continue
    parts = re.split(r"[\\s\\t,;]+", line)
    print("parts", parts[:4])
    if len(parts) >= 2:
        try:
            two_theta.append(float(parts[0]))
            intensity.append(float(parts[1]))
        except ValueError:
            skipped += 1

print(len(two_theta))
print(two_theta[:5])
print(intensity[:5])
print("skipped", skipped)

