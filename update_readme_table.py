#!/usr/bin/env python3

import os
import pandas as pd
from pathlib import Path

def get_facility_counts():
    """Get facility counts for each jurisdiction from the data files."""
    data_dir = Path('data')
    facility_counts = {}
    
    # Jurisdiction metadata
    jurisdictions = {
        'federal': {
            'name': 'Federal',
            'agency': 'Bureau of Prisons (BOP)'
        },
        'california': {
            'name': 'California', 
            'agency': 'Dept. of Corrections and Rehabilitation (CDCR)'
        },
        'texas': {
            'name': 'Texas',
            'agency': 'Dept. of Criminal Justice (TDCJ)'
        },
        'new_york': {
            'name': 'New York',
            'agency': 'Dept. of Corrections and Community Supervision (DOCCS)'
        },
        'illinois': {
            'name': 'Illinois',
            'agency': 'Dept. of Corrections (IDOC)'
        },
        'florida': {
            'name': 'Florida',
            'agency': 'Dept. of Corrections (FDC)'
        },
        'pennsylvania': {
            'name': 'Pennsylvania',
            'agency': 'Dept. of Corrections (PA DOC)'
        },
        'georgia': {
            'name': 'Georgia',
            'agency': 'Dept. of Corrections (GDC)'
        },
        'north_carolina': {
            'name': 'North Carolina',
            'agency': 'Dept. of Adult Correction (DAC)'
        },
        'michigan': {
            'name': 'Michigan',
            'agency': 'Dept. of Corrections (MDOC)'
        },
        'virginia': {
            'name': 'Virginia',
            'agency': 'Dept. of Corrections (VADOC)'
        },
        'washington': {
            'name': 'Washington',
            'agency': 'Dept. of Corrections (WADOC)'
        },
        'arizona': {
            'name': 'Arizona',
            'agency': 'Dept. of Corrections (ADOC)'
        },
        'tennessee': {
            'name': 'Tennessee',
            'agency': 'Dept. of Correction (TDOC)'
        },
        'massachusetts': {
            'name': 'Massachusetts',
            'agency': 'Dept. of Correction (MADOC)'
        },
        'indiana': {
            'name': 'Indiana',
            'agency': 'Dept. of Correction (IDOC)'
        }
    }
    
    total_facilities = 0
    
    for jurisdiction_key, jurisdiction_info in jurisdictions.items():
        csv_file = data_dir / jurisdiction_key / f"{jurisdiction_key}_prisons.csv"
        
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                count = len(df)
                facility_counts[jurisdiction_key] = {
                    'name': jurisdiction_info['name'],
                    'agency': jurisdiction_info['agency'],
                    'count': count
                }
                total_facilities += count
                print(f"✓ {jurisdiction_info['name']}: {count} facilities")
            except Exception as e:
                print(f"✗ Error reading {csv_file}: {e}")
        else:
            print(f"✗ File not found: {csv_file}")
    
    return facility_counts, total_facilities

def generate_table_markdown(facility_counts):
    """Generate the markdown table for the README."""
    
    # Sort by facility count (descending)
    sorted_jurisdictions = sorted(
        facility_counts.items(), 
        key=lambda x: x[1]['count'], 
        reverse=True
    )
    
    lines = []
    lines.append("| Jurisdiction | Agency | Facilities |")
    lines.append("|--------------|--------|------------|")
    
    for jurisdiction_key, info in sorted_jurisdictions:
        name = f"**{info['name']}**"
        agency = info['agency']
        count = info['count']
        lines.append(f"| {name} | {agency} | {count} |")
    
    return '\n'.join(lines)

def update_readme(table_markdown, total_facilities, total_jurisdictions):
    """Update the README.md file with the new table."""
    
    readme_path = Path('README.md')
    
    if not readme_path.exists():
        print("✗ README.md not found")
        return
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Find the table section and replace it
    start_marker = "| Jurisdiction | Agency | Facilities |"
    end_marker = f"**Total Coverage**: "
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("✗ Could not find table start marker in README.md")
        return
    
    end_idx = content.find(end_marker)
    if end_idx == -1:
        print("✗ Could not find table end marker in README.md")
        return
    
    # Replace the table section
    new_content = (
        content[:start_idx] + 
        table_markdown + 
        f"\n\n**Total Coverage**: {total_facilities} facilities across {total_jurisdictions} jurisdictions\n\n" +
        content[end_idx:].split('\n\n', 1)[1]
    )
    
    with open(readme_path, 'w') as f:
        f.write(new_content)
    
    print(f"✓ Updated README.md with {total_facilities} facilities across {total_jurisdictions} jurisdictions")

def main():
    """Main function to update the README table."""
    print("Updating README.md facility table...")
    print("=" * 50)
    
    # Get facility counts
    facility_counts, total_facilities = get_facility_counts()
    
    if not facility_counts:
        print("✗ No facility data found")
        return
    
    total_jurisdictions = len(facility_counts)
    
    print(f"\nTotal: {total_facilities} facilities across {total_jurisdictions} jurisdictions")
    print()
    
    # Generate table markdown
    table_markdown = generate_table_markdown(facility_counts)
    
    print("Generated table:")
    print(table_markdown)
    print()
    
    # Update README
    update_readme(table_markdown, total_facilities, total_jurisdictions)

if __name__ == "__main__":
    main()
