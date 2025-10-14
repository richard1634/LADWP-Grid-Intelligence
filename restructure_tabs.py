#!/usr/bin/env python3
"""
Restructure dashboard.py to use tabs:
- Tab 1 (default): System Demand Forecast + ML Features
- Tab 2: Real-Time Energy Prices
"""

import re

print("Reading dashboard.py...")
with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section markers
section2_start = content.find('# SECTION 2: System Demand Analysis')
section2_end = content.find('st.markdown("---")\n\n# ==========================================\n# SECTION 2.5:')
section25_start = content.find('# SECTION 2.5: ML-Powered Anomaly Detection')
section26_start = content.find('# SECTION 2.6: Smart Recommendations')
section3_start = content.find('# SECTION 3: Real-Time Price Analysis')
section3_end = content.find('st.markdown("---")\n\n# ==========================================\n# SECTION 4:')

if section3_end == -1:
    # Look for end of file or next major section
    section3_end = content.find('\n\n# ==========================================\n# SECTION 4:', section3_start)
    if section3_end == -1:
        # Find the end of the demand section (look for the else block and following markdown)
        pattern = r'(else:\s+st\.warning\("⚠️ Unable to fetch demand forecast data[^"]*"\)\s*\nst\.markdown\("---"\))'
        match = re.search(pattern, content[section3_start:])
        if match:
            section3_end = section3_start + match.end()

print(f"Section 2 (Prices): {section2_start} to {section2_end}")
print(f"Section 2.5 (ML Anomaly): {section25_start}")
print(f"Section 2.6 (Recommendations): {section26_start}")
print(f"Section 3 (Demand): {section3_start} to {section3_end}")

# Extract sections
before_section2 = content[:section2_start]
prices_section = content[section2_start:section2_end]
ml_sections = content[section25_start:section3_start]
demand_section = content[section3_start:section3_end]
after_section3 = content[section3_end:]

# Create tab structure
tab_structure = '''# ==========================================
# SECTION 2: Tabbed Analysis View
# ==========================================
tab1, tab2 = st.tabs(["📈 System Demand Forecast & AI Analysis", "💰 Real-Time Energy Prices"])

# ==========================================
# TAB 1: SYSTEM DEMAND FORECAST + ML FEATURES (Default)
# ==========================================
with tab1:
'''

# Indent demand section (4 spaces)
demand_lines = demand_section.split('\n')
indented_demand = []
for line in demand_lines:
    if line.strip():  # Only indent non-empty lines
        indented_demand.append('    ' + line)
    else:
        indented_demand.append(line)
demand_section_indented = '\n'.join(indented_demand)

# Indent ML sections (4 spaces)
ml_lines = ml_sections.split('\n')
indented_ml = []
for line in ml_lines:
    if line.strip():
        indented_ml.append('    ' + line)
    else:
        indented_ml.append(line)
ml_sections_indented = '\n'.join(indented_ml)

# Create Tab 2 structure
tab2_structure = '''

# ==========================================
# TAB 2: REAL-TIME ENERGY PRICES
# ==========================================
with tab2:
'''

# Indent prices section (4 spaces)
prices_lines = prices_section.split('\n')
indented_prices = []
for line in prices_lines:
    if line.strip():
        indented_prices.append('    ' + line)
    else:
        indented_prices.append(line)
prices_section_indented = '\n'.join(indented_prices)

# Reconstruct the file
new_content = (
    before_section2 +
    tab_structure +
    demand_section_indented +
    '\n\n' +
    ml_sections_indented +
    tab2_structure +
    prices_section_indented +
    '\n\nst.markdown("---")\n' +
    after_section3
)

# Write the new file
print("\nWriting restructured dashboard.py...")
with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Dashboard restructured with tabs!")
print("\nTab 1 (default): System Demand Forecast + ML Analysis")
print("Tab 2: Real-Time Energy Prices")
print("\nRestart Streamlit to see the changes.")
