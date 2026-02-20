# SPDX License Exceptions

SPDX license exceptions are queried and used almost the same way as licenses: there is a dedicated exceptions index plus JSON data you can fetch for use in `WITH` expressions.

---

## 1. Where to Get the List

| Resource | URL |
|----------|-----|
| Human‑readable index (HTML) | `https://spdx.org/licenses/exceptions-index.html` — lists all current exceptions with full names and short identifiers like `Classpath-exception-2.0`, `GCC-exception-2.0`, etc. |
| Exceptions JSON (license-list-data) | `https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json` — master list of all exception IDs and metadata |
| Per-exception detail | `https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions/{ID}.json` — full text and metadata for each exception |

**References:**
- [SPDX License List spec](https://spdx.github.io/spdx-spec/v2.3/SPDX-license-list/)
- [spdx-exceptions.json](https://github.com/jslicense/spdx-exceptions.json) (Node) — exports an array of exception IDs for validation/autocomplete

---

## 2. Programmatic Access Pattern

Mirror the license workflow:

1. **Fetch the exceptions list** from `license-list-data`:
   ```
   https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions.json
   ```

2. **Per-exception entry** includes:
   - **Short identifier** (e.g. `Classpath-exception-2.0`)
   - **Full name** (e.g. "Classpath exception 2.0")
   - **Canonical URL** (e.g. `https://spdx.org/licenses/Classpath-exception-2.0.html`)
   - **detailsUrl** — pointer to the detail JSON

3. **Fetch exception detail** from:
   ```
   https://raw.githubusercontent.com/spdx/license-list-data/main/json/exceptions/{ID}.json
   ```

4. **Detail JSON fields**:
   - `licenseExceptionId` — short identifier
   - `name` — full name
   - `licenseExceptionText` — vetted exception text
   - `licenseComments` — notes
   - `seeAlso` — reference URLs
   - `licenseExceptionTemplate` — template with optional/replaceable markup
   - `exceptionTextHtml` — HTML version

---

## 3. How It's Used in Expressions

Exceptions appear after `WITH` in SPDX license expressions:

| Expression | Meaning |
|------------|---------|
| `GPL-2.0-only WITH Classpath-exception-2.0` | GPL-2.0-only plus the Classpath exception |
| `GPL-3.0-or-later WITH GCC-exception-3.1` | GPL-3.0-or-later plus the GCC exception |

**Workflow:**
1. Retrieve the list of valid exception IDs and metadata
2. Validate exception IDs when they appear after `WITH` in SPDX expressions
3. The actual exception semantics are in the text at the SPDX HTML page for that exception

---

## 4. Building an Exceptions Dataset

The `build_spdx_exceptions.py` script fetches all exceptions from `license-list-data` and produces a dataset with the same structure as the licenses dataset:

- `exception_id` — short identifier (e.g. `Classpath-exception-2.0`)
- `exception_name` — full name
- `full_text` — exception text
- `source_url` — `https://spdx.org/licenses/{ID}.html`
- `page_markdown` — self-contained markdown document

Run:
```bash
python build_spdx_exceptions.py
python build_spdx_exceptions.py --push --repo midah/hf-dataset-licenses-exceptions
```
