#!/usr/bin/env python3
"""Fix indentation for ML sections to be inside tab1"""

with open('dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the range to indent (from line 610 to line 792)
# Lines are 0-indexed in Python, so subtract 1
start_line = 609  # Line 610 in editor
end_line = 791    # Line 792 in editor

print(f"Indenting lines {start_line+1} to {end_line+1}")

# Add 4 spaces to each line in this range
for i in range(start_line, min(end_line + 1, len(lines))):
    if lines[i].strip():  # Only indent non-empty lines
        lines[i] = '    ' + lines[i]

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Indentation fixed for ML sections')
