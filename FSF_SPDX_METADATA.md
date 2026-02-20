# FSF Metadata API and SPDX License Classification

This document describes how the dataset uses the Free Software Foundation (FSF) metadata API to enrich SPDX licenses with GPL compatibility and freedom classifications.

---

## What FSF / "GPL Compatibility" Means

You can query a small JSON API, keyed by SPDX ID, to learn whether the FSF classifies that license as GPL‑compatible (and more generally, free / non‑free, etc.) via tags like `gpl-2-compatible`, `gpl-3-compatible`, and `libre`.

**Source:** [github.com/spdx/fsf-api](https://github.com/spdx/fsf-api)

---

## How the FSF Metadata API Works

The SPDX `fsf-api` repo exposes FSF license metadata at these URLs:

| Resource | URL |
|----------|-----|
| All FSF licenses (IDs only) | `https://spdx.github.io/fsf-api/licenses.json` |
| Full metadata for all licenses | `https://spdx.github.io/fsf-api/licenses-full.json` |
| One license by FSF ID | `https://spdx.github.io/fsf-api/{id}.json` (e.g. `Expat.json`) |
| **One license by SPDX ID** | `https://spdx.github.io/fsf-api/spdx/{SPDX_ID}.json` (e.g. `MIT.json`) |

### License JSON Structure

Each license JSON object includes:

- **`name`**: Human‑readable license name
- **`uris`**: Array of URLs the FSF associates with this license
- **`tags`**: Array of FSF categories, including:
  - `gpl-2-compatible`, `gpl-3-compatible` (GPL compatibility)
  - `libre` (free license)
  - `non-free`, `viewpoint`, `fdl-compatible`, etc.
- **`identifiers.spdx`**: Array of mapped SPDX IDs (first entry is the closest match)

**FSF license list:** [gnu.org/licenses/license-list.en.html](https://www.gnu.org/licenses/license-list.en.html)

---

## Using It in Practice (SPDX → FSF → GPL‑compat)

Workflow:

1. Start from an SPDX ID (e.g. `GPL-2.0-only`, `MIT`).
2. Fetch `https://spdx.github.io/fsf-api/spdx/{ID}.json`.
3. Inspect `tags` to determine compatibility and "free" status.

### Example (Python)

```python
import requests

def fsf_metadata_for_spdx(spdx_id: str) -> dict | None:
    url = f"https://spdx.github.io/fsf-api/spdx/{spdx_id}.json"
    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None
    return r.json()

def gpl_compatibility(spdx_id: str) -> str | None:
    data = fsf_metadata_for_spdx(spdx_id)
    if not data:
        return None
    tags = set(data.get("tags", []))
    if "gpl-3-compatible" in tags and "gpl-2-compatible" in tags:
        return "GPL-2 and GPL-3 compatible"
    if "gpl-3-compatible" in tags:
        return "GPL-3 compatible only"
    if "gpl-2-compatible" in tags:
        return "GPL-2 compatible only"
    if "non-free" in tags:
        return "Non-free (not GPL-compatible)"
    if "libre" in tags:
        return "Free but not marked GPL-compatible"
    return "Unknown / not classified"
```

This gives you an API‑driven way to enrich SPDX IDs with FSF views on GPL compatibility and freedom status without hard‑coding your own mapping.

---

## What an SPDX License Entry Contains

Each license on the SPDX License List has, at minimum:

- **Short identifier**: Unique machine‑readable ID like `Apache-2.0`, `MIT`, or `xpp`
- **Full name**: Human‑readable license name, e.g. "XPP License"
- **Vetted license text**: Canonical license text (with markup for optional/replaceable sections where relevant)
- **Canonical URL**: Permanent URL under `https://spdx.org/licenses/ID.html`

Additional metadata commonly present:

- Whether the license is OSI‑approved (`isOsiApproved`)
- Whether it is FSF "free" or "GPL‑compatible" (via FSF API)
- List version when added (`listVersionAdded`), deprecation info
- Cross‑reference URLs (`crossRef`)

**SPDX License List:** [spdx.github.io/spdx-spec/v2.3/SPDX-license-list/](https://spdx.github.io/spdx-spec/v2.3/SPDX-license-list/)

---

## Interpretation Summary

Using the FSF metadata API means: you do not infer compatibility yourself; you read the FSF's own tagging from that JSON and interpret those tags in your tooling. For a given SPDX ID:

1. Request: `https://spdx.github.io/fsf-api/spdx/{SPDX_ID}.json`
2. The response has a `tags` array with entries like `gpl-2-compatible`, `gpl-3-compatible`, `libre`, or `non-free`
3. Use those tags to drive your license classification logic

---

## Dataset Columns Added

The build script enriches each license with:

| Column | Description |
|--------|-------------|
| `fsf_tags` | JSON array of FSF tags (e.g. `["gpl-2-compatible","gpl-3-compatible","libre"]`) or `null` if not in FSF API |
| `fsf_gpl_compatibility` | Human-readable summary (e.g. "GPL-2 and GPL-3 compatible", "Non-free (not GPL-compatible)") or `null` |

The `page_markdown` field also includes an **FSF Classification** section when FSF data is available.
