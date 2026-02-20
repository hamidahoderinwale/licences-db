"""
Build a Hugging Face dataset of SPDX license exceptions from the SPDX License List.

Exceptions are used in WITH expressions: e.g. GPL-2.0-only WITH Classpath-exception-2.0

Usage:
    pip install datasets requests
    python build_spdx_exceptions.py
    python build_spdx_exceptions.py --push --repo midah/hf-dataset-licenses-exceptions

See SPDX_EXCEPTIONS.md for documentation.
"""

import json
import requests
from datasets import Dataset

SPDX_EXCEPTIONS_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json"
SPDX_EXCEPTION_DETAIL_BASE = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions/"


def fetch_exceptions_list():
    """Fetch the master list of all SPDX exceptions."""
    print("Fetching SPDX exceptions list...")
    resp = requests.get(SPDX_EXCEPTIONS_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    exceptions = data.get("exceptions", [])
    print(f"Found {len(exceptions)} exceptions.")
    return exceptions


def fetch_exception_detail(exception_id: str) -> dict:
    """Fetch the full detail JSON for a single exception."""
    url = f"{SPDX_EXCEPTION_DETAIL_BASE}{exception_id}.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Warning: Could not fetch {exception_id}: {e}")
        return {}


def build_page_markdown(exc: dict, source_url: str) -> str:
    """Build a self-contained markdown document for the exception."""
    if not exc:
        return ""

    exc_id = exc.get("licenseExceptionId", "")
    name = exc.get("name", "")
    text = exc.get("licenseExceptionText", "")
    comment = exc.get("licenseComments", "")
    see_also = exc.get("seeAlso", [])

    sections = []
    sections.append(f"# {name}\n")
    sections.append(f"**SPDX Exception ID:** `{exc_id}`\n")
    sections.append(f"**Source:** {source_url}\n")
    sections.append("\n**Used in expressions:** `LICENSE WITH {id}`\n".format(id=exc_id))

    if comment:
        sections.append("## Notes\n\n")
        sections.append(f"{comment}\n")

    sections.append("## Exception Text\n\n")
    sections.append("```\n")
    sections.append(text.strip())
    sections.append("\n```\n")

    if see_also:
        sections.append("## References\n\n")
        for url in see_also[:10]:
            sections.append(f"- {url}\n")

    return "".join(sections)


def build_dataset(push_to_hub: bool = False, hub_repo: str = None, sample: int = None):
    """Build the exceptions dataset."""
    exceptions = fetch_exceptions_list()
    if sample is not None:
        exceptions = exceptions[:sample]
        print(f"  (Sampling first {sample} exceptions)")

    rows = []
    for i, exc in enumerate(exceptions):
        exc_id = exc.get("licenseExceptionId", "")
        print(f"  [{i+1}/{len(exceptions)}] Fetching {exc_id}...")

        source_url = exc.get("reference", f"https://spdx.org/licenses/{exc_id}.html")
        detail = fetch_exception_detail(exc_id)
        full_text = detail.get("licenseExceptionText", "") if detail else ""
        page_markdown = build_page_markdown(detail, source_url) if detail else ""

        rows.append({
            "exception_id": exc_id,
            "exception_name": exc.get("name", ""),
            "full_text": full_text,
            "source_url": source_url,
            "page_markdown": page_markdown,
            "is_deprecated": exc.get("isDeprecatedLicenseId", False),
        })

    ds = Dataset.from_list(rows)
    print(f"\nDataset built: {len(ds)} exceptions")
    print(ds)

    ds.save_to_disk("spdx_exceptions_dataset")
    ds.to_parquet("spdx_exceptions_dataset.parquet")
    ds.to_csv("spdx_exceptions_dataset.csv")
    print("Saved to: spdx_exceptions_dataset/, .parquet, .csv")

    if push_to_hub and hub_repo:
        ds.push_to_hub(hub_repo)
        print(f"Pushed to: https://huggingface.co/datasets/{hub_repo}")

    return ds


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build SPDX exceptions dataset")
    parser.add_argument("--push", action="store_true", help="Push to HF Hub after building")
    parser.add_argument("--repo", type=str, default="midah/hf-dataset-licenses-exceptions", help="HF repo")
    parser.add_argument("--sample", type=int, default=None, help="Process only N exceptions (for testing)")
    args = parser.parse_args()

    build_dataset(push_to_hub=args.push, hub_repo=args.repo, sample=args.sample)
