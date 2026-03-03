#!/usr/bin/env python3
"""Verification script for linkBox ID updates"""

import json
import os
import re

print("Verifying linkBox ID updates...")
print("=" * 70)

# Test 1: Verify JSON changes
print("\n1. JSON LinkBox Update Verification")
print("-" * 70)

with open('tests/data/textcritics.json') as f:
    data = json.load(f)

total_linkboxes = 0
updated_linkboxes = 0

for entry in data['textcritics']:
    entry_id = entry.get('id')
    for lb in entry.get('linkBoxes', []):
        total_linkboxes += 1
        svg_id = lb.get('svgGroupId', '')
        sheet_id = lb.get('linkTo', {}).get('sheetId', '')
        expected_format = f'{entry_id}to{sheet_id}'
        
        if svg_id == expected_format:
            updated_linkboxes += 1

print(f"Total linkBoxes in JSON: {total_linkboxes}")
print(f"Updated to correct format {'{entry_id}to{sheetId}'}: {updated_linkboxes}")
print(f"JSON Update Status: {'✓ PASSED' if updated_linkboxes == total_linkboxes else '✗ FAILED'}")

# Test 2: Verify SVG changes  
print("\n2. SVG LinkBox Update Verification")
print("-" * 70)

svg_folder = 'tests/img/'
pattern = re.compile(r'id="([^"]*to[^"]*)" class="link-box"')

svg_count = 0
svg_files_with_linkbox = 0

for filename in os.listdir(svg_folder):
    if filename.endswith('.svg'):
        with open(os.path.join(svg_folder, filename)) as f:
            content = f.read()
            matches = pattern.findall(content)
            if matches:
                svg_files_with_linkbox += 1
                svg_count += len(matches)

print(f"SVG files with updated linkBoxes: {svg_files_with_linkbox}")
print(f"Total updated linkBox IDs in SVGs: {svg_count}")
print(f"SVG Update Status: {'✓ PASSED' if svg_count > 0 else '✗ FAILED'}")

# Test 3: Sample verification
print("\n3. Sample Data Verification")
print("-" * 70)

sample_entries = [e for e in data['textcritics'] if e.get('linkBoxes')][:2]
for entry in sample_entries:
    entry_id = entry.get('id')
    print(f"\nEntry: {entry_id}")
    for i, lb in enumerate(entry.get('linkBoxes', [])[:3]):
        svg_id = lb.get('svgGroupId')
        sheet_id = lb.get('linkTo', {}).get('sheetId')
        print(f"  LinkBox {i+1}: {svg_id}")

print("\n" + "=" * 70)
print("Verification Complete!")
print("=" * 70)
