"""
Build a Hugging Face dataset of open-source license texts from the SPDX License List.

Usage:
    pip install datasets huggingface_hub requests
    python build_license_dataset.py

This will:
1. Fetch all license texts from the SPDX license-list-data repo
2. Structure them into a HF dataset with columns:
   - license_name: Full name of the license
   - spdx_id: SPDX identifier (e.g., "MIT", "Apache-2.0")
   - license_family: Base license name (e.g., "Apache", "GPL", "MIT")
   - version: Version number (e.g., "2.0", "3.0") or None
   - version_modifier: "only", "or-later", or None
   - usage_category: Typical usage on HF ("dataset", "model", "both", "code", "other")
   - full_text: Complete legal text of the license
   - source_url: URL to the official SPDX page for this license
3. Save locally and optionally push to Hugging Face Hub
"""

import json
import re
import requests
from datasets import Dataset

SPDX_LICENSES_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
SPDX_DETAIL_BASE = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/details/"

# Categorization of licenses based on typical HuggingFace usage
LICENSE_USAGE_MAP = {
    # Licenses commonly used for BOTH datasets and models
    "MIT": "both",
    "Apache-2.0": "both",
    "BSD-2-Clause": "both",
    "BSD-3-Clause": "both",
    "GPL-3.0": "both",
    "GPL-2.0": "both",
    "LGPL-3.0": "both",
    "LGPL-2.1": "both",
    "ISC": "both",
    "MPL-2.0": "both",
    
    # Creative Commons - primarily for datasets but also used for models
    "CC0-1.0": "both",
    "CC-BY-4.0": "dataset",
    "CC-BY-SA-4.0": "dataset",
    "CC-BY-NC-4.0": "dataset",
    "CC-BY-NC-SA-4.0": "dataset",
    "CC-BY-ND-4.0": "dataset",
    "CC-BY-NC-ND-4.0": "dataset",
    
    # Data-specific licenses
    "CDLA-Permissive-1.0": "dataset",
    "CDLA-Permissive-2.0": "dataset",
    "CDLA-Sharing-1.0": "dataset",
    "C-UDA-1.0": "dataset",
    "ODbL-1.0": "dataset",
    "PDDL-1.0": "dataset",
    
    # Model-specific (RAIL and similar)
    "OpenRAIL-M": "model",
    "OpenRAIL++": "model",
    "BigScience-OpenRAIL-M": "model",
    "CreativeML-OpenRAIL-M": "model",
    "BigScience-BLOOM-RAIL-1.0": "model",
    
    # Code/software specific
    "AGPL-3.0": "code",
    "Unlicense": "both",
    "WTFPL": "code",
    "Zlib": "code",
    "BSL-1.0": "code",
    
    # Proprietary/restrictive
    "SSPL-1.0": "code",
}


def get_license_usage_category(spdx_id: str) -> str:
    """
    Determine the typical usage category for a license on Hugging Face.
    
    Returns:
        "dataset" - primarily used for datasets
        "model" - primarily used for models
        "both" - commonly used for both datasets and models
        "code" - primarily used for code/software
        "other" - general purpose or unknown usage pattern
    """
    # Direct match
    if spdx_id in LICENSE_USAGE_MAP:
        return LICENSE_USAGE_MAP[spdx_id]
    
    # Pattern matching for license families
    if "CC-BY" in spdx_id or "CC-" in spdx_id:
        return "dataset"
    if "GPL" in spdx_id or "LGPL" in spdx_id:
        return "both"
    if "BSD" in spdx_id:
        return "both"
    if "Apache" in spdx_id:
        return "both"
    if "RAIL" in spdx_id or "OpenRAIL" in spdx_id:
        return "model"
    if "CDLA" in spdx_id or "ODbL" in spdx_id:
        return "dataset"
    
    # Default for unknown licenses
    return "other"


def parse_license_version(spdx_id: str, license_name: str) -> dict:
    """
    Extract license family, version, and version modifiers from SPDX ID.
    
    Returns:
        dict with keys:
            - license_family: Base license name (e.g., "Apache", "GPL", "MIT")
            - version: Version number (e.g., "2.0", "3.0") or None
            - version_modifier: "only", "or-later", or None
    """
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
    # Pattern: LICENSE-X.Y or LICENSE-X.Y.Z
    version_match = re.search(r'-(\d+(?:\.\d+)*(?:\.\d+)?)(?:-|$)', spdx_id)
    if version_match:
        result["version"] = version_match.group(1)
        # Extract family name (everything before the version)
        family = spdx_id[:version_match.start()]
        result["license_family"] = family
    else:
        # No version found, the whole ID is the family
        result["license_family"] = spdx_id
    
    # Special handling for common families
    if result["license_family"] in ["GPL", "LGPL", "AGPL", "GFDL"]:
        # Keep as-is
        pass
    elif result["license_family"] == "CC0":
        result["license_family"] = "CC0"
    elif result["license_family"].startswith("CC-"):
        # Creative Commons licenses
        result["license_family"] = "Creative Commons"
    
    return result


def fetch_license_list():
    """Fetch the master list of all SPDX licenses."""
    print("Fetching SPDX license list...")
    resp = requests.get(SPDX_LICENSES_URL)
    resp.raise_for_status()
    data = resp.json()
    print(f"Found {len(data['licenses'])} licenses.")
    return data["licenses"]


def fetch_license_detail(spdx_id: str) -> str:
    """Fetch the full legal text for a single license."""
    url = f"{SPDX_DETAIL_BASE}{spdx_id}.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        detail = resp.json()
        return detail.get("licenseText", "")
    except Exception as e:
        print(f"  Warning: Could not fetch {spdx_id}: {e}")
        return ""


def build_dataset(push_to_hub: bool = False, hub_repo: str = None):
    """Build the full dataset."""
    licenses = fetch_license_list()

    rows = []
    for i, lic in enumerate(licenses):
        spdx_id = lic["licenseId"]
        print(f"  [{i+1}/{len(licenses)}] Fetching {spdx_id}...")

        full_text = fetch_license_detail(spdx_id)

        usage_category = get_license_usage_category(spdx_id)
        version_info = parse_license_version(spdx_id, lic["name"])
        
        rows.append({
            "license_name": lic["name"],
            "spdx_id": spdx_id,
            "license_family": version_info["license_family"],
            "version": version_info["version"],
            "version_modifier": version_info["version_modifier"],
            "usage_category": usage_category,
            "full_text": full_text,
            "source_url": lic.get("reference", f"https://spdx.org/licenses/{spdx_id}.html"),
        })

    ds = Dataset.from_list(rows)
    print(f"\nDataset built: {len(ds)} licenses")
    print(ds)

    # Save locally
    ds.save_to_disk("spdx_licenses_dataset")
    ds.to_parquet("spdx_licenses_dataset.parquet")
    ds.to_csv("spdx_licenses_dataset.csv")
    print("Saved to: spdx_licenses_dataset/, .parquet, .csv")

    # Optionally push to HF Hub
    if push_to_hub and hub_repo:
        ds.push_to_hub(hub_repo)
        print(f"Pushed to: https://huggingface.co/datasets/{hub_repo}")

    return ds


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build SPDX license dataset")
    parser.add_argument("--push", action="store_true", help="Push to HF Hub")
    parser.add_argument("--repo", type=str, default=None, help="HF repo (e.g., 'midah/spdx-licenses')")
    args = parser.parse_args()

    build_dataset(push_to_hub=args.push, hub_repo=args.repo)

