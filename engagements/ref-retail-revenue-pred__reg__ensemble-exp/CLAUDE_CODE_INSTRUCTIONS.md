# Claude Code instructions — `ref-retail-revenue-pred__reg__ensemble-exp`

**Authored:** 2026-05-07 (session 007)
**Authority:** `procedures/run-catalog-entry.md` v1.1 in `000-smb-consulting-system-private`
**Catalog entry slug (target):** `smb-retail-revenue-pred__reg__ensemble`
**Engagement slug:** `ref-retail-revenue-pred__reg__ensemble-exp`
**HF Space targets:**
- Backend: `EvagAIML/smb-retail-revenue-pred-backend`
- Frontend: `EvagAIML/smb-retail-revenue-pred-frontend`

---

## Context

This engagement migrates an existing v26 retail revenue prediction notebook into the consulting-system reference-data layout. The notebook predicts per-product-per-store revenue using product attributes (weight, sugar content, type, MRP, allocated area) and store attributes (size, location tier, type, age). It generates both a FastAPI backend and a Streamlit frontend with a NEW_STORE option for hypothetical store profiling.

Two existing live HuggingFace Spaces represent the *prior* deployment of this model:
- `https://huggingface.co/spaces/EvagAIML/RetailPrediction001Backend`
- `https://huggingface.co/spaces/EvagAIML/RetailPrediction001frontend`

This work prepares a fresh execution + redeploy under the consulting-system structure, with new Spaces named per the consulting-system slug convention (see HF Space targets above).

The actual HF deploy is in `HF_DEPLOY_GUIDE.md` (this folder), executed by the operator after Tasks 1–3 complete.

---

## What's already staged

**Engagement folder structure** has been created at `engagements/ref-retail-revenue-pred__reg__ensemble-exp/` with these subdirectories: `data/raw/`, `notebooks/`, `models/`, `deployment/`, `metadata/`. All empty (except this file and `HF_DEPLOY_GUIDE.md`).

**The v26 notebook** is being placed by the operator at `notebooks/working.ipynb`. If it isn't there when you start Task 2, halt and ask the operator.

**`.gitattributes` in reference-data** has been verified. CSVs are excluded from LFS — committing the dataset as raw bytes will work as expected and the slug-pattern URL on `raw.githubusercontent.com` will serve actual file contents.

**Keep-alive workflow file** has been pre-staged at `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml` (at the reference-data repo root). The file pings both the backend and frontend Spaces on a 12-hour schedule (8am and 8pm UTC) to prevent free-tier sleep. The file will sit dormant until committed; once committed and pushed, GitHub Actions will pick it up automatically. Task 3h covers committing it.

---

## Repos this work touches (read-write authorization)

This arc spans TWO repos, both of which the operator has authorized for read-write access in this session. Do not halt to ask permission for cross-repo file operations between these two paths:

- **`/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data`** (your declared project folder, primary scope) — Tasks 1, 2, 3a–3e, 3h. Most of the work happens here.

- **`/Users/eriksvagshenian/Desktop/000-smb-consulting-system-private`** (sibling repo, also authorized) — Tasks 3f (lessons-log append at `lessons/lessons.md`) and 3g (optional catalog entry at `catalog/v1.yaml`). Both are appends/edits to existing files, not new repo creation.

For cross-repo git operations, use `git -C /absolute/path/to/repo <command>` form. Each repo has its own remote and main branch; commits and pushes happen against each repo independently.

If you encounter an actual permission denial (not a confirmation prompt) when writing to system-private, that's a real problem — halt and surface. But proceed without prompting on the assumption that cross-repo access works, because it does.

---

## Task 1 — Migrate the dataset (do first, halt and report)

The v26 notebook currently reads its CSV from `https://raw.githubusercontent.com/EvagAIML/020_Model_Deployment/main/RetailPrediction%20copy.csv`. Per `procedures/run-catalog-entry.md` Step 9a and `system-design.md` §8.4, reference-build datasets must live in `000-smb-consulting-reference-data` under the engagement folder, not in arbitrary other repos.

Steps:

1. `cd` to `000-smb-consulting-reference-data`. Confirm the working tree is clean before starting (`git status`). NOTE: there will be untracked files in this commit from the pre-staged work (the engagement folder, the instructions, the deploy guide, the keep-alive workflow). That's expected — those will be committed across Tasks 1, 3e, and 3h as appropriate.

2. `curl -L "https://raw.githubusercontent.com/EvagAIML/020_Model_Deployment/main/RetailPrediction%20copy.csv" -o engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv`

3. Verify the download:
   - File size is reasonable (expected ~600KB-1MB for ~8,800 rows)
   - First line is a CSV header containing the 12 expected columns: `Product_Id`, `Product_Weight`, `Product_Sugar_Content`, `Product_Allocated_Area`, `Product_Type`, `Product_MRP`, `Store_Id`, `Store_Establishment_Year`, `Store_Size`, `Store_Location_City_Type`, `Store_Type`, `Product_Store_Sales_Total`
   - File is not an HTML error page (curl can silently return HTML for 404s)
   - File is not an LFS pointer (would be tiny, ~130 bytes, with content starting `version https://git-lfs.github.com/spec/v1`)

4. Confirm `.gitattributes` excludes `*.csv` from LFS. Run `git check-attr filter engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv` and confirm output does NOT include `lfs`.

5. `git add` the engagement folder (which includes the data file, this instructions file, the deploy guide, and the empty subdirectories). Commit with `Add engagement: ref-retail-revenue-pred__reg__ensemble-exp (data + scaffolding — Task 1 of 3)`. `git push origin main`.

   NOTE: do not yet commit the `.github/workflows/keep-alive-*.yml` file — that goes in Task 3h after the Spaces exist, so the workflow's first run isn't pinging nonexistent URLs.

6. After push, verify the slug-pattern URL is live:
   ```
   curl -sI "https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv"
   ```
   Expected: HTTP 200, `Content-Type: text/plain; charset=utf-8` (or similar), `Content-Length` matching the local file size.

7. **Halt and report.** Surface to the operator:
   - Local file size and the first 3 lines (sanity check)
   - The git-check-attr result
   - The curl HEAD result
   - Confirmation that the URL serves the actual file (not an LFS pointer or error page)

Do not proceed to Task 2 until the operator confirms Task 1 is clean.

---

## Task 2 — Update notebook to read from new URL, then execute

Steps:

1. Confirm `notebooks/working.ipynb` exists in the engagement folder. If it does not, halt and ask the operator to drop the v26 notebook there.

2. Open `working.ipynb`. Find cell 16 (the data ingestion cell — contains `pd.read_csv(...)` with the `020_Model_Deployment` URL). Replace the URL with:
   ```
   https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv
   ```
   The cell after edit should read approximately:
   ```python
   kart = pd.read_csv("https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv")
   ```

3. Insert a temporary diagnostic cell *immediately after cell 19* (the Data Checkpoint cell that creates the `data` working copy). The diagnostic prints categorical value counts for every column the frontend has dropdowns for. Use this exact source:
   ```python
   # ------------------------------
   # DIAGNOSTIC — CATEGORICAL COVERAGE CHECK
   # ------------------------------
   # Compares categorical values in the loaded data against the frontend's
   # dropdown options (cell 218). Any value that prints here but is not in
   # the corresponding frontend list is a missing dropdown option.
   # This cell is for verification only — remove before final commit.

   for col in [
       "Store_Id",
       "Store_Type",
       "Store_Size",
       "Store_Location_City_Type",
       "Product_Type",
       "Product_Sugar_Content",
   ]:
       print(f"--- {col} ---")
       print(data[col].value_counts())
       print()
   ```

4. Run the notebook end-to-end via Papermill. The notebook's install cell (cell 6) declares its own dependencies — use those. Capture per-cell wall times.

5. If any cell fails, run the §5.2 repair loop: max 3 attempts total, structured `repair_log.json` written to `metadata/repair_log.json`, halt and surface if attempts exhaust or repetition fires.

6. After successful execution, save the executed notebook back to `notebooks/working.ipynb`. Do NOT yet commit or rename to `executed.ipynb`.

7. **Halt and report.** Surface to the operator:
   - The diagnostic cell's value_counts output (all 6 columns)
   - The model leaderboard output (from cell 198, performance aggregation)
   - The selected primary and secondary models with their test-set metrics
   - Any repair attempts that fired
   - Total wall time

Do not proceed to Task 3 without explicit operator approval.

---

## Task 3 — Apply operator-directed cleanup, fix BACKEND_URL, finalize, commit keep-alive (held pending operator approval)

This task has multiple parts. The first is conditional on Task 2's findings. The remainder are required regardless of findings.

### Task 3a — Cleanup based on Task 2 diagnostic (conditional)

Depending on what the value_counts output surfaces:

- **If categorical values appear in the data that are NOT in the frontend's dropdown lists (cell 218):** the operator will direct one of two fixes:
  - Extend the cleaning logic in cell 179 (the `replace` map currently only handles `reg → Regular` for Sugar Content) to normalize the unexpected values into existing canonical labels
  - Add the values to the frontend's option lists in cell 218 (the `STORE_TYPE_OPTIONS` / `PRODUCT_TYPES` / `ALL_SUGAR_OPTIONS` / `CATEGORY_TO_SUGAR_CONTENT` / `CATEGORY_TO_PRODUCT_TYPES` constants)
- **If the diagnostic is clean:** remove the temporary diagnostic cell.
- **If the model lands in a definable tier per the four-tier framework** (`tier_1_exceptional` / `tier_2_strong` / `tier_3_below_target` / `tier_4_not_shippable` per `system-design.md` §6.1): operator may direct adding a tier verdict cell to the notebook.

### Task 3b — Fix the frontend's BACKEND_URL (REQUIRED)

The v26 notebook's cell 218 hardcodes the OLD backend URL:

```python
BACKEND_URL = "https://EvagAIML-RetailPrediction001Backend.hf.space/v1/predict"
```

Change this to point at the NEW backend Space (which the operator will create per `HF_DEPLOY_GUIDE.md`):

```python
BACKEND_URL = "https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/v1/predict"
```

### Task 3c — Fix the upload_folder repo_ids (REQUIRED)

Cell 215 (backend push) and the corresponding frontend push cell currently target the OLD HF Spaces. Update them to target the NEW Spaces:

- **Backend push (cell 215)**: change `repo_id="EvagAIML/RetailPrediction001Backend"` to `repo_id="EvagAIML/smb-retail-revenue-pred-backend"`. Also change `create_pr=True` to `create_pr=False` (direct push for new Spaces).
- **Frontend push** (cell after 218): change `repo_id` to `EvagAIML/smb-retail-revenue-pred-frontend`. Also `create_pr=False`.

Do NOT execute the push cells yet (cells 213, 215, and the frontend push). Those run when the operator deploys per `HF_DEPLOY_GUIDE.md`. Just update the `repo_id` strings.

### Task 3d — Re-execute deployment-asset cells (REQUIRED if Task 3a or 3b changed cell 218)

If cell 218 was modified in Task 3b (BACKEND_URL fix) or Task 3a (frontend dropdown additions), re-execute cell 218 to regenerate `frontend_space_root/src/streamlit_app.py` with the corrected source. The push cells in `HF_DEPLOY_GUIDE.md` rely on `frontend_space_root/` being current.

Verify the change took:
```bash
grep BACKEND_URL frontend_space_root/src/streamlit_app.py
```
Expected output: the new URL pointing at `smb-retail-revenue-pred-backend`.

### Task 3e — Finalize the engagement folder (REQUIRED)

Once Tasks 3a–3d are complete:

1. Rename `notebooks/working.ipynb` to `notebooks/executed.ipynb`
2. Write `metadata/timing.json` (per-cell wall times from Task 2)
3. Write `metadata/repair_log.json` (even if empty — `{"attempts": []}`)
4. Write `metadata/tier_receipt.json` if a tier was assigned in Task 3a
5. `git add` the engagement folder, `git commit -m "ref-retail-revenue-pred__reg__ensemble-exp: notebook executed and ready for deploy (Task 3 of 3)"`, `git push origin main`

### Task 3f — Append lessons-log entry (REQUIRED)

In `000-smb-consulting-system-private/lessons/lessons.md`, append an entry per `system-design.md` §15.3 capturing:
- What was migrated (the v26 notebook from `020_Model_Deployment` mirror)
- What surprised (anything from Task 2's diagnostic, any repair attempts, any tier-vs-expected-tier mismatch)
- What was changed in docs or catalog (likely nothing for this initial migration)
- What to watch for next time:
  - The `BACKEND_URL` coupling between frontend and backend Space names is a foot-gun — flag it
  - The `system-design.md` §5.3 keep-alive workflow location ("engagement folder") conflicts with how GitHub Actions actually loads workflows (only from repo-root `.github/workflows/`). The compromise used here (file at repo root, named with full engagement slug) preserves the per-engagement spirit. Worth a §5.3 doc update in a future session.

Commit the lessons entry on the system-private repo with `Lessons: ref-retail-revenue-pred migration to consulting-system structure`.

### Task 3g — Optional: catalog YAML entry

If the operator approves, draft a `catalog/v1.yaml` entry for `smb-retail-revenue-pred__reg__ensemble` mirroring the multi-cls entry's structure:
- `dependencies`, `quality_tiers`, `notebook_requirements`, `data_signal_dependencies`, `improvement_paths`, `calibration_runs` (with the receipt from this build)
- `deployment` block referencing the new HF Space names
- `deployment.keep_alive` block referencing the workflow path `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml`
- Status: `active`

This is optional — operator decides whether to commit it now or defer.

### Task 3h — Commit the keep-alive workflow (REQUIRED, do AFTER operator confirms Spaces are live per HF_DEPLOY_GUIDE.md)

The keep-alive workflow file has been pre-staged at `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml`. It pings both the backend and frontend Spaces on a 12-hour schedule (8am and 8pm UTC = 3am and 3pm CDT during DST).

**Important: do not commit this file until the operator confirms the new HF Spaces are live and responding (per `HF_DEPLOY_GUIDE.md` Steps 3 and 6).** If committed before the Spaces exist, the workflow's first cron run will fail with connection errors (Space URL doesn't resolve), which is harmless but creates noisy red checks in the GitHub Actions tab.

Once the operator gives the all-clear:

1. Verify the workflow file exists at `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml`. If it doesn't, halt — something happened to the pre-staged file.
2. `git add .github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml`
3. `git commit -m "Add keep-alive workflow for ref-retail-revenue-pred Spaces (Task 3h of 3)"`
4. `git push origin main`
5. After push, verify the workflow is loaded by GitHub Actions:
   - Open `https://github.com/EvagAIML/000-smb-consulting-reference-data/actions` in browser (operator does this)
   - Confirm the "keep-alive — ref-retail-revenue-pred__reg__ensemble-exp" workflow appears in the workflows list
   - Trigger a manual run via the "Run workflow" button (`workflow_dispatch` is enabled)
   - Confirm both ping steps complete with HTTP 200 from both Spaces

If the manual run succeeds, the keep-alive is live and will fire on schedule. Report this back to the operator.

---

## What the operator (Erik) is doing in parallel

The operator (working with Claude.ai in the conversation that authored these instructions) will, while you execute Tasks 1–2:

- Verify the slug-pattern URL is live (after Task 1's push) by reading the local committed file via filesystem MCP
- Pre-stage the cell 16 URL change as a `str_replace` patch the operator can sanity-check
- Once Task 2 completes, read the executed notebook from `notebooks/working.ipynb` directly and:
  - Compare the diagnostic output against cell 218's dropdown lists, identifying any gaps precisely
  - Read the model evaluation outputs and recommend a tier verdict
  - Recommend whether each gap should be fixed in cleaning (cell 179) or frontend (cell 218)

That analysis is what the operator will use to direct Task 3a.

After Task 3 completes (excluding Task 3h, which waits), the operator runs the deploy per `HF_DEPLOY_GUIDE.md`. Once Spaces are confirmed live, Task 3h fires.

---

## Halt-and-surface protocol

Per `procedures/run-catalog-entry.md` §"Failure modes the procedure must handle gracefully": surface to the operator before proceeding if any of the following:

- Dataset URL returns 404 or wrong content type
- File appears as an LFS pointer instead of raw bytes
- Notebook execution fails on cells outside the §5.2 repair loop's reachable scope (install cell, runtime config, data loading)
- Repair loop exhausts 3 attempts
- Pass-2-style orphan placeholders are encountered (this notebook is pre-Pass-1/Pass-2-pattern, so no placeholder tokens are expected — but if any appear, halt)
- The pre-staged keep-alive workflow file at `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml` is missing when Task 3h is reached
- The operator has not approved a step that requires approval

When halting, write the relevant context to a markdown file in this engagement folder (e.g., `metadata/halt_task1_url_404.md`) so the operator can read it and respond.

---

## What this work is NOT

- Not the actual deploy to HuggingFace. That's `HF_DEPLOY_GUIDE.md`, executed by the operator.
- Not a re-author of the notebook to current style standards. That cleanup (Value Proposition cell, banner comments, expanded executive summary in the canonical pattern, lessons-log integration in the notebook itself) is separate work for a future session.
- Not the construction of a `catalog/v1.yaml` entry. That's optional in Task 3g.

---

*End of instructions.*
