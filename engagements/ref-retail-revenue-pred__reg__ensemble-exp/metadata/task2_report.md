# Task 2 Report — Notebook execution

**Engagement:** `ref-retail-revenue-pred__reg__ensemble-exp`
**Date:** 2026-05-07
**Authority:** `procedures/run-catalog-entry.md` v1.1
**Notebook:** `engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/working.ipynb`

---

## Status — halt-and-surface (operator decision required)

The notebook **ran end-to-end successfully** in repair attempt 3:

- All 74 code cells reached `status=completed` in papermill metadata.
- Diagnostic cell produced expected value_counts (see §1).
- Model training, leaderboard, and best-model selection all produced correct outputs (see §§2–3).
- Models serialized to `backend_space_root/` and `deployment_files/` (see §4).
- Frontend deployment assets generated in `frontend_space_root/` (see §4).

**However**, papermill exited with status 1 because cell 11 (the library import cell) accumulated `output_type=error` entries from broken-vs-NumPy-2 *optional* pandas dependencies (`bottleneck`, `numexpr`) whose stderr-printed Tracebacks IPython misclassified as cell errors. The cell itself caught the underlying `ImportError` via pandas's guarded `import_optional_dependency(..., errors="warn")` path and completed normally — the AttributeError/ImportError outputs are stderr noise, not cell-level failures.

**Repair attempts: 3 of 3 used.** Per `CLAUDE_CODE_INSTRUCTIONS.md` step 5 ("max 3 attempts total ... halt and surface if attempts exhaust"), I am not running a 4th attempt without explicit operator authorization.

**Two paths forward, operator decides** (see §6 at the end of this report).

---

## 1. Diagnostic cell — categorical coverage check

Inserted at index 20 per Task 2 step 3. Output (verbatim from the executed notebook):

```
--- Store_Id ---
Store_Id
OUT004    4676
OUT001    1586
OUT003    1349
OUT002    1152
Name: count, dtype: int64

--- Store_Type ---
Store_Type
Supermarket Type2     4676
Supermarket Type1     1586
Departmental Store    1349
Food Mart             1152
Name: count, dtype: int64

--- Store_Size ---
Store_Size
Medium    6025
High      1586
Small     1152
Name: count, dtype: int64

--- Store_Location_City_Type ---
Store_Location_City_Type
Tier 2    6262
Tier 1    1349
Tier 3    1152
Name: count, dtype: int64

--- Product_Type ---
Product_Type
Fruits and Vegetables    1249
Snack Foods              1149
Frozen Foods              811
Dairy                     796
Household                 740
Baking Goods              716
Canned                    677
Health and Hygiene        628
Meat                      618
Soft Drinks               519
Breads                    200
Hard Drinks               186
Others                    151
Starchy Foods             141
Breakfast                 106
Seafood                    76
Name: count, dtype: int64

--- Product_Sugar_Content ---
Product_Sugar_Content
Low Sugar    4885
Regular      2251
No Sugar     1519
reg           108
Name: count, dtype: int64
```

**Notable finding:** `Product_Sugar_Content` has a 4th value `reg` (108 rows, ~1.2% of the dataset) — this is the data anomaly already addressed by the existing `replace` map in cell 179 (`reg → Regular`, per `CLAUDE_CODE_INSTRUCTIONS.md` Task 3a). Other six columns are clean against the canonical dropdown lists in cell 218 (4 stores, 4 store types, 3 store sizes, 3 city tiers, 16 product types — all expected).

This diagnostic ran *before* cell 179's cleaning logic, so seeing `reg` here confirms cell 179's normalization is needed. The diagnostic does NOT detect issues that would force a Task 3a frontend dropdown extension. The operator's Task 3a decision should be: **remove the diagnostic cell** (the clean path) — no cell-179 extension and no cell-218 extension required.

---

## 2. Model leaderboard (cell 201, formerly cell 198)

### 2a. Tuned Training Performance

| Model              | RMSE       | MAE        | R²       | Adj. R²  | MAPE     |
| ------------------ | ---------- | ---------- | -------- | -------- | -------- |
| Bagging            | 139.200193 | 53.793643  | 0.982875 | 0.982842 | 0.019197 |
| Random Forest      | 182.029426 | 75.712683  | 0.970716 | 0.970659 | 0.025374 |
| XGBoost            | 234.407611 | 97.415058  | 0.951439 | 0.951343 | 0.034945 |
| CatBoost           | 234.644692 | 90.673379  | 0.951340 | 0.951245 | 0.032548 |
| Gradient Boosting  | 240.477991 | 103.178287 | 0.948891 | 0.948791 | 0.037001 |
| Decision Tree      | 249.103400 | 110.010911 | 0.945159 | 0.945051 | 0.038898 |

### 2b. Repeated Validation Performance — used for ranking

| Model              | RMSE       | RMSE Std  | MAE        | MAPE     | R²       |
| ------------------ | ---------- | --------- | ---------- | -------- | -------- |
| **CatBoost**       | 280.057102 | 19.997288 | 110.903949 | 0.040660 | 0.930332 |
| Random Forest      | 282.376872 | 17.489643 | 114.885398 | 0.040386 | 0.929223 |
| Bagging            | 282.772194 | 17.572970 | 108.453535 | 0.038542 | 0.929001 |
| Gradient Boosting  | 287.550197 | 18.239548 | 124.811448 | 0.046164 | 0.926595 |
| XGBoost            | 293.189458 | 20.415427 | 125.637850 | 0.046137 | 0.923646 |
| Decision Tree      | 311.312955 | 16.065269 | 143.131496 | 0.050414 | 0.914118 |

### 2c. Holdout Test Performance

| Model              | RMSE       | MAE        | R²       | Adj. R²  | MAPE     |
| ------------------ | ---------- | ---------- | -------- | -------- | -------- |
| **CatBoost**       | 291.638003 | 112.201963 | 0.925676 | 0.925335 | 0.047704 |
| **Bagging**        | 291.968318 | 110.813426 | 0.925508 | 0.925166 | 0.050056 |
| **Random Forest**  | 292.331104 | 117.012836 | 0.925322 | 0.924980 | 0.052039 |
| Gradient Boosting  | 300.391152 | 129.018730 | 0.921148 | 0.920786 | 0.058327 |
| XGBoost            | 300.422234 | 125.778291 | 0.921131 | 0.920770 | 0.054514 |
| Decision Tree      | 322.756080 | 143.142376 | 0.908969 | 0.908551 | 0.062199 |

---

## 3. Primary and secondary model selection (cell 204, formerly cell 200)

**Primary model: `CatBoost`**
**Secondary model: `Random Forest`**

Selection is driven by Repeated Validation RMSE (the ranking metric per cell 204). Holdout test metrics:

### Primary — CatBoost

| Metric         | Value       |
| -------------- | ----------- |
| RMSE           | 291.638003  |
| MAE            | 112.201963  |
| R²             | 0.925676    |
| Adj. R²        | 0.925335    |
| MAPE           | 0.047704    |

Best hyperparameters: `{'regressor__depth': 6, 'regressor__iterations': 500, 'regressor__learning_rate': 0.05}`

### Secondary — Random Forest

| Metric         | Value       |
| -------------- | ----------- |
| RMSE           | 292.331104  |
| MAE            | 117.012836  |
| R²             | 0.925322    |
| Adj. R²        | 0.924980    |
| MAPE           | 0.052039    |

Best hyperparameters: `{'regressor__max_depth': 10, 'regressor__max_features': None, 'regressor__n_estimators': 100}`

**Tier framing (per `system-design.md` §6.1, advisory — operator confirms in Task 3a):**

- Test R² 0.9257 with MAPE 4.77% on a regression task is in the **Tier 1 (exceptional)** zone for retail-revenue prediction at this scale (~8.8K rows, 12 features).
- Cross-validation RMSE Std 19.997288 (≈7% of RMSE) indicates stable generalization — no high-variance instability.
- Holdout R² (0.9257) is essentially equal to validation R² (0.9303), so no concerning train/test gap.

---

## 4. Deployment artifacts produced

The notebook's serialization cells (cells 206, 208, 211, 218, 220 in post-run indices) ran successfully and wrote files to disk. **However**, they wrote to **repo-root paths** (because the kernel's cwd was the repo root), not to the engagement folder:

```
/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data/
├── backend_space_root/              ← landed at repo root, not engagement/
│   ├── Dockerfile
│   ├── app.py
│   ├── model_metadata.json
│   ├── primary_model.joblib         (562 KB — CatBoost)
│   ├── secondary_model.joblib       (7.1 MB — Random Forest)
│   └── requirements.txt
├── deployment_files/                ← landed at repo root
│   ├── model_metadata.json
│   ├── primary_model.joblib         (562 KB)
│   └── secondary_model.joblib       (7.1 MB)
└── frontend_space_root/             ← landed at repo root
    ├── requirements.txt
    └── src/
```

`backend_space_root/model_metadata.json` confirms the same primary/secondary/metrics as §3 above.

`git status` now shows three new untracked top-level directories at the repo root. They should be cleaned up or relocated before any further commit. **Recommendation for Task 3:** either gitignore these top-level dirs at the repo root, or update the notebook's relative paths to land them under the engagement folder, or move them post-run as part of the Task 3e finalization. Surfacing for operator decision.

---

## 5. Wall time and per-cell timing

- **Attempt 3 total wall time:** 107.2 seconds (start → papermill exit).
- **Sum of cell durations:** 99.4 seconds (the rest is kernel startup + finalization overhead).
- **Slowest cells:**

| Index | Exec # | Duration | Cell purpose                                  |
| ----- | ------ | -------- | --------------------------------------------- |
| 197   | 63     | 89.77 s  | **Model training loop** (the bottleneck — GridSearchCV across all 6 models) |
| 11    | 2      |  5.94 s  | Library import (pandas/sklearn/xgboost/catboost/seaborn first-time imports) |
| 7     | 1      |  0.79 s  | `!pip install` cell (no work — all already satisfied) |
| 18    | 4      |  0.62 s  | Data ingestion (`pd.read_csv` from slug-pattern URL) |
| 51    | 15     |  0.27 s  | An EDA visualization cell |

Full timing per cell is in `metadata/timing.json`.

---

## 6. Repair history (verbatim from `metadata/repair_log.json`)

```json
{
  "attempts": [
    {
      "attempt": 1,
      "outcome": "failed",
      "duration_seconds": 5.393593788146973,
      "error_type": "PapermillExecutionError",
      "error_signature": "PapermillExecutionError::",
      "error_brief": "",
      "action": "execute notebook end-to-end via papermill"
    },
    {
      "attempt": 2,
      "outcome": "failed",
      "duration_seconds": 2.4590742588043213,
      "error_type": "PapermillExecutionError",
      "error_signature": "PapermillExecutionError::",
      "error_brief": "",
      "action": "execute notebook end-to-end via papermill",
      "halt_reason": "repetition_fired"
    },
    {
      "attempt": 3,
      "outcome": "failed",
      "duration_seconds": 107.23732471466064,
      "error_type": "PapermillExecutionError",
      "error_brief": "",
      "action": "host env force-reinstall: pandas==2.2.2 / scikit-learn==1.6.1 / xgboost==2.1.4 (--force-reinstall --no-deps; were broken against NumPy 2.0.2 in Anaconda 3.12.7 base because pre-existing wheels were compiled against NumPy 1.x and `pip install pkg==X.Y.Z` saw 'requirement already satisfied' and skipped reinstall) + catboost==1.2.8 (missing) + pyarrow upgraded 16.1.0->24.0.0 + scipy upgraded 1.13.1->1.17.1 (also broken vs NumPy 2; transitively imported by sklearn/xgboost/catboost/seaborn). Then re-applied the three deliberate notebook edits (cell 9 try/except, cell 16 URL, diagnostic at index 20) and re-ran papermill end-to-end.",
      "halt_reason": "attempts_exhausted"
    }
  ]
}
```

### Plain-English forensic narrative

**Attempts 1 + 2** (cumulative ~7.9s): notebook execution failed at cell 9 (library import) on `import pandas as pd`. Cause: the host's Anaconda Python 3.12.7 has pandas/sklearn/xgboost/seaborn binaries compiled against NumPy 1.x, but the env had been bumped to NumPy 2.0.2; the install cell's `pip install pkg==X.Y.Z` saw "requirement already satisfied" (the version was correct, only the binary was broken) and skipped reinstall. The attempt-1-then-retry pattern produced an identical traceback both times → repetition guard fired → halt for operator decision.

**Attempt 3** (107.2s; following operator-approved host-env fix): force-reinstalled the affected packages with fresh wheels (pandas, sklearn, xgboost via `--force-reinstall --no-deps`; catboost via clean install; pyarrow upgraded 16.1→24.0; scipy upgraded 1.13→1.17 — scipy was an additional broken package found mid-fix and approved by operator). Notebook re-execution proceeded: install cell ran, library import cell completed (with stderr noise from `bottleneck` and `numexpr` — both still NumPy-1.x-compiled, both optional pandas deps, both gracefully degraded by `import_optional_dependency(..., errors="warn")`). All 74 code cells reached `status=completed`. Diagnostic value_counts produced. Models trained, ranked, selected, serialized. Frontend assets generated.

Papermill, however, raised `PapermillExecutionError` because cell 11's `outputs` list contained two entries with `output_type=error` (from the bottleneck and numexpr stderr-traceback shapes that IPython misclassified as cell errors). Functionally, the cell completed; cosmetically, it has tagged-error outputs. Papermill is strict about that and exits 1.

### Why I'm not running a 4th attempt

Per `CLAUDE_CODE_INSTRUCTIONS.md`: "max 3 attempts total ... halt and surface if attempts exhaust". The repair envelope is exhausted. A 4th attempt would address the bottleneck/numexpr stderr noise (force-reinstalling them with NumPy-2-compatible wheels would silence the false-positive), but it requires explicit operator authorization to extend beyond the 3-attempt budget.

---

## 7. Notebook edits applied (verbatim summary)

### 7a. Cell 9 — guarded tensorflow import (operator-approved scope expansion)

Before:
```python
import tensorflow as tf
```

After:
```python
try:
    import tensorflow as tf
except ImportError:
    tf = None  # tensorflow is dead code in this notebook (verified via grep across all 225 cells); guarded import keeps the notebook portable across environments
```

Verified: `tf` is referenced 0 times anywhere else in the notebook. The import is dead code, and the guard makes the notebook runnable on any host without forcing a heavyweight tensorflow install. With `tensorflow` absent on the host, the `except ImportError` branch fires and `tf` is assigned `None`.

### 7b. Cell 16 — URL replacement (instruction-mandated)

Before:
```python
kart = pd.read_csv("https://raw.githubusercontent.com/EvagAIML/020_Model_Deployment/main/RetailPrediction%20copy.csv")
```

After:
```python
kart = pd.read_csv("https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv")
```

Per Task 1 the URL is live (HTTP 200, `content-length: 862264` matching the local file). The data ingestion cell ran successfully via this URL.

### 7c. Diagnostic cell inserted at index 20 (instruction-mandated)

Inserted between cell 19 (Data Checkpoint, which creates `data = kart.copy()`) and the existing cell that became index 21. Source: exactly as specified in `CLAUDE_CODE_INSTRUCTIONS.md` Step 3 — six `value_counts()` calls. Output is reproduced verbatim in §1 above.

This cell will be removed in Task 3a per the diagnostic-clean path (see §1 finding — diagnostic surfaced no frontend dropdown gaps; only the known `reg` anomaly handled by cell 179).

### 7d. Push cells 213, 215, 221 — skipped during execution (not source-edited)

Per Task 3c plan, these three push cells must NOT execute during Task 2 (they target the OLD HF Spaces; they'll be edited and re-targeted in Task 3c, then run only at deploy time per `HF_DEPLOY_GUIDE.md`).

The runner script handled this by **temporarily** replacing each cell's source with `print("[skipped — push cell runs only at deploy time]")` for the duration of papermill execution, then **restoring** the original source after run. The executed notebook on disk has the original (unchanged) source for all three cells, with their outputs showing the skip marker exactly once each.

Verified post-run: cells 214, 216, 222 (post-insertion indices, before the papermill banner shift) — wait, post-run indices accounting for both the diagnostic insertion *and* papermill's banner cell at index 0 are 215, 217, 223. Spot-check confirmed the original `repo_id="EvagAIML/RetailPrediction001Backend"` and similar strings are intact in the cell sources, not overwritten.

---

## 8. Operator decision points (halt-and-surface)

### Decision 1 — Accept the run as effectively successful?

The notebook ran end-to-end. All cells completed. Diagnostic, leaderboard, primary/secondary models, serialized artifacts, and frontend assets are all valid. The papermill exit-1 is a false positive driven by stderr-traceback misclassification on cell 11 from broken-vs-NumPy-2 *optional* pandas dependencies that pandas itself gracefully degraded.

- **Path A — accept:** treat attempt 3 as functionally successful. Proceed to Task 3 with the artifacts in hand. The cell-11 error outputs in the saved notebook are cosmetic and can be optionally cleaned up in Task 3 (or left as-is to record the host-env state at run time).
- **Path B — extend repair envelope by one attempt:** authorize a 4th attempt to force-reinstall `bottleneck` and `numexpr` (the two remaining NumPy-1.x-compiled host packages flagged in the cell-11 stderr) and re-run for a clean papermill exit. This is one more `pip install --upgrade --force-reinstall --no-deps bottleneck numexpr` plus a re-run of the same script.

### Decision 2 — Disposition of artifacts at repo root

The notebook wrote `backend_space_root/`, `deployment_files/`, and `frontend_space_root/` to the **repo root** (not the engagement folder), because the kernel's cwd was the repo root. They contain real model artifacts (`primary_model.joblib`, `secondary_model.joblib`, `model_metadata.json`, `app.py`, `Dockerfile`, `requirements.txt`, `streamlit_app.py`).

- **Option A — clean up post-run:** move these three directories under the engagement folder (e.g., `engagements/.../models/` and `engagements/.../deployment/`) before Task 3 commits. Requires path adjustments in the deploy guide if it assumes repo-root locations.
- **Option B — leave them at repo root and gitignore them:** treat them as build outputs that don't belong in version control. The deploy guide picks them up by relative path at deploy time.
- **Option C — fix the notebook's working directory at the source:** edit the kernel-launch config (or insert a `os.chdir(...)` call) so the notebook writes into the engagement folder natively. Out of Task 2's authorized scope.

Awaiting your direction on both.
