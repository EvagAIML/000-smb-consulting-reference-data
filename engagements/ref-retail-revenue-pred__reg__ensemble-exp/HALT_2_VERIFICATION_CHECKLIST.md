# Halt 2 verification checklist — Hill Country Grocer notebook

Things to check against the authored `hill_country_grocer__reg__ensemble.ipynb` before approving Halt 3. Each item is grounded in a specific prior failure documented in `lessons/lessons.md`. Numbered for cross-reference in your reply to Claude Code.

## A. Bugs that broke prior executions

### A1. NumPy 2 / scipy / optional-deps install discipline (2026-05-07 retail build)
The prior retail build's install cell pinned exact versions, pip said "requirement already satisfied," and left NumPy-1.x-compiled binaries (pandas, sklearn, xgboost, seaborn, scipy, bottleneck, numexpr) in place. Two failed Papermill attempts before the operator manually `--force-reinstall --no-deps`'d everything.

**Check:** Does the install cell either (a) use `--force-reinstall --no-deps` on the binary-sensitive pins, OR (b) explicitly avoid pinning to versions that may exist on the operator's host as broken binaries? Catboost in particular must be installed unconditionally — it was missing entirely on the retail run.

**Pass criterion:** Install cell does not rely on "requirement already satisfied" semantics for any package that has NumPy ABI dependencies. Either force-reinstall, or document the host-prep step in the markdown above the install cell.

### A2. No embedded source-code blobs inside cells (2026-04-30 Prophet build)
The Prophet build's deployment cell embedded a Streamlit app inside a triple-quoted string and the escaping broke. The retail build also embedded its Streamlit source in cell 218's heredoc — worked only because it had been verified on Colab, but flagged as a foot-gun.

**Check:** Does the Hill Country notebook embed any `.py` source as a string inside a code cell? Backend/frontend cells should be **absent entirely** (we deferred deployment), but if any model-loading or utility script is being written-to-disk via heredoc, that's an anti-pattern.

**Pass criterion:** Notebook contains no triple-quoted strings being written to `.py` files. If serialization needs to write a small `model_registry.json`, that's fine (JSON, not Python source).

### A3. No multi-line f-strings with line continuations (2026-04-30 AutoGluon classifier)
Multi-line f-strings broke on first Papermill execution. Fix is to use accumulator variables.

**Check:** Any `f"""..."""` blocks spanning multiple lines? Any `f"... \` line continuations inside f-strings?

**Pass criterion:** F-strings are either single-line or built up with `+=` accumulators.

### A4. AutoGluon kwarg drift, generalized (2026-05-01 used-car build)
Specific instance was `random_seed=` removed in AutoGluon 1.5. The general lesson is: **kwargs in library calls must be valid for the version pinned in the install cell.** For this notebook, that's XGBoost, CatBoost, LightGBM kwargs (if used), sklearn version-specific kwargs (e.g., `OneHotEncoder` had `sparse=` deprecated in favor of `sparse_output=`).

**Check:** Cross-reference any `XGBRegressor(...)`, `CatBoostRegressor(...)`, `OneHotEncoder(...)`, `RandomForestRegressor(...)` kwargs against the version pinned in the install cell. Particular suspects: `OneHotEncoder(sparse=False)` vs `sparse_output=False`; `XGBRegressor(use_label_encoder=...)` removed.

**Pass criterion:** Every kwarg in every estimator constructor is valid for the pinned version.

## B. Procedure-ordering and content-grounding failures

### B1. Pass 1 / Pass 2 narrative grounding (2026-04-30 Prophet, 2026-05-01 used-car)
Pre-execution narratives claimed metrics that didn't match execution (5% MAPE claimed, 7.58% actual on Prophet; "100,000 rows" claimed, 72,435 actual on used-car). The system-design contract is that *every factual claim* in narrative cells gets regenerated against executed evidence in Pass 2.

**Check:** Does the Value Proposition cell and the top Executive Summary contain any concrete numeric claims (R², MAPE, RMSE, row counts, brand lists, top features)? If yes, are they placeholder-tokenized (`{R2_PLACEHOLDER}`, etc.) so Pass 2 has clear substitution targets after Colab execution?

**Pass criterion:** Either (a) narrative is generic and avoids concrete metric claims pre-execution, OR (b) every concrete claim is a placeholder token, never a guessed value. The Hill Country prompt told Claude Code to use placeholders — verify it actually did.

### B2. Orphan placeholders — every placeholder must have a measured source (2026-05-01 multi-cls)
Pass 1 wrote `{TOP_FEATURES_PLACEHOLDER}` but no code cell computed feature importance. Pass 2 caught the orphan rather than fabricating.

**Check:** For every placeholder token in the notebook, identify the code cell that produces the corresponding value at execution time.

**Pass criterion:** No placeholder is orphaned. Each one has a clearly-identifiable producing cell — feature importance, tier assignment, model leaderboard, etc.

### B3. Slug-pattern data URL, not a third-party mirror (2026-05-01 multi-cls)
The used-car build claimed to use the slug pattern but actually loaded from `Ajinkya017/Car_Dataset`. The contract is: data loads from `000-smb-consulting-reference-data` via the slug-pattern URL.

**Check:** The data-ingestion cell pulls from this exact URL (or a substring-equivalent):

```
https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/hill_country_grocer_weekly_sales.csv
```

**Pass criterion:** URL is exactly the above (or a documented variable holding it). No mirror URLs, no `/tmp/`, no absolute filesystem paths.

## C. Scope-creep markers (2026-05-07 retail build)

### C1. Vocabulary check for unauthorized work
Words that flag scope creep in Claude Code preamble: "corruption", "fix script", "comprehensive script", "while I'm in here," "I also noticed and fixed," "I went ahead and."

**Check:** Read the Halt 2 report end-to-end. Any of these phrases present?

**Pass criterion:** No unauthorized work was bundled. If any was, demand it be reverted before Halt 3.

### C2. File scope at Halt 2
Halt 2 should show **one new file on disk**: `hill_country_grocer__reg__ensemble.ipynb`. Nothing else.

**Check:** Ask Claude Code to run `git status` and report. The only untracked or modified file in `notebooks/` should be the new `.ipynb`. The original `colab_authored.ipynb` and `executed.ipynb` must be byte-identical to their committed state. The two `.py` files (`backend_app.py`, `frontend_streamlit_app.py`) must be untouched.

**Pass criterion:** `git status` shows exactly one new file in the engagement folder's `notebooks/` subdirectory.

## D. Notebook-structure invariants from the style guide

### D1. Required cells present
Per the style guide and the agreed plan: Title, Value Proposition, Executive Summary, Problem Statement + Data Dictionary, Code Execution divider, then the lifecycle, then Expanded Executive Summary at the bottom.

**Check:** Cell-by-cell sequence matches the plan Claude Code laid out at Halt 1 (the 30-cell-section list).

**Pass criterion:** All sections present, ordered as planned. Any divergence from the Halt 1 plan must be explained.

### D2. Every markdown cell has Summary/Process + Observations/Outcome
Style guide is explicit. Observations/Outcome can be placeholder for unexecuted notebooks but the line must exist.

**Check:** Random spot-check on 5–10 markdown cells across the notebook. Look for the two bolded labels.

**Pass criterion:** Every sampled markdown cell has both lines.

### D3. Every code cell has banner + plain-English description + commented imports
Style guide is explicit.

**Check:** Random spot-check on 5–10 code cells.

**Pass criterion:** Every sampled code cell opens with `# -----`, has a description, and every import line has a trailing comment.

## E. Modeling-decision invariants (specific to this build)

### E1. Weekly_Units_Sold is dropped
The whole reason we're doing this build differently. The target-leakage callout cell exists and explicitly explains why.

**Check:** Search the notebook for `Weekly_Units_Sold`. Should appear: (a) in the data dictionary, (b) in the target-leakage callout markdown, (c) in feature engineering as an explicit drop. Should NOT appear: as a feature in any model fit.

**Pass criterion:** Drop is explicit and documented. No model is trained on it.

### E2. UPC is dropped, not engineered
Confirmed at Halt 1 — drop entirely.

**Check:** Search for `UPC`. Should appear only in data dictionary and feature engineering (as a drop).

**Pass criterion:** No UPC manufacturer-prefix extraction, no UPC categorical encoding.

### E3. All six models serialized + preprocessor + registry
Per the addendum prompt.

**Check:** Serialization section contains six `joblib.dump` calls for the trained estimators, one for the fitted preprocessor, and one for `model_registry.json`.

**Pass criterion:** All eight artifacts are produced. The six-model registry includes display name, slug, test R², test MAPE, and `is_primary` flag for each.

### E4. Tier thresholds are v1.0 verbatim
Decided at Halt 1 — option (a), keep verbatim.

**Check:** Tier assignment cell uses thresholds from `catalog/v1.yaml` (R² ≥ 0.92 ∧ MAPE ≤ 0.08 for Tier 1, etc.). No revised thresholds defined locally in the notebook.

**Pass criterion:** Thresholds match v1.0 catalog, notebook honestly reports whatever tier the executed metrics land in.

### E5. Forward-honest comparability caveat
Asked at Halt 1 reply — two sentences in the target-leakage callout noting prior `colab_authored.ipynb` retained the analogous leakage feature and metrics are not directly comparable.

**Check:** Target-leakage callout cell contains explicit reference to the prior notebook and a statement that cross-notebook metric comparison is not valid.

**Pass criterion:** Both sentences present, plainly worded.

## F. Things that are NOT in scope for Halt 2

Do not fail Halt 2 for any of these — they're downstream:

- Actual executed metrics (notebook hasn't run yet)
- The eight serialized artifacts existing on disk (they're produced at Colab execution, not at authoring time)
- Backend/frontend Python files (separate task)
- HF Spaces deployment (separate task)
- The keep-alive workflow file (per the prior `CLAUDE_CODE_INSTRUCTIONS.md`, that's deferred to a later task after Spaces exist)

---

## How to use this at Halt 2

When Claude Code surfaces with the Halt 2 report, paste the relevant checks back to it. The structure I'd use:

1. Ask Claude Code to run `git status` and report — closes C2.
2. Ask Claude Code to grep the notebook for the vocabulary markers in C1.
3. Ask Claude Code to grep for `Weekly_Units_Sold` and `UPC` references and quote the surrounding context — closes E1, E2.
4. Ask Claude Code to list every placeholder token in the notebook with the cell index that produces the value — closes B1, B2.
5. Ask Claude Code to dump the install cell's full contents — closes A1.
6. Spot-check 5 markdown cells and 5 code cells, including the target-leakage callout — closes D2, D3, E5.
7. Open the notebook in Jupyter for the operator's own eyeball check.

If items 1–6 pass, Halt 3 is approve-able. Step 7 is the human check that anything not captured by the checklist still looks right.
