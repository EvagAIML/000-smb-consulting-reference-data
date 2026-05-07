# HuggingFace Spaces Deploy Guide

**Engagement:** `ref-retail-revenue-pred__reg__ensemble-exp`
**Catalog entry slug (target):** `smb-retail-revenue-pred__reg__ensemble`
**Backend Space:** `EvagAIML/smb-retail-revenue-pred-backend`
**Frontend Space:** `EvagAIML/smb-retail-revenue-pred-frontend`

---

## Prerequisite: notebook execution must be complete and clean

Do not start this guide until:

- Task 1 (data migration) and Task 2 (notebook execution) from `CLAUDE_CODE_INSTRUCTIONS.md` are complete
- Tasks 3a–3g (cleanup, including the cell 218 `BACKEND_URL` update — see "Critical pre-deploy fix" below) are complete
- The executed notebook has produced these directories on disk:
  - `backend_space_root/` containing `app.py`, `requirements.txt`, `Dockerfile`, `model_metadata.json`, `primary_model.joblib`, `secondary_model.joblib`
  - `frontend_space_root/` containing `requirements.txt` and `src/streamlit_app.py`

If those directories don't exist, the notebook didn't execute the deployment-asset cells (cells 211, 215, 218). Re-run those cells before proceeding.

Note: Task 3h (commit the keep-alive workflow) happens AFTER Step 6 of this guide — the keep-alive cron should not start running until both Spaces actually exist, otherwise its first runs will fail with connection errors.

---

## Critical pre-deploy fix — frontend's BACKEND_URL

The v26 notebook's cell 218 hardcodes the OLD backend URL:

```python
BACKEND_URL = "https://EvagAIML-RetailPrediction001Backend.hf.space/v1/predict"
```

This must be changed to the NEW backend URL before the frontend is pushed:

```python
BACKEND_URL = "https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/v1/predict"
```

**This change must happen IN THE NOTEBOOK** (so the frontend_space_root regenerates with the correct URL), not directly in the deployed Streamlit file. The notebook is the source of truth.

The change is one `str_replace` on cell 218. Re-execute cells 218 onward to regenerate `frontend_space_root/` with the corrected URL. Verify the change took by reading `frontend_space_root/src/streamlit_app.py` and grepping for `BACKEND_URL`.

This is part of Task 3b/3d. Without it, the new frontend will silently call the old backend.

---

## Deploy order — backend first, then frontend, then keep-alive

The frontend depends on the backend being live (it calls it on every prediction). Deploy backend first, verify it responds, then deploy frontend, verify end-to-end, then activate the keep-alive workflow.

---

## Step 1 — Create the backend Space on HuggingFace

1. Sign in to https://huggingface.co with the EvagAIML account.

2. Click your profile avatar (top right) → **New Space**.

3. Fill in the form:
   - **Owner:** `EvagAIML`
   - **Space name:** `smb-retail-revenue-pred-backend`
   - **License:** Choose appropriately (MIT or Apache 2.0 are common for tooling). If unsure, MIT.
   - **Select the Space SDK:** **Docker** (the v26 notebook generates a Dockerfile because the backend is FastAPI on uvicorn, not Streamlit/Gradio).
   - **Choose a Docker template:** Blank.
   - **Space hardware:** CPU basic (free tier).
   - **Visibility:** Public (the consulting-system pattern is public reference deployments; private is for customer engagements).

4. Click **Create Space**.

5. The Space will be created empty. Note the Space's URL — it should be `https://huggingface.co/spaces/EvagAIML/smb-retail-revenue-pred-backend`. Confirm this matches before proceeding.

---

## Step 2 — Push backend artifacts via the notebook's HF push cell

The v26 notebook has cell 215 that uses `huggingface_hub.upload_folder` to push `backend_space_root/` to a Space. The cell currently targets the OLD Space (`EvagAIML/RetailPrediction001Backend`).

Change the cell to target the new Space:

```python
from huggingface_hub import upload_folder
upload_folder(
    repo_id="EvagAIML/smb-retail-revenue-pred-backend",
    folder_path="backend_space_root",
    path_in_repo=".",
    repo_type="space",
    commit_message="Initial deploy of smb-retail-revenue-pred backend (catalog entry v1)",
    create_pr=False,  # was True in old cell — set to False for direct push
)
```

If you haven't authenticated already, run cell 213 first (`from huggingface_hub import login; login()`) and paste your HF write token when prompted. Get a write token from https://huggingface.co/settings/tokens if you don't have one.

Run cell 215. It will upload all files in `backend_space_root/` (Dockerfile, requirements.txt, app.py, the two .joblib model files, model_metadata.json) to the Space.

---

## Step 3 — Verify backend build and health

1. Open `https://huggingface.co/spaces/EvagAIML/smb-retail-revenue-pred-backend` in your browser.

2. The Space will start building. The build log shows the Docker image being constructed (FROM python:3.12-slim, pip install requirements, etc.). Build typically takes 3-7 minutes for this image (depends on package install time, joblib model size).

3. **Watch for these specific success markers in the build log:**
   - `FROM python:3.12-slim` (per the Dockerfile in cell 211)
   - `Successfully installed catboost-* xgboost-* scikit-learn-* ...` (no install failures)
   - `Application startup complete.` (uvicorn started successfully)

4. **If the build fails:**
   - Check the build log for the actual error
   - Most common failure mode is package version conflicts — the v26 notebook pins a specific set in cell 211 (`fastapi==0.111.0 uvicorn==0.30.1 scikit-learn==1.6.1 ...`). If any of those have been yanked from PyPI or have transitive conflicts, the build fails.
   - Use HF's "Factory rebuild" button (Settings tab on the Space) if the build looks stuck or stale

5. Once the Space shows "Running", verify the API:
   ```
   curl https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/health
   ```
   Expected response (JSON):
   ```json
   {
     "status": "healthy",
     "primary_model": "<primary model label, e.g., 'CatBoost'>",
     "secondary_model": "<secondary model label, e.g., 'XGBoost'>"
   }
   ```

   If `/health` returns 200 with both model labels populated, the backend is live and ready for the frontend.

6. (Optional) Test a single prediction to confirm the model serves correctly:
   ```
   curl -X POST https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/v1/predict \
     -H "Content-Type: application/json" \
     -d '{
       "model": "<primary model label from /health>",
       "rows": [{
         "Product_Weight": 12.65,
         "Product_Sugar_Content": "Low Sugar",
         "Product_Allocated_Area": 0.069,
         "Product_Type": "Fruits and Vegetables",
         "Product_MRP": 147.03,
         "Store_Id": "OUT004",
         "Store_Type": "Supermarket Type2",
         "Store_Size": "Medium",
         "Store_Location_City_Type": "Tier 2",
         "Store_Age_Years": 16,
         "Product_Id_char": "FD",
         "Product_Type_Category": "Perishables"
       }]
     }'
   ```
   Expected: a JSON response with `predictions`, `overall_total`, `store_totals`, and `model_used` populated. Predicted revenue should be a positive float in the typical range ($1,000-$8,000 per row based on the dataset's distribution).

   If this curl returns a useful prediction, the backend is fully verified.

---

## Step 4 — Create the frontend Space on HuggingFace

1. Back at https://huggingface.co, click your avatar → **New Space**.

2. Fill in the form:
   - **Owner:** `EvagAIML`
   - **Space name:** `smb-retail-revenue-pred-frontend`
   - **License:** Same as backend (MIT or Apache 2.0).
   - **Select the Space SDK:** **Streamlit** (the frontend is a pure Streamlit app; no Docker needed).
   - **Streamlit version:** Default (latest stable). The notebook's cell 218 pins `streamlit==1.43.2` in `frontend_space_root/requirements.txt`, which HF will honor.
   - **Space hardware:** CPU basic (free tier).
   - **Visibility:** Public.

3. Click **Create Space**.

4. Confirm the URL is `https://huggingface.co/spaces/EvagAIML/smb-retail-revenue-pred-frontend`.

---

## Step 5 — Push frontend artifacts via the notebook's HF push cell

The v26 notebook has a frontend push cell (the cell after 218 that calls `upload_folder` for `frontend_space_root/`). It currently targets the OLD frontend Space.

Locate the cell and change its `repo_id` to:

```python
from huggingface_hub import upload_folder
upload_folder(
    repo_id="EvagAIML/smb-retail-revenue-pred-frontend",
    folder_path="frontend_space_root",
    path_in_repo=".",
    repo_type="space",
    commit_message="Initial deploy of smb-retail-revenue-pred frontend (catalog entry v1)",
    create_pr=False,
)
```

Run the cell. It will upload `requirements.txt` and `src/streamlit_app.py` to the new Space.

---

## Step 6 — Verify frontend build and end-to-end flow

1. Open `https://huggingface.co/spaces/EvagAIML/smb-retail-revenue-pred-frontend` in your browser.

2. The Streamlit app will build (typically 1-2 minutes — much faster than the Docker backend).

3. **Watch for these markers in the build log:**
   - `Successfully installed streamlit-1.43.2 requests-2.32.3` (no install failures)
   - `You can now view your Streamlit app...` (Streamlit started)

4. Once the Space shows "Running", the app should render in the embedded view. Test the end-to-end flow:

   **Single prediction test (existing store):**
   - In the "Store Information" section, leave Store ID at default (or select OUT004)
   - Confirm the Store Type, Size, City Tier, Age fields auto-fill and become locked (this verifies the cascading store profile logic)
   - Leave product fields at defaults
   - Click **Predict Revenue**
   - Expected: a revenue prediction appears (positive float, $1,000-$8,000 range)
   - If the prediction comes back successfully, **the frontend is talking to the new backend** (any backend URL bug would surface as a connection error here)

   **Single prediction test (new store):**
   - Select Store ID = `NEW_STORE`
   - Confirm Store Type, Size, City Tier, Age become editable
   - Fill in plausible values (e.g., Supermarket Type1, Medium, Tier 2, 5 years)
   - Click **Predict Revenue**
   - Expected: a different prediction (since the store profile differs from any existing store)

   **Batch prediction test:**
   - Download a few rows from the source data (e.g., the first 10 rows of `retail_prediction.csv` — but only the feature columns, not the target column `Product_Store_Sales_Total`)
   - Save as a CSV with the same column headers
   - Upload via the "Batch Prediction File" widget
   - Click **Predict Batch**
   - Expected: per-row predictions, an `overall_total`, and `store_totals` rolled up by Store_Id

5. If all three tests pass, the deploy is verified end-to-end. Tell Claude Code to proceed with Task 3h (activate the keep-alive workflow).

---

## Step 7 — Document the deploy and activate keep-alive

Once both Spaces are live and verified end-to-end (Step 6 passed):

1. **Tell Claude Code to execute Task 3h** (commit the pre-staged keep-alive workflow file at `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml`). Per the instructions, Claude Code will commit + push the workflow, then expect you to verify in the Actions tab.

2. **Verify the keep-alive workflow loaded.** Open `https://github.com/EvagAIML/000-smb-consulting-reference-data/actions` in browser. The "keep-alive — ref-retail-revenue-pred__reg__ensemble-exp" workflow should appear in the workflows list.

3. **Trigger a manual run** to confirm the workflow works without waiting for the cron:
   - Click into the workflow
   - Click "Run workflow" (top right) → confirm with the green button
   - Wait ~30 seconds, refresh the page
   - The run should appear with a green checkmark
   - Click into the run and expand the "Ping backend Space" and "Ping frontend Space" steps — both should report HTTP 200

   If either ping reports a non-200/503 status, surface to the operator. The most likely cause is a typo in the Space name (yours vs. the workflow's hardcoded URL).

4. In the engagement folder (`engagements/ref-retail-revenue-pred__reg__ensemble-exp/`), create `deployment/deployment_record.md` capturing:
   - Backend Space URL and deploy date
   - Frontend Space URL and deploy date
   - The `model_metadata.json` contents (which models are primary/secondary, with their test-set metrics)
   - The model artifact sizes
   - Any deploy issues encountered and their fixes
   - The keep-alive workflow's first successful run timestamp (from Step 7.3 above)

5. Append a lessons-log entry to `lessons/lessons.md` in `000-smb-consulting-system-private` per `system-design.md` §15.3, capturing what was deployed and any surprises (this likely already happened in Task 3f — if so, just append to that entry).

6. (Optional, if you want to retire the old Spaces) On HuggingFace, you can either:
   - Delete `RetailPrediction001Backend` and `RetailPrediction001Frontend` (clean break)
   - Add a README banner to each old Space pointing at the new ones (preserves continuity for anyone with the old URLs bookmarked)

The latter is friendlier to anyone who's already shared the old URLs.

---

## Failure modes worth knowing about

- **Backend build hangs at package install.** Some HF Docker builds can stall on heavy ML packages (catboost is the usual culprit). Use Settings → Factory rebuild to retry.

- **Backend returns 500 on /v1/predict but /health works.** The model loaded but a column expected by the model isn't in the predict request. Check the model_metadata.json's expected feature names against the request payload.

- **Frontend renders but predictions error with "Backend error (404)".** The BACKEND_URL is wrong (still pointing at the old backend, or the new backend Space hasn't finished building yet). Verify the new backend's `/health` returns 200 first.

- **Frontend renders but predictions error with "Backend error (500)".** The frontend is reaching the backend but the backend can't process the request. Check the backend's runtime logs (Logs tab on the backend Space) for the actual error.

- **HF push fails with `403 Forbidden`.** Your HF token doesn't have write access to that Space, or the Space doesn't exist yet. Re-create the token with write scope, or confirm the Space was created in Step 1 / Step 4.

- **Keep-alive workflow's manual run reports HTTP 503 for both pings.** The Spaces are awake but reporting "starting" — usually means they're cold-starting. Wait 60-90 seconds and re-run. Ongoing 503s mean the Spaces themselves have an issue (check their Status tab).

- **Keep-alive workflow's manual run reports HTTP 000 or curl error.** The Space URL doesn't resolve. Check the Space name matches what's hardcoded in the workflow file (`EvagAIML-smb-retail-revenue-pred-backend.hf.space` and `EvagAIML-smb-retail-revenue-pred-frontend.hf.space`).

---

## What this guide is NOT

- Not a CI/CD setup. Each deploy is a manual `upload_folder` call from the notebook. Automated redeploy on catalog version bump is v2 work.
- Not a custom domain setup. The deployed Spaces use the default `*.hf.space` URLs. Custom domain mapping is HF Pro feature, out of scope here.

---

*End of HF deploy guide.*
