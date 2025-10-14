#!/usr/bin/env python3
"""
Add tabs to dashboard.py - robust version
"""

def indent_lines(text, spaces=4):
    """Add indentation to all non-empty lines"""
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():  # Only indent non-empty lines
            result.append(' ' * spaces + line)
        else:
            result.append(line)
    return '\n'.join(result)

print("Reading dashboard.py...")
with open('dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key line numbers
section2_line = None
section25_line = None
section3_line = None
section3_end_line = None

for i, line in enumerate(lines):
    if '# SECTION 2: System Demand Analysis' in line:
        section2_line = i
    elif '# SECTION 2.5: ML-Powered Anomaly Detection' in line:
        section25_line = i
    elif '# SECTION 3: Real-Time Price Analysis' in line:
        section3_line = i
    elif section3_line and i > section3_line and 'st.markdown("---")' in line and section3_end_line is None:
        section3_end_line = i + 1  # Include the markdown line

print(f"Found Section 2 (Prices) at line {section2_line + 1}")
print(f"Found Section 2.5 (ML) at line {section25_line + 1}")
print(f"Found Section 3 (Demand) at line {section3_line + 1}")
print(f"Found Section 3 end at line {section3_end_line + 1}")

# Extract sections
before_section2 = lines[:section2_line]
prices_section = lines[section2_line:section25_line]
ml_sections = lines[section25_line:section3_line]
demand_section = lines[section3_line:section3_end_line]
after_section3 = lines[section3_end_line:]

# Create new structure
new_lines = []

# Add content before section 2
new_lines.extend(before_section2)

# Add tab structure
new_lines.append('# ==========================================\n')
new_lines.append('# SECTION 2: Tabbed Analysis View\n')
new_lines.append('# ==========================================\n')
new_lines.append('tab1, tab2 = st.tabs(["📈 System Demand Forecast & AI Analysis", "💰 Real-Time Energy Prices"])\n')
new_lines.append('\n')

# TAB 1: Demand + ML
new_lines.append('# ==========================================\n')
new_lines.append('# TAB 1: SYSTEM DEMAND FORECAST + ML FEATURES (Default)\n')
new_lines.append('# ==========================================\n')
new_lines.append('with tab1:\n')

# Indent demand section
for line in demand_section:
    if line.strip():
        new_lines.append('    ' + line)
    else:
        new_lines.append(line)

new_lines.append('\n')

# Indent ML sections
for line in ml_sections:
    if line.strip():
        new_lines.append('    ' + line)
    else:
        new_lines.append(line)

new_lines.append('\n')

# TAB 2: Prices
new_lines.append('# ==========================================\n')
new_lines.append('# TAB 2: REAL-TIME ENERGY PRICES\n')
new_lines.append('# ==========================================\n')
new_lines.append('with tab2:\n')

# Indent prices section
for line in prices_section:
    if line.strip():
        new_lines.append('    ' + line)
    else:
        new_lines.append(line)

new_lines.append('\n')
new_lines.append('st.markdown("---")\n')
new_lines.append('\n')

# Add remaining content
new_lines.extend(after_section3)

# Write new file
print("\nWriting restructured dashboard.py...")
with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Dashboard restructured successfully!")
print("\nStructure:")
print("  Tab 1 (default): System Demand Forecast + ML Analysis") 
print("  Tab 2: Real-Time Energy Prices")
print("\nRestart the Streamlit app to see changes.")
