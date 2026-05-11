# Claude Code prompt — build backend + frontend for `hill_country_grocer__reg__ensemble`

**Do not run this prompt until Colab execution of `hill_country_grocer__reg__ensemble.ipynb` has completed and the operator has confirmed model metrics landed in the target band (R² 0.85–0.95, MAPE 8–15%).** This task assumes the six serialized model artifacts and the `model_registry.json` exist on disk in the engagement's `models/` directory.

You are building the deployment layer (FastAPI backend + Streamlit frontend) for the Hill Country Grocer revenue prediction model. The engagement is `ref-retail-revenue-pred__reg__ensemble-exp` in repo `000-smb-consulting-reference-data`. Your working directory is `/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data`.

## Context

The model is a six-candidate ensemble trained on a 16-column Hill Country Grocer weekly sales panel. `Weekly_Units_Sold` was dropped from features to avoid target leakage. The trained artifacts live at:

```
engagements/ref-retail-revenue-pred__reg__ensemble-exp/models/
  decision-tree__hill-country-grocer.joblib
  bagging__hill-country-grocer.joblib
  random-forest__hill-country-grocer.joblib
  gradient-boosting__hill-country-grocer.joblib
  xgboost__hill-country-grocer.joblib
  catboost__hill-country-grocer.joblib
  preprocessor__hill-country-grocer.joblib
  model_registry.json
```

`model_registry.json` is the source of truth for which models exist, their display names, their metrics, and which one was flagged as primary at training time.

The prior generation of this engagement has two `.py` files in the `notebooks/` folder:
- `backend_app.py` — FastAPI backend for the 12-column retail dataset
- `frontend_streamlit_app.py` — Streamlit frontend for same

**Do NOT modify those files.** They are reference history. You are creating two new files:
- `notebooks/hill_country_backend.py` — new FastAPI backend
- `notebooks/hill_country_streamlit.py` — new Streamlit frontend

## Authoritative references (read these first)

1. `notebooks/backend_app.py` and `notebooks/frontend_streamlit_app.py` in this engagement — the prior generation's deployment layer. Use for reference on FastAPI route structure, Streamlit form layout, and the new/old store pattern. Do NOT copy verbatim; the schema is different.

2. `engagements/ref-retail-revenue-pred__reg__ensemble-exp/HF_DEPLOY_GUIDE.md` — explains the HF Space targets (`EvagAIML/smb-retail-revenue-pred-backend` and `EvagAIML/smb-retail-revenue-pred-frontend`) and the keep-alive workflow. Skim for context on deployment conventions.

3. `notebooks/hill_country_grocer__reg__ensemble.ipynb` (the executed Colab version) — read the feature engineering cells to confirm exactly which derived features the preprocessor expects (`discount_pct`, `store_age`, `is_promo`).

## Backend requirements — `hill_country_backend.py`

FastAPI app with these endpoints:

**`GET /models`** — returns the parsed `model_registry.json` so the frontend can populate the admin dropdown. Response shape:

```json
{
  "models": [
    {"slug": "random-forest", "display_name": "Random Forest", "test_r2": 0.92, "test_mape": 0.094, "is_primary": true},
    {"slug": "xgboost", "display_name": "XGBoost", "test_r2": 0.91, "test_mape": 0.098, "is_primary": false},
    ...
  ]
}
```

**`POST /predict`** — accepts a request body with the model slug and a product-store record, returns the predicted weekly revenue.

Request shape:
```json
{
  "model_slug": "random-forest",
  "record": {
    "Item_Description": "Fresh Bananas",
    "Department": "Produce",
    "Brand_Type": "National Brand",
    "Net_Weight_oz": 2.15,
    "Pack_Size": 1,
    "List_Price_USD": 1.40,
    "Promo_Price_USD": 1.25,
    "Shelf_Facings": 8,
    "Store_Number": "HCG-101",
    "Store_Banner": "Hill Country Grocer",
    "Store_Region": "South - Texas Central",
    "Store_Sq_Ft": 42000,
    "Store_Open_Year": 2011
  }
}
```

Note: `UPC` is NOT in the request — it was dropped from features in the notebook. `Weekly_Units_Sold` is NOT in the request — that was the target-leakage feature. `Weekly_Revenue_USD` is NOT in the request — that's the target being predicted.

Response shape:
```json
{
  "predicted_weekly_revenue_usd": 130.60,
  "model_used": "random-forest",
  "model_test_r2": 0.92,
  "model_test_mape": 0.094
}
```

Implementation details:
- Load all six models + preprocessor + registry once at app startup, cache in module-level globals. Do not reload per request.
- Apply derived features (`discount_pct`, `store_age`, `is_promo`) to the incoming record before passing through the preprocessor. The frontend sends raw record fields; derivations happen server-side so the API contract is simple.
- Use `current_year = 2026` for `store_age` derivation. Hardcoded — do not pull from `datetime.now()`. The model was trained against a fixed year and using runtime year would silently drift predictions over time.
- Return HTTP 400 if `model_slug` is not in the registry, with a message listing valid slugs.
- Return HTTP 422 (FastAPI default) on malformed request bodies. Pydantic models enforce types.
- Include a `GET /health` endpoint returning `{"status": "ok", "models_loaded": 6}`. The keep-alive workflow pings this.

CORS: enable for all origins. The frontend is on a different HF Space.

## Frontend requirements — `hill_country_streamlit.py`

Streamlit app with two top-level modes selected by a sidebar radio:

**Mode 1 — "Predict for an existing store"** (default)

User flow:
1. Select a store from a dropdown of the six real stores (HCG-101 through HCG-106). Display each as `"{Store_Number} — {Store_City}"`. Reading store metadata: hardcode a small dict in the frontend mapping Store_Number → {Store_City, Store_Banner, Store_Region, Store_Sq_Ft, Store_Open_Year}. Six entries. Source the values from the dataset's actual store records.
2. Selected store auto-fills the store fields (read-only display, not editable).
3. User enters product fields: Item_Description (text), Department (dropdown of 12 departments from the dataset), Brand_Type (dropdown: National Brand / Private Label / Specialty — confirm exact values from the dataset), Net_Weight_oz (number), Pack_Size (number), List_Price_USD (number), Promo_Price_USD (number, defaulting to List_Price), Shelf_Facings (number).
4. "Predict" button calls `POST /predict` and displays the predicted revenue as a large metric, with the model used + its test R²/MAPE shown smaller below.

**Mode 2 — "Predict for a hypothetical new store"**

User flow:
1. All store fields become editable: Store_Banner (dropdown of the three banners observed in the dataset — Hill Country Grocer / Hill Country Grocer Express / Hill Country Grocer Warehouse), Store_Region (dropdown of the four regions), Store_Sq_Ft (number, with sensible min/max), Store_Open_Year (number, 2000–2026). Store_Number is auto-generated as `"HCG-NEW"` or similar and shown read-only.
2. Product fields same as Mode 1.
3. "Predict" button same as Mode 1.

**Admin section** (collapsible expander at the bottom of the sidebar, labeled "Admin — Model Selection"):

- Default state: collapsed. When expanded, shows a dropdown of all six models populated from `GET /models`.
- Each option shows: `"{Display Name} (R² {test_r2:.3f}, MAPE {test_mape:.1%})"`. The primary model is marked with a "★" prefix.
- Default selection: the primary model. Changing the selection changes which model the next "Predict" click uses.
- Below the dropdown, a small caption explaining: "Choose a model to compare predictions across the six trained candidates. The starred model was the primary selection at training time."

**Backend URL configuration:**

- Read from a Streamlit secret or environment variable `BACKEND_URL`. Fall back to `http://localhost:8000` for local dev. Do not hardcode the HF Space URL.

**Visual notes:**

- Page title: `"Hill Country Grocer — Weekly Revenue Forecasting"`
- Sidebar header: brand name, then mode radio, then admin expander.
- Main area: form, then on submit, prediction display.
- Use `st.metric` for the prediction, `st.caption` for model attribution.

## Halt points

**Halt A — after reading references, before authoring.** Confirm:
- All six model files + preprocessor + registry are present in `models/`
- The executed notebook's feature engineering cells match what this prompt assumes (`discount_pct`, `store_age`, `is_promo` with `current_year = 2026`)
- The actual values of `Brand_Type`, `Department`, `Store_Region`, `Store_Banner` from the dataset, so dropdowns are correct
- Report any discrepancies before authoring

Wait for operator approval.

**Halt B — after authoring both files, before any git operations.** Report:
- Line counts of both files
- The route list for the backend
- The dropdown values you derived from the dataset
- Any assumptions you made that aren't directly stated in this prompt

Do NOT commit. Wait for operator to review.

**Halt C — after operator approval, for the commit.** Stage and commit:

```
git add engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/hill_country_backend.py
git add engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/hill_country_streamlit.py
```

Commit message:
```
Add Hill Country Grocer deployment layer: backend + frontend

- hill_country_backend.py — FastAPI app loading all six serialized models +
  preprocessor. GET /models exposes the registry; POST /predict accepts a
  model_slug and product-store record, returns predicted weekly revenue.
- hill_country_streamlit.py — Streamlit frontend with existing-store and
  new-store modes, admin model-choice dropdown comparing all six candidates.

Targets HF Spaces EvagAIML/smb-retail-revenue-pred-{backend,frontend} per
the existing HF_DEPLOY_GUIDE.md.
```

Push to `origin main`. Report commit SHA and slug-pattern URLs for both files.

## What you do NOT do

- Do not modify the existing `backend_app.py` or `frontend_streamlit_app.py`
- Do not modify the notebook, the dataset, or anything under `models/`
- Do not deploy to HuggingFace Spaces — that's the operator's manual step using `HF_DEPLOY_GUIDE.md` after this commit lands
- Do not commit anything before Halt C

If anything in the deployed model artifacts doesn't match what this prompt assumes, halt and ask.
