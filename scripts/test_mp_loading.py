"""Test MP file loading"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.reference_pattern import ReferenceDatabase

# Test loading MP database
db = ReferenceDatabase()
db.load_database('data/examples/reference_patterns')

print(f'Loaded {len(db)} patterns from MP database')
print('\nFirst 5 patterns:')
for i, p in enumerate(db.get_all()[:5]):
    print(f'  {i+1}. ID: "{p.id}", Name: "{p.name}", Source: {p.data.get("source", "N/A")}')
    print(f'     Has pattern data: {p.two_theta is not None and len(p.two_theta) > 0}')

# Test loading ICDD database
db2 = ReferenceDatabase()
db2.load_database('data/databases/json')

print(f'\nLoaded {len(db2)} patterns from ICDD database')
print('\nFirst 5 patterns:')
for i, p in enumerate(db2.get_all()[:5]):
    print(f'  {i+1}. ID: "{p.id}", Name: "{p.name}", Source: {p.data.get("source", "N/A")}')
    print(f'     Has pattern data: {p.two_theta is not None and len(p.two_theta) > 0}')

# Test search
print('\n\nSearch test:')
results = db.search('mp-3271')
print(f'Search "mp-3271": {len(results)} results')
for r in results:
    print(f'  Found: {r.id} / {r.name}')

results2 = db2.search('Ti3AlC2')
print(f'\nSearch "Ti3AlC2": {len(results2)} results')
for r in results2:
    print(f'  Found: {r.id} / {r.name}')

