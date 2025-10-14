#!/usr/bin/env python3
"""
Add tabs to dashboard - Final comprehensive version
This reads the file, finds sections, and writes a completely new file with proper tabs
"""
import re

print("=" * 70)
print("DASHBOARD TAB RESTRUCTURE")
print("=" * 70)

# Read the entire file
print("\n[1/5] Reading dashboard.py...")
with open('dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find section boundaries using regex
print("[2/5] Locating sections...")

# Find Section 2 (Prices) - starts with comment, ends before Section 2.5
section2_match = re.search(
    r'(# ={42}\n# SECTION 2: System Demand Analysis\n# ={42}\n)',
    content
)
section2_start = section2_match.start() if section2_match else -1

# Find Section 2.5 (ML Anomaly)
section25_match = re.search(
    r'(# ={42}\n# SECTION 2\.5: ML-Powered Anomaly Detection.*?\n# ={42}\n)',
    content
)
section25_start = section25_match.start() if section25_match else -1

# Find Section 3 (Demand)
section3_match = re.search(
    r'(# ={42}\n# SECTION 3: Real-Time Price Analysis\n# ={42}\n)',
    content
)
section3_start = section3_match.start() if section3_match else -1

# Find the end of Section 3 (look for the next st.markdown("---") after Section 3)
if section3_start > 0:
    section3_content = content[section3_start:]
    # Find the closing else block for demand section
    end_pattern = r'else:\s+st\.warning\("⚠️ Unable to fetch demand forecast data.*?"\)\s*\nst\.markdown\("---"\)'
    end_match = re.search(end_pattern, section3_content, re.DOTALL)
    if end_match:
        section3_end = section3_start + end_match.end()
    else:
        section3_end = -1
else:
    section3_end = -1

print(f"   Section 2 (Prices): char {section2_start}")
print(f"   Section 2.5 (ML): char {section25_start}")  
print(f"   Section 3 (Demand): char {section3_start}")
print(f"   Section 3 end: char {section3_end}")

if -1 in [section2_start, section25_start, section3_start, section3_end]:
    print("\n❌ ERROR: Could not locate all sections!")
    print("Please check the dashboard structure.")
    exit(1)

# Extract sections
print("[3/5] Extracting sections...")
before_section2 = content[:section2_start]
prices_section = content[section2_start:section25_start]
ml_section = content[section25_start:section3_start]
demand_section = content[section3_start:section3_end]
after_section3 = content[section3_end:]

# Helper function to indent text
def indent_text(text, spaces=4):
    """Indent all non-empty lines"""
    lines = text.split('\n')
    result = []
    for line in lines:
        if line.strip():  # Non-empty line
            result.append(' ' * spaces + line)
        else:  # Empty line
            result.append(line)
    return '\n'.join(result)

# Build new content
print("[4/5] Building new structure with tabs...")

new_content = before_section2

# Add tab structure
new_content += "# ==========================================\n"
new_content += "# SECTION 2: Tabbed Analysis View\n"
new_content += "# ==========================================\n"
new_content += 'tab1, tab2 = st.tabs(["📈 System Demand Forecast & AI Analysis", "💰 Real-Time Energy Prices"])\n'
new_content += "\n"

# TAB 1: Demand + ML (default)
new_content += "# ==========================================\n"
new_content += "# TAB 1: SYSTEM DEMAND FORECAST + ML FEATURES\n"  
new_content += "# ==========================================\n"
new_content += "with tab1:\n"
new_content += indent_text(demand_section)
new_content += "\n\n"
new_content += indent_text(ml_section)
new_content += "\n"

# TAB 2: Prices
new_content += "# ==========================================\n"
new_content += "# TAB 2: REAL-TIME ENERGY PRICES\n"
new_content += "# ==========================================\n"
new_content += "with tab2:\n"
new_content += indent_text(prices_section)
new_content += "\n"

# Add remaining content
new_content += "\nst.markdown(\"---\")\n"
new_content += after_section3

# Write new file
print("[5/5] Writing new dashboard.py...")
with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n" + "=" * 70)
print("✅ SUCCESS! Dashboard restructured with tabs")
print("=" * 70)
print("\nNew structure:")
print("  📑 Tab 1 (default): System Demand Forecast + ML Analysis")
print("  📑 Tab 2: Real-Time Energy Prices")
print("\nNext step:")
print("  Restart Streamlit: Ctrl+C then rerun")
