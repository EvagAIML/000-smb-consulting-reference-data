# Colab-authored notebook audit

**Subject:** [`engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/colab_authored.ipynb`](engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/colab_authored.ipynb)
**Auditor:** Claude Code, read-only inspection
**Date:** 2026-05-07
**Scope:** Findings only — no changes to the notebook were made.
**References:**

- [`notebook-style-guide.md` v2.1](~/Desktop/000-smb-consulting-system-private/notebook-style-guide.md)
- [`system-design.md` v2.2](~/Desktop/000-smb-consulting-system-private/system-design.md) §6.1, §12.7
- Canonical reference notebook (used-car): [`engagements/ref-used-car-price__reg__autogluon-exp/notebooks/executed.ipynb`](engagements/ref-used-car-price__reg__autogluon-exp/notebooks/executed.ipynb)
- v26 retail notebook (substance baseline): [`engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/executed.ipynb`](engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/executed.ipynb)
- Sibling app source: [`backend_app.py`](engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/backend_app.py), [`frontend_streamlit_app.py`](engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/frontend_streamlit_app.py)

**Notebook overview:** 60 cells (29 markdown + 31 code), Python 3.12 kernel. All code cells parse cleanly via `ast.parse`. Title section + Executive Summary + Code Execution divider + body alternating markdown/code + Expanded Executive Summary at end.

---

## Summary

| Result | Count |
| --- | ---: |
| PASS | 33 |
| NOTE | 1 |
| FAIL | 0 |
| Total | 34 |

The notebook is **substantially compliant** with all four standards (style guide v2.1, v26 substance preservation, Colab compatibility, code/deployment correctness). One NOTE worth surfacing (C5) — minor and Colab-environment-specific.

---

## A. Style guide compliance (notebook-style-guide.md v2.1)

| # | Verdict | Justification |
| --- | --- | --- |
| **A1** | **PASS** | Cell 0: `# **Retail Revenue Prediction**: Supervised Tabular Regression with Six-Model Ensemble` — matches the `# **Use Case Name**: Problem Type Description` pattern. |
| **A2** | **PASS** | Cell 1 opens with "In order to help multi-location food and beverage retailers reduce profit leakage from demand variability at the product–store level, a six-model regression ensemble was developed across 8,763 product–store sales records..." |
| **A3** | **PASS** | Cell 2 has `### **Business Opportunities**` with three lettered items A/B/C (each pairing the opportunity statement with its narrative solution in a single paragraph), `### **Outcomes**` with primary metrics and tier framing, and `### **Live Deployment**` with three blockquoted links. Pattern matches the canonical used-car notebook (which uses the same A/B/C-narrative-only structure rather than explicit "Solution:" sub-labels). |
| **A4** | **PASS** | Cell 4 markdown contains `# **Code Execution**` (the divider). |
| **A5** | **PASS** | Cell 5 has `### **Runtime Configuration**` with blockquote specifying `**Hardware Accelerator:** **CPU**` and `**RAM:** **Standard**`, plus a runtime expectation note ("8–15 minutes on standard Colab CPU runtime"). |
| **A6** | **PASS** | Cell 7 contains an HTML `<div>` with `border: 2px solid #d32f2f`, light-pink background `#ffebee`, "⚠ Runtime Restart Required" header, and the "Restart the Colab runtime via *Runtime → Restart Session*" message. Wrapped in `if installed_anything:` so it only renders when packages were actually installed. |
| **A7** | **PASS** | Every body markdown cell (10, 12, 14, 16, 18, 21, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 45, 47, 49, 51, 53, 55, 57) has both `**Summary:**` and `**Observations:**` blocks. Cell 38 uses an extended bulleted Observations format (definitions of RMSE/MAE/R²/MAPE) which is appropriate for the technical model-comparison surface; the labels are still present. |
| **A8** | **PASS** | All 31 code cells start with the canonical 30-dash banner (`# ------------------------------\n# SECTION TITLE\n# ------------------------------\n# Plain-English description...`). Verified programmatically. |
| **A9** | **PASS** | Every import statement carries an inline comment. Single-name imports use per-line comments (e.g., `import os # filesystem checks for...`); grouped imports (e.g., `from sklearn.ensemble import (BaggingRegressor, GradientBoostingRegressor, RandomForestRegressor,)`) put the comment on the `from` line ("# ensemble regressors"). The grouped-import pattern matches the canonical used-car notebook's style. |
| **A10** | **PASS** | Customer-facing surfaces (cell 1 Value Proposition, cell 2 Outcomes) lead with translation, metric in parentheses ("a typical revenue forecast for a product–store row is within about ₹112 of the actual"). Technical surfaces (cell 38 model comparison, cell 43 test-set print, cell 46 business alignment) lead with metric, then short trailing translation. Both forms per §12.7. |
| **A11** | **PASS** | Cell 59 has `## **Expanded Executive Summary**` with `### **TL;DR**` (5-sentence punchline incl. tier verdict) and `### **Full Summary**` containing four `####`-level subsections (Objective / Data and Preparation / Iterative Development / Model Selection / Deployment Readiness / Limitations and Honest Framing). |
| **A12** | **PASS** | Cell 50 reads FastAPI app source from sibling `backend_app.py`; cell 52 reads Streamlit source from sibling `frontend_streamlit_app.py`. No embedded heredoc strings inside notebook cells — explicit `FileNotFoundError` guard if siblings are missing, citing the v0 lessons-log entry on the Prophet build. |

---

## B. Substance preservation (vs. v26 retail notebook)

| # | Verdict | Justification |
| --- | --- | --- |
| **B1** | **PASS** | Cell 33 defines all six v26 models: `Decision Tree` (DecisionTreeRegressor), `Bagging` (BaggingRegressor), `Random Forest` (RandomForestRegressor), `Gradient Boosting` (GradientBoostingRegressor), `XGBoost` (XGBRegressor), `CatBoost` (CatBoostRegressor). Verified the same six classes are imported in v26 cell 9. |
| **B2** | **PASS** | `evaluate_model` in cell 35 wraps each model in `GridSearchCV(..., cv=SEARCH_CV=5, scoring="neg_root_mean_squared_error")` with model-specific param_grids defined in cell 33. Each of the six models has its own grid covering depth, learning_rate, n_estimators, etc. |
| **B3** | **PASS** | Cell 9 defines `REPEATED_VALIDATION_CV = RepeatedKFold(n_splits=5, n_repeats=2, random_state=RANDOM_STATE)`; cell 35's `evaluate_model` runs `cross_validate(best_model, X_train, y_train, cv=REPEATED_VALIDATION_CV, ...)` per model. |
| **B4** | **PASS** | Cell 35 computes `tuned_test_metrics = get_metrics(y_test, best_model.predict(X_test), "Test", feature_count)` for each model. Cell 39 aggregates per-model holdout test metrics into `test_perf_df`. Cell 43 reports the primary model's holdout test metrics with full plain-English block. |
| **B5** | **PASS** | Two-Space architecture preserved: backend cells 50 (asset staging from `backend_app.py` + Dockerfile + `python:3.12-slim`) and 56 (push to `EvagAIML/smb-retail-revenue-pred-backend`); frontend cells 52 (asset staging from `frontend_streamlit_app.py` + placeholder substitution) and 58 (push to `EvagAIML/smb-retail-revenue-pred-frontend`). FastAPI + Streamlit roles match v26 deployment. |
| **B6** | **PASS** | Currency tally across all 60 cells: `₹` (INR) appears 15 times; `INR` appears 14 times; `USD` appears 0 times; `$` literal appears 0 times. The target column comment in cell 3 explicitly identifies revenue as "Total revenue (INR)". No premature or accidental USD conversion anywhere. |
| **B7** | **PASS** | Cell 27 applies all four v26 feature-engineering transformations: (1) `data["Product_Sugar_Content"].replace({"reg": "Regular"})` resolves the 108-row data-entry variant; (2) `data["Product_Id_char"] = data["Product_Id"].str[:2]` extracts the two-letter product-family prefix; (3) `data["Store_Age_Years"] = 2025 - data["Store_Establishment_Year"]`; (4) `data["Product_Type_Category"] = ...` derives Perishables/Non Perishables flag. Drops `Product_Id` and `Store_Establishment_Year`; retains `Store_Id` (per the EDA's per-store revenue justification). |
| **B8** | **PASS** | Cell 9: `RANDOM_STATE = 1`, `HOLDOUT_TEST_SIZE = 0.30`. Cell 29 calls `train_test_split(X, y, test_size=HOLDOUT_TEST_SIZE, random_state=RANDOM_STATE, shuffle=True)`. v26 cell 182 uses identical `HOLDOUT_TEST_SIZE = 0.30, HOLDOUT_RANDOM_STATE = 1`. Match. |

---

## C. Colab compatibility

| # | Verdict | Justification |
| --- | --- | --- |
| **C1** | **PASS** | Programmatic scan for `/Users/`, `/opt/anaconda`, `/home/`, `C:\\`, `/tmp/`, `eriksvagshenian`: zero matches across all 60 cells. All paths are relative (e.g., `Path("backend_space_root")`, `Path("backend_app.py")`). |
| **C2** | **PASS** | Cell 11 builds the URL as `f"{DATA_REPO_BASE}/engagements/{ENGAGEMENT_SLUG}/data/raw/retail_prediction.csv"` where `DATA_REPO_BASE = "https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main"` — exactly the slug pattern declared in style guide §"Data Loading Pattern". |
| **C3** | **PASS** | No `try: import X; except ImportError:` patterns guarding missing-locally packages anywhere in the notebook. The only `try/except` around imports is in cell 7's install-detection loop (using `importlib.import_module` to decide whether `pip install` is needed) — this is the install-cell pattern, not a dead-code guard. No `import tensorflow as tf` or similar in the notebook. |
| **C4** | **PASS** | Cell 7 implements the `importlib`-based detection pattern: iterates over a `REQUIRED_PACKAGES` list of `(module_name, pip_spec)` tuples, attempts `importlib.import_module(module_name)`, only invokes `subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pip_spec])` for missing packages. Sets `installed_anything = True` and conditionally renders the restart banner. No naked `!pip install` lines. |
| **C5** | **NOTE** | Cells 39 and 41 call `display(...)` directly without an explicit `from IPython.display import display` statement in those cells (or at the top of the notebook in the imports cell). This works in Colab and Jupyter because IPython kernels auto-inject `display` into the user namespace as a builtin. It does **not** work if someone tries to run the notebook code in plain `python` (e.g., via Papermill kernel that doesn't add IPython builtins, or via `jupyter nbconvert --to script` then `python script.py`). For Colab-target authoring, this is fine; flagging in case the notebook is ever re-run via a non-IPython execution path. The IPython.display import at cell 7 is local to the install banner block (`from IPython.display import HTML, display` inside the `if installed_anything:` branch), so its scope doesn't carry to cells 39/41. |

---

## D. Code correctness

| # | Verdict | Justification |
| --- | --- | --- |
| **D1** | **PASS** | All 31 code cells parse cleanly via `ast.parse`. Verified programmatically — zero `SyntaxError`. |
| **D2** | **PASS** | `PRIMARY_MODEL_LABEL` is defined in cell 41 (after model selection: `PRIMARY_MODEL_LABEL = MODEL_DISPLAY_LABELS[primary_model_name]`). It is referenced in cells 43, 44, 48, 52, 56 — all after cell 41. Same ordering for `SECONDARY_MODEL_LABEL`. `ENGAGEMENT_SLUG` defined in cell 11, used in cells 48, 56, 58 — all later. `primary_model_name` / `secondary_model_name` defined cell 41, used cells 43, 48 — later. |
| **D3** | **PASS** | Cell 48 writes `model_metadata.json` with keys `primary_model_name`, `secondary_model_name`, `primary_label`, `secondary_label`, `primary_holdout_metrics`, `secondary_holdout_metrics`, `tier_verdict`, `tier_receipt`, `engagement_slug`. `backend_app.py` lines 25–29 read `METADATA = json.load(...)` and access `METADATA["primary_label"]` and `METADATA["secondary_label"]`. The two keys the backend reads are present in the notebook's write schema. |
| **D4** | **PASS** | `frontend_streamlit_app.py` lines 25–26 contain `PRIMARY_LABEL = "__PRIMARY_LABEL__"` and `SECONDARY_LABEL = "__SECONDARY_LABEL__"` placeholder tokens. Cell 52 reads the file with `FRONTEND_APP_SOURCE_PATH.read_text()`, then runs `frontend_source.replace("__PRIMARY_LABEL__", PRIMARY_MODEL_LABEL)` and `.replace("__SECONDARY_LABEL__", SECONDARY_MODEL_LABEL)` before writing to `frontend_root / "src" / "streamlit_app.py"`. |

---

## E. Deployment correctness

| # | Verdict | Justification |
| --- | --- | --- |
| **E1** | **PASS** | Cell 56: `BACKEND_REPO_ID = "EvagAIML/smb-retail-revenue-pred-backend"` passed to `upload_folder(repo_id=BACKEND_REPO_ID, ...)`. |
| **E2** | **PASS** | Cell 58: `FRONTEND_REPO_ID = "EvagAIML/smb-retail-revenue-pred-frontend"` passed to `upload_folder(repo_id=FRONTEND_REPO_ID, ...)`. |
| **E3** | **PASS** | `frontend_streamlit_app.py` line 22: `BACKEND_URL = "https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/v1/predict"` — points at the correct backend Space's `/v1/predict` endpoint. |
| **E4** | **PASS** | Cell 50 writes the backend `requirements.txt` containing `fastapi==0.111.0`, `uvicorn==0.30.1`, `scikit-learn==1.6.1`, `joblib==1.4.2`, `pandas==2.2.2`, `numpy==2.0.2`, `xgboost==2.1.4`, `catboost==1.2.8`. Notebook's `REQUIRED_PACKAGES` (cell 7) has the same versions for the inference-relevant subset (numpy, pandas, sklearn, xgboost, catboost, joblib). FastAPI/uvicorn are deployment-only and not in the notebook's REQUIRED_PACKAGES (correct — the notebook training kernel doesn't need them). |
| **E5** | **PASS** | Cell 50 Dockerfile content: `FROM python:3.12-slim`, `WORKDIR /app`, copies `requirements.txt`, runs `pip install -r requirements.txt`, copies app contents, `CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]`. Port 7860 (HF Spaces convention) and Python 3.12 confirmed. |

---

## Recommended-fix queue

**Zero FAIL items.** No mandatory fixes required for the notebook to satisfy the audit's pass criteria.

**One NOTE item** the operator may consider addressing (operator's call):

- **C5** — Add `from IPython.display import display` to cell 9 (the imports cell), so cells 39 and 41's `display(...)` calls are robust against non-IPython execution paths. This is a one-line addition that costs nothing in the Colab-target case and protects against silent breakage if someone runs the notebook through Papermill on a kernel without IPython builtins, or extracts the Python via `nbconvert --to script` for offline execution. Trade-off: makes the notebook slightly more conservative; minor stylistic departure from the canonical used-car notebook (which doesn't use `display(...)` at all and so doesn't need the import).

No other findings rise to the level of a recommended fix. The two style choices the audit examined (A3 paired-Solutions presence and A9 grouped-import comment scope) both match the canonical used-car notebook's actual practice and so are accepted as in-spec.

---

*End of audit report.*
