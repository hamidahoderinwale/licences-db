---
license: cc0-1.0
task_categories:
- text-classification
- text-generation
language:
- en
tags:
- legal
- licenses
- spdx
- open-source
size_categories:
- n<1K
---

# SPDX License Dataset

[![GitHub](https://img.shields.io/badge/GitHub-licences--db-blue?logo=github)](https://github.com/hamidahoderinwale/licences-db)
[![HuggingFace](https://img.shields.io/badge/🤗-Dataset-yellow)](https://huggingface.co/datasets/midah/hf-dataset-licenses)

This dataset contains the complete text of all open-source licenses from the [SPDX License List](https://spdx.org/licenses/), with additional metadata for analyzing license usage patterns on Hugging Face.

## Project Overview

This project provides:
1. **A comprehensive dataset** of SPDX license texts for research and compliance
2. **Systematic version parsing** to extract license families, versions, and modifiers
3. **Usage categorization** for Hugging Face ecosystem (datasets, models, code)
4. **Automated data pipeline** to fetch and structure license information

### Repository Structure

```
licences-db/
├── build_license_dataset.py   # Main script to fetch and build dataset
├── README.md                   # This file
├── spdx_licenses_dataset/     # Full dataset directory
├── spdx_licenses_dataset.parquet  # Dataset in Parquet format
└── spdx_licenses_dataset.csv  # Dataset in CSV format
```

## Dataset Description

- **Homepage:** https://spdx.org/licenses/
- **Repository:** https://github.com/spdx/license-list-data
- **License:** CC0-1.0 (the dataset itself; individual license texts retain their own terms)

## Dataset Structure

### Data Fields

- `license_name` (string): Full name of the license (e.g., "MIT License", "Apache License 2.0")
- `spdx_id` (string): SPDX identifier for the license (e.g., "MIT", "Apache-2.0", "GPL-3.0-or-later")
- `license_family` (string): Base license name without version (e.g., "Apache", "GPL", "MIT")
  - Extracted systematically from SPDX ID using regex parsing
  - Groups related versions together for analysis
- `version` (string or null): Version number if applicable (e.g., "2.0", "3.0", "1.1")
  - Parsed from SPDX ID using pattern matching: `-(\d+(?:\.\d+)*)`
  - `null` for licenses without versions (e.g., "MIT", "Unlicense")
- `version_modifier` (string or null): License versioning flexibility
  - `"only"` - This version specifically (e.g., GPL-3.0-only)
  - `"or-later"` - This version or any later version (e.g., GPL-3.0-or-later, Apache-2.0+)
  - `null` - No modifier specified
- `usage_category` (string): Typical usage context on Hugging Face:
  - `"dataset"` - Primarily used for datasets (e.g., CC-BY-4.0, ODbL-1.0, CDLA)
  - `"model"` - Primarily used for models (e.g., OpenRAIL-M, BigScience-OpenRAIL-M)
  - `"both"` - Commonly used for both datasets and models (e.g., MIT, Apache-2.0, GPL-3.0)
  - `"code"` - Primarily used for code/software (e.g., AGPL-3.0)
  - `"other"` - General purpose or unknown usage pattern
- `full_text` (string): Complete legal text of the license
- `source_url` (string): URL to the official SPDX page for this license
- `page_markdown` (string): Self-contained markdown document including license metadata, full text, standard header, and reference links (in addition to `source_url`)

### How Version Information is Acquired

Version information is **systematically parsed from the standardized SPDX identifier format**, not from separate metadata fields. SPDX uses a consistent naming convention:

**Format**: `{LICENSE_FAMILY}-{VERSION}[-{MODIFIER}]`

**Parsing Strategy**:
1. Extract modifiers (`-only`, `-or-later`, or `+` suffix)
2. Use regex to find version numbers: `r'-(\d+(?:\.\d+)*(?:\.\d+)?)(?:-|$)'`
3. Split into family (text before version), version (numeric part), and modifier

**Examples**:
- `Apache-2.0` → family: "Apache", version: "2.0", modifier: null
- `GPL-3.0-or-later` → family: "GPL", version: "3.0", modifier: "or-later"
- `CC-BY-4.0` → family: "CC-BY", version: "4.0", modifier: null
- `MIT` → family: "MIT", version: null, modifier: null
- `AGPL-1.0+` → family: "AGPL", version: "1.0", modifier: "or-later"

This approach is reliable because SPDX maintains strict naming conventions across all 700+ licenses.

### Data Splits

This dataset contains a single split with all licenses (~700+ licenses).

### License Coverage Note

This dataset includes all official SPDX-registered licenses. Note that some licenses commonly used on Hugging Face (such as `OpenRAIL-M`, `BigScience-OpenRAIL-M`, `CreativeML-OpenRAIL-M`) are not yet part of the official SPDX list and therefore not included in this dataset. These RAIL (Responsible AI License) licenses are model-specific licenses designed for AI systems.

## Dataset Creation

This dataset was created by fetching license data from the official [SPDX license-list-data repository](https://github.com/spdx/license-list-data).

### Source Data

All license texts are sourced directly from the SPDX project's authoritative license list.

## Usage

```python
from datasets import load_dataset

# Load the dataset
ds = load_dataset("midah/hf-dataset-licenses")

# Access a specific license
mit_license = ds['train'].filter(lambda x: x['spdx_id'] == 'MIT')[0]
print(mit_license['full_text'])
print(f"Usage category: {mit_license['usage_category']}")

# Filter by usage category
dataset_licenses = ds['train'].filter(lambda x: x['usage_category'] == 'dataset')
model_licenses = ds['train'].filter(lambda x: x['usage_category'] == 'model')
both_licenses = ds['train'].filter(lambda x: x['usage_category'] == 'both')

print(f"Found {len(dataset_licenses)} dataset-specific licenses")
print(f"Found {len(model_licenses)} model-specific licenses")
print(f"Found {len(both_licenses)} licenses used for both")
```

## Use Cases

- Training models to understand and classify license types
- Building license compliance tools for datasets and models
- License text analysis and comparison
- Filtering licenses by usage context (dataset vs model vs both)
- Educational resources about open-source licensing in AI/ML contexts
- Automated license compatibility checking for HuggingFace repositories

## Additional Information

### Licensing Information

The dataset compilation is released under CC0-1.0. Individual license texts retain their original terms and are included for informational and compliance purposes.

### Citation Information

If you use this dataset, please cite the SPDX project:

```
@misc{spdx,
  title = {SPDX License List},
  author = {The Linux Foundation},
  howpublished = {\url{https://spdx.org/licenses/}},
  year = {2024}
}
```

