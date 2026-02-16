"""
Add version fields to existing SPDX license dataset.
"""
import re
import pandas as pd
from datasets import Dataset

def parse_license_version(spdx_id):
    """Extract license family, version, and version modifiers from SPDX ID."""
    result = {
        "license_family": None,
        "version": None,
        "version_modifier": None
    }
    
    # Handle "only" and "or-later" modifiers
    if "-only" in spdx_id:
        result["version_modifier"] = "only"
        spdx_id = spdx_id.replace("-only", "")
    elif "-or-later" in spdx_id:
        result["version_modifier"] = "or-later"
        spdx_id = spdx_id.replace("-or-later", "")
    elif spdx_id.endswith("+"):
        result["version_modifier"] = "or-later"
        spdx_id = spdx_id.rstrip("+")
    
    # Try to extract version number from SPDX ID
    version_match = re.search(r'-(\d+(?:\.\d+)*(?:\.\d+)?)(?:-|$)', spdx_id)
    if version_match:
        result["version"] = version_match.group(1)
        result["license_family"] = spdx_id[:version_match.start()]
    else:
        result["license_family"] = spdx_id
    
    return result

# Load existing dataset
print("Loading existing dataset...")
df = pd.read_parquet("spdx_licenses_dataset.parquet")
print(f"Loaded {len(df)} licenses")

# Add version fields
print("Parsing version information...")
version_data = df['spdx_id'].apply(parse_license_version).apply(pd.Series)
df['license_family'] = version_data['license_family']
df['version'] = version_data['version']
df['version_modifier'] = version_data['version_modifier']

# Reorder columns
column_order = ['license_name', 'spdx_id', 'license_family', 'version', 'version_modifier', 'usage_category', 'full_text', 'source_url']
df = df[column_order]

# Save
print("Saving updated dataset...")
ds = Dataset.from_pandas(df)
ds.save_to_disk("spdx_licenses_dataset")
ds.to_parquet("spdx_licenses_dataset.parquet")

print(f"\nDataset updated with {len(df)} licenses")
print(f"Columns: {list(df.columns)}")
print("\nSample:")
print(df[['spdx_id', 'license_family', 'version', 'version_modifier']].head(10))

