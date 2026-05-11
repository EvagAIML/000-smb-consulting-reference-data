"""Pass 2 narrative regeneration: Hill Country Grocer notebook against v2.2 canon.

One-shot rewrite of the executed notebook's markdown cells (all code cells preserved
verbatim, including execution_count and outputs) plus addition of deployment cells
per the v2.2 Deployment Section Placement convention.

Run once from any cwd:
    python3 engagements/ref-retail-revenue-pred__reg__ensemble-exp/scripts/pass2_rewrite.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

NB_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "hill_country_grocer__reg__ensemble.ipynb"
)


# ===========================================================================
# Combined top-of-notebook cell (replaces old cells 1, 2, 3; old cell 0 Title
# stays as-is; old cell 4 Code-Execution divider gets its `---` prefix stripped.)
# ===========================================================================

CELL_COMBINED_TOP = """## **Value Proposition**

In order to give a Texas regional grocery chain a defensible weekly revenue forecast for every item-store combination in its catalog, a six-model regression bake-off was developed across 8,880 weekly product-store sales records. The selected model — **CatBoost** — predicts `Weekly_Revenue_USD` with an R² of 0.9465 and a MAPE of 11.21% on the held-out test set (mean actual \\$81.22, MAE \\$8.86, RMSE \\$14.04). The recommendation is to deploy CatBoost as the lead model and retain XGBoost (R² 0.9384, MAPE 12.59%) as the parallel challenger.

## **Executive Summary**

### Business Opportunities

* **Opportunity A:** A multi-banner regional grocer with thousands of item-store combinations cannot price, stock, or merchandise each one by intuition. Category managers and inventory planners need the same defensible reference forecast for any combination in the catalog.

* **Solution A:** CatBoost returns a weekly revenue estimate per item-store row from product and store attributes alone (banner, region, square footage, store age, department, brand type, weight, pack size, list and promo prices, shelf facings), with test R² 0.9465. Every planner across the chain plugs the same row into the same model and gets the same answer.

* **Opportunity B:** When a store needs to decide how many shelf facings to allocate or whether to run a promotional price on a specific item, the planning team needs a measured confidence band rather than a guess.

* **Solution B:** CatBoost's test MAPE is 11.21% on a mean actual of \\$81.22, which corresponds to MAE \\$8.86. Forecasts are typically within roughly \\$9 of actual on a row averaging \\$81. Planning decisions can budget against that band rather than against intuition.

* **Opportunity C:** Mispriced, misallocated, or under-promoted inventory is hard to spot in a catalog of thousands of item-store combinations without a reference forecast to compare actuals against.

* **Solution C:** Comparing actual weekly revenue against CatBoost's forecast surfaces item-store rows where the actual materially diverges from the model. The 11.21% MAPE is the noise floor below which discrepancies are likely week-to-week variation; rows more than roughly 22% off the forecast (twice the noise floor) become a sortable list of action items for category review.

### Outcomes

**Model Performance**

* CatBoost is the primary model: test R² 0.9465, MAPE 11.21%, MAE \\$8.86, RMSE \\$14.04 on a mean actual of \\$81.22.

* XGBoost is the secondary model and challenger: test R² 0.9384, MAPE 12.59%. Roughly 0.8 percentage points of R² behind CatBoost and 1.4 percentage points of MAPE behind.

* Cross-validation stability is consistent with the test result. CatBoost's repeated 5×2 K-fold validation RMSE is \\$15.14 (standard deviation \\$0.85), and XGBoost's is \\$16.56 (standard deviation \\$1.00). The test-set numbers are not a single-split fluke.

**Architecture**

* Six regression candidates were trained and tuned: CatBoost, XGBoost, Gradient Boosting, Bagging, Random Forest, Decision Tree. Each ran inside an sklearn `Pipeline` with a shared `ColumnTransformer` preprocessor; tuning was done via 5-fold `GridSearchCV`; ranking was done via repeated 5×2 K-fold cross-validation RMSE.

* CatBoost won on validation RMSE and confirmed on the held-out test set. XGBoost finished second on both signals.

* All six trained candidates are serialized to disk alongside the fitted preprocessor and a `model_registry.json`. The deployed frontend exposes an admin model-choice dropdown across the full six so a user can compare predictions across model families on the same row.

**Economic Impact**

* MAPE 11.21% on a mean actual of \\$81.22 means typical forecasts land within roughly \\$9 of actual weekly revenue per item-store row.

* For a regional grocer planning shelf allocation and promotional pricing across thousands of item-store combinations, that band supports defensible operational decisions. Shelf-allocation reviews, promotional-pricing sign-off, and inventory-reorder planning all sit inside the model's measured noise floor rather than being driven by per-row guesswork.

* Tier 2 (Shippable — Strong) per the v1.0 catalog thresholds (Tier 1: R² ≥ 0.92 and MAPE ≤ 8%; Tier 2: R² ≥ 0.85 and MAPE ≤ 12%). The build clears the R² Tier 1 bar (0.9465 ≥ 0.92); MAPE (11.21%) lands inside the Tier 2 band and just outside the Tier 1 ≤ 8% bar, which places the overall tier at Tier 2.

**Strategy Recommendation**

* **Enterprise:** Deploy CatBoost as the production model. Maintain XGBoost as a parallel challenger in shadow mode against live traffic; revisit the comparison quarterly as the dataset grows and the operating context changes.

* **SMB:** Deploy CatBoost as the production model. Treat XGBoost as the secondary option exposed inside the deployed frontend's admin model-choice dropdown rather than as a separate production track.

### Live Deployment

* **Frontend (interactive app):** [Hill Country Grocer Revenue Forecaster](https://huggingface.co/spaces/evagaiml/hill-country-grocer-revenue-pred-frontend)

* **Backend (inference API):** [FastAPI service](https://huggingface.co/spaces/evagaiml/hill-country-grocer-revenue-pred-backend)

## **Problem Space**

### Overview

* Hill Country Grocer is a multi-banner Texas regional grocery chain with thousands of item-store combinations across departments, brands, banners, and store sizes.

* Small weekly forecasting errors scale into material financial impact across that catalog and footprint. Overstock ties up working capital and increases holding costs; understock directly reduces revenue capture and customer satisfaction.

* Pricing, shelf-allocation, and promotion decisions are made on a weekly cadence. A defensible per-row revenue forecast, computed from attributes known *before* the week begins, is the input planning teams need to make those decisions consistently across stores and categories.

### Data Description

* **Row count:** 8,880 weekly item-store sales records.

* **Column count:** 16 (15 features plus 1 target).

* **Columns:** `UPC` (12-digit identifier; dropped before modeling), `Item_Description` (product name), `Department`, `Brand_Type`, `Net_Weight_oz`, `Pack_Size`, `List_Price_USD`, `Promo_Price_USD`, `Shelf_Facings`, `Store_Number`, `Store_Banner`, `Store_Region`, `Store_Sq_Ft`, `Store_Open_Year` (transformed to `store_age` before modeling), `Weekly_Units_Sold` (target-leakage feature; dropped before modeling — see callout cell below), and the target `Weekly_Revenue_USD`.

* **Target:** `Weekly_Revenue_USD` (continuous, regression).

* **File:** `hill_country_grocer_weekly_sales.csv`, loaded from the public `000-smb-consulting-reference-data` repository via the canonical slug-pattern URL.

### Process

* **Data preparation:** `Weekly_Units_Sold` was dropped (target leakage — units × price approximately equals revenue). `UPC` was dropped (high-cardinality identifier). Three derived features were added: `discount_pct` (`(List_Price - Promo_Price) / List_Price`), `store_age` (reference-year-anchored tenure), and `is_promo` (binary indicator).

* **Modeling approach:** Six regression candidates (Decision Tree, Bagging, Random Forest, Gradient Boosting, XGBoost, CatBoost) were trained inside a shared `Pipeline` with a `ColumnTransformer` preprocessor, tuned via `GridSearchCV`, and ranked by repeated 5×2 K-fold cross-validation RMSE. The top two became primary and secondary.

* **Variance caveat:** Tree-based ensembles carry run-to-run variance from random fold splits and stochastic estimators. All random states are pinned for reproducibility, but absolute metric values can drift by a small amount if seeds change.

### Results

>| Model | Key Signal | Current Role |
>|---|---|---|
>| **CatBoost ✅** | R² 0.9465, MAPE 11.21%, MAE \\$8.86 on mean actual \\$81.22 | Lead deployment model |
>| XGBoost | R² 0.9384, MAPE 12.59% | Parallel challenger; retained for continued development |"""


CELL_CODE_EXECUTION_DIVIDER = "# **Code Execution**"


# ===========================================================================
# Body markdown rewrites (Process / Outcome — and Process / Analysis / Outcome
# where interpretation belongs). Indexed by OLD cell index.
# ===========================================================================

CELL_LIBRARY_INSTALLATION = """### **Library Installation**

**Process:** Required packages are checked against the active environment and any missing ones are installed; a runtime-restart banner is rendered if any package was added.

**Outcome:** The notebook environment carries the tree-based regression dependencies (`xgboost`, `catboost`) plus the standard PyData stack (`scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `joblib`) at the versions the rest of the notebook expects."""

CELL_IMPORTS = """### **Imports and Configuration**

**Process:** Core libraries for tabular analysis, visualization, preprocessing, evaluation, and ensemble regression modeling are initialized for the full workflow. Reproducibility seeds and cross-validation configuration are pinned at this step.

**Outcome:** The notebook environment is ready to load Hill Country Grocer weekly sales data, prepare features, and compare regression candidates. Random-state seeds are pinned across the train/test split, `GridSearchCV`, repeated K-fold, and each estimator's RNG so the bake-off is reproducible."""

CELL_DATA_INGESTION = """### **Data Ingestion**

**Process:** The Hill Country Grocer weekly sales dataset is loaded from the `000-smb-consulting-reference-data` repository via the canonical slug-pattern URL on `raw.githubusercontent.com`, per the notebook style guide's data-loading contract.

**Outcome:** The dataset loads as a single CSV at 8,880 rows by 16 columns. No authentication is required because the reference-data repo is public and `*.csv` is excluded from LFS, so `raw.githubusercontent.com` serves the actual file bytes rather than an LFS pointer."""

CELL_DATA_CHECKPOINT = """### **Data Checkpoint**

**Process:** A working copy of the raw DataFrame is created so subsequent cleaning and feature-engineering steps mutate the working copy rather than the originally loaded data.

**Outcome:** `df_raw` is preserved untouched; all downstream operations target the working copy. Re-running any downstream cell after editing does not require re-downloading the CSV."""

CELL_DATA_UNDERSTANDING = """### **Data Understanding**

**Process:** Column dtypes, basic descriptive statistics, and the target's distribution shape are assessed before any feature engineering or modeling.

**Analysis:** The schema separates cleanly into six categorical columns (`Item_Description`, `Department`, `Brand_Type`, `Store_Number`, `Store_Banner`, `Store_Region`), seven numeric features (`Net_Weight_oz`, `Pack_Size`, `List_Price_USD`, `Promo_Price_USD`, `Shelf_Facings`, `Store_Sq_Ft`, `Store_Open_Year`), the `UPC` identifier, the `Weekly_Units_Sold` leakage column, and the target `Weekly_Revenue_USD`. The target has a moderate right-skew typical of revenue distributions.

**Outcome:** The schema is well-formed and ready for the data-quality pass; the identifier and leakage columns are flagged for removal before modeling."""

CELL_DATA_QUALITY = """### **Data Quality Checks**

**Process:** The DataFrame is inspected for missing values, duplicate rows, and obviously implausible values (negative prices, zero or negative weights, promo prices above list prices) before any feature engineering.

**Outcome:** No duplicate rows, no missing values, and no implausible numerics surface; the dataset proceeds to EDA without remediation."""

CELL_EDA_UNIVARIATE_NUMERIC = """### **Exploratory Data Analysis — Univariate Numeric Distributions**

**Process:** Histograms with kernel-density overlays are rendered for each numeric column to surface shape, spread, and any visible outliers or multi-modality.

**Analysis:** `Weekly_Revenue_USD` shows a right-skewed distribution; `List_Price_USD` and `Promo_Price_USD` show stepwise concentration at common price points; `Store_Sq_Ft` is effectively discrete, corresponding to a small number of distinct store-size buckets.

**Outcome:** The numeric features carry usable signal across their observed ranges; no transformation is required at this stage beyond the feature engineering planned below."""

CELL_EDA_UNIVARIATE_CATEGORICAL = """### **Exploratory Data Analysis — Univariate Categorical Frequencies**

**Process:** Value-count bar charts are rendered for each low-cardinality categorical column; high-cardinality columns (`UPC`, `Item_Description`) get a `value_counts().head()` printout rather than a chart.

**Outcome:** Each categorical column shows a multi-level distribution with no degenerate single-value or all-null state, confirming that one-hot encoding will produce meaningful binary columns rather than zero-variance noise."""

CELL_EDA_BIVARIATE = """### **Exploratory Data Analysis — Bivariate Relationships**

**Process:** Scatter plots of each numeric feature against the target `Weekly_Revenue_USD` are rendered to surface obvious linear, monotone, or nonlinear relationships before committing to the model bake-off.

**Analysis:** `List_Price_USD` and `Promo_Price_USD` show strong positive monotone relationships with revenue; `Shelf_Facings` and `Store_Sq_Ft` show positive but noisier relationships. `Weekly_Units_Sold` shows the strongest relationship of all — visual confirmation of the target-leakage signal that motivates dropping it.

**Outcome:** Predictive signal is present across the legitimate numeric features; the leakage relationship is visually obvious and gets dropped before modeling."""

CELL_CORRELATION_MATRIX = """### **Correlation Matrix**

**Process:** Pearson correlations among all numeric columns (including `Weekly_Units_Sold` and the target) are computed and rendered as a heatmap. Including the leakage column at this step makes the leakage signal numerically explicit before the feature-engineering cell drops it.

**Analysis:** `Weekly_Units_Sold` shows a near-1.0 correlation with `Weekly_Revenue_USD` — units × price approximately equals revenue. The legitimate predictors (`List_Price_USD`, `Promo_Price_USD`, `Shelf_Facings`, `Store_Sq_Ft`) show moderate positive correlations with the target.

**Outcome:** The leakage signal is now numerically established alongside the visual one, motivating the explicit drop in the Feature Engineering step."""

CELL_REVENUE_AGGREGATION = """### **Revenue Aggregation by Segment**

**Process:** Mean and total `Weekly_Revenue_USD` are computed for each level of the major categorical segments (`Department`, `Brand_Type`, `Store_Banner`, `Store_Region`).

**Analysis:** Each categorical segment shows directional revenue variation across its levels — different departments, banners, and regions sit at materially different revenue tiers, confirming that each categorical column carries usable signal.

**Outcome:** All major categorical features are retained for modeling; none collapse to a single-value or uniform-revenue distribution that would make them uninformative."""

CELL_TARGET_LEAKAGE_CALLOUT = """### **Target Leakage Callout — Why `Weekly_Units_Sold` is Dropped**

`Weekly_Units_Sold` is dropped from the feature set before any model is fit. It is present in the source dataset but is not a usable input feature.

**Mechanical reason:** Revenue is approximately `units × price`. Both `List_Price_USD` and `Promo_Price_USD` are already in the feature set, so a model handed `Weekly_Units_Sold` can recover the target almost exactly by multiplication. The correlation matrix above shows the near-1.0 correlation with the target.

**Business reason:** A revenue forecaster is meant to predict revenue *before* the week has occurred, from product and store attributes that are known in advance — price, weight, pack size, shelf facings, store size, region. A model that requires knowing units sold to predict revenue is not a forecaster; it is a calculator that requires the answer as an input.

**Process:** The drop is implemented in the Feature Engineering cell below. The column is retained in the EDA cells above so the leakage signal is visible to the reader, then explicitly removed before the model pipeline sees the data.

**Outcome:** All downstream modeling operates on product and store attributes only; `Weekly_Units_Sold` does not influence the trained models or their measured metrics."""

CELL_FEATURE_ENGINEERING = """### **Feature Engineering**

**Process:** Five transformations prepare the dataset for modeling. (1) `Weekly_Units_Sold` is dropped per the leakage callout above. (2) `UPC` is dropped (12-digit unique identifier whose cardinality would explode the feature matrix; product-level signal is carried by `Item_Description`, `Department`, and `Brand_Type`). (3) `discount_pct` is derived as `(List_Price - Promo_Price) / List_Price`. (4) `store_age` is derived from `Store_Open_Year` relative to a fixed reference year. (5) `is_promo` is derived as a binary indicator (`Promo_Price < List_Price`). `Store_Open_Year` is dropped after `store_age` is derived.

**Outcome:** The engineered feature set contains the product attributes (`Item_Description`, `Department`, `Brand_Type`, `Net_Weight_oz`, `Pack_Size`, `List_Price_USD`, `Promo_Price_USD`, `Shelf_Facings`), the store attributes (`Store_Number`, `Store_Banner`, `Store_Region`, `Store_Sq_Ft`), and the three derived features (`discount_pct`, `store_age`, `is_promo`) — plus the target `Weekly_Revenue_USD`."""

CELL_TRAIN_TEST_SPLIT = """### **Train / Test Split**

**Process:** The engineered dataset is split into 70% training and 30% holdout test, with a pinned random state for reproducibility. The test split is held back untouched — no model selection or hyperparameter tuning sees it.

**Outcome:** 6,216 training rows and 2,664 test rows. The 30% holdout is the final unbiased confirmation set; ranking happens on the training portion via cross-validation."""

CELL_PREPROCESSING_PIPELINE = """### **Preprocessing Pipeline**

**Process:** A `ColumnTransformer` applies median imputation to numeric columns and most-frequent imputation followed by one-hot encoding to categorical columns. The transformer is wrapped inside each model's `Pipeline` so cross-validation folds are preprocessed using only the fold's training portion.

**Outcome:** Each model sees a numerically clean, one-hot-encoded feature matrix; preprocessing leakage across folds is prevented by the pipeline structure. The fitted preprocessor is also serialized separately so the deployment frontend can transform user inputs identically."""

CELL_MODEL_DEFINITIONS = """### **Model Definitions and Hyperparameter Grids**

**Process:** Six regression estimators are defined for the bake-off (Decision Tree, Bagging, Random Forest, Gradient Boosting, XGBoost, CatBoost), each with a model-specific hyperparameter grid sized to keep the bake-off inside an 8–15 minute wall-clock on standard Colab CPU runtime. All estimators are pinned to a shared `RANDOM_STATE`; estimators run single-threaded so `GridSearchCV`'s outer parallelism controls overall concurrency.

**Outcome:** The grids are deliberately modest — depth in {3, 5, 7, None}, n_estimators in {100, 200}, learning rate in {0.05, 0.1}. The point of the bake-off is to compare model families on this dataset, not to push any single family to its limit."""

CELL_MODEL_EVAL_UTILITIES = """### **Model Evaluation Utilities**

**Process:** Two helper functions are defined. `get_metrics` returns RMSE, MAE, R², adjusted R², and MAPE for a `(y_true, y_pred)` pair labeled by subset name. `evaluate_model` runs the per-model flow: base fit, `GridSearchCV` on the training split, repeated K-fold cross-validation, tuned-model train/test metrics.

**Outcome:** Each model returns a structured dict that the bake-off loop aggregates. Repeated K-fold (5 splits × 2 repeats = 10 folds) is the primary ranking signal; the holdout test is reserved for final confirmation."""

CELL_MODEL_TRAINING_LOOP = """### **Model Training Loop**

**Process:** All six models are run through `evaluate_model` and their structured results collected into a `results` dict keyed by model name.

**Outcome:** The full bake-off completes inside the expected 8–15 minute Colab CPU wall-clock. The slowest single model is CatBoost; total wall time depends on the runtime's CPU count."""

CELL_MODEL_COMPARISON = """### **Model Comparison — Performance Aggregation**

**Process:** The per-model `results` dict is flattened into two DataFrames: `validation_perf_df` (repeated K-fold metrics) and `test_perf_df` (tuned-model holdout metrics). Both are sorted to make the ranking immediately readable.

**Analysis:** The validation ranking by RMSE is CatBoost (\\$15.14), XGBoost (\\$16.56), Gradient Boosting (\\$16.95), Bagging (\\$20.89), Random Forest (\\$20.91), Decision Tree (\\$28.76). The holdout ranking matches the validation ranking — no model swaps position between cross-validation and the held-out test set.

**Outcome:** CatBoost is the consistent top performer; XGBoost is consistently second. The other four candidates trail by a material margin and serve as context rather than as deployment options."""

CELL_PRIMARY_SECONDARY = """### **Primary and Secondary Model Selection**

**Process:** The two model frames are joined and the combined frame sorted by validation RMSE (primary ranking signal) with MAE, holdout RMSE, and R² as tie-breakers. The top-ranked model becomes the primary; the second-ranked becomes the secondary.

**Analysis:** **CatBoost** is selected as primary (validation RMSE \\$15.14, holdout R² 0.9465, holdout MAPE 11.21%). **XGBoost** is selected as secondary (validation RMSE \\$16.56, holdout R² 0.9384, holdout MAPE 12.59%).

**Outcome:** Both models advance to the test-set evaluation and serialization steps. The deployed frontend exposes the full six in an admin dropdown so the user can compare predictions across model families on the same row."""

CELL_TEST_SET_EVAL = """### **Test Set Evaluation — Primary Model**

**Process:** The primary model's predictions on the held-out test set are used to compute final RMSE, MAE, R², adjusted R², and MAPE. A predicted-vs-actual scatter plot is rendered alongside the metrics so residual structure is visible.

**Analysis:** CatBoost's test metrics are R² 0.9465, MAPE 11.21%, MAE \\$8.86, RMSE \\$14.04 on a mean actual of \\$81.22. The predicted-vs-actual scatter clusters tightly around the 45-degree reference line across the full revenue range, with no obvious heteroscedasticity or systematic bias at the high or low end.

**Outcome:** The held-out test confirms the cross-validation ranking. CatBoost is the lead deployment model."""

CELL_BUSINESS_ALIGNMENT = """### **Business Alignment and Tier Assignment**

**Process:** The v1.0 catalog quality-tier thresholds are applied to the measured test metrics, and each business opportunity from the Executive Summary is mapped to the metric that supports it.

**Analysis:** CatBoost's R² 0.9465 clears the Tier 1 R² bar (≥ 0.92); its MAPE 11.21% sits inside the Tier 2 MAPE band (≤ 12%) and just outside the Tier 1 MAPE bar (≤ 8%). The combined assignment is **Tier 2 (Shippable — Strong)** per the v1.0 threshold logic.

**Outcome:** The build is shippable. Forecasts are typically within roughly \\$9 of actual on rows averaging \\$81 — the band against which shelf-allocation, promotional-pricing, and inventory-flag decisions can be made."""

CELL_SERIALIZATION_PRIMARY_SECONDARY = """### **Model Serialization — Primary and Secondary**

**Process:** The primary and secondary fitted estimators are serialized to `joblib` files inside the engagement's `models/` directory. Filename pattern: `{model_slug}__hill-country-grocer.joblib`.

**Outcome:** `models/catboost__hill-country-grocer.joblib` and `models/xgboost__hill-country-grocer.joblib` are written. These are the two models a default deployment would load; the next cell extends serialization to all six candidates plus the preprocessor."""

CELL_SERIALIZATION_ALL = """### **Model Serialization — All Candidates and Preprocessor**

**Process:** All six trained candidates plus the fitted preprocessor are serialized to disk, and a `model_registry.json` is written alongside them. The registry records each model's slug, display name, test R², test MAPE, and the primary/secondary flags.

**Outcome:** The `models/` directory carries the six model joblibs, `preprocessor__hill-country-grocer.joblib`, and `model_registry.json`. The deployment cells below copy these artifacts into the two HF Space root directories and write the FastAPI inference service and Streamlit frontend that consume them."""

CELL_EXPANDED_EXEC_SUMMARY = """### **Expanded Executive Summary**

**TLDR**

A six-model regression bake-off across 8,880 weekly item-store sales records selected **CatBoost** as the lead model for Hill Country Grocer weekly revenue prediction, with test R² 0.9465, MAPE 11.21%, MAE \\$8.86, and RMSE \\$14.04 on a mean actual of \\$81.22 — Tier 2 (Shippable — Strong) per the v1.0 catalog thresholds. **XGBoost** is the parallel challenger (test R² 0.9384, MAPE 12.59%), retained for continued development and exposed alongside CatBoost in the deployed frontend's admin model-choice dropdown.

**Full Summary**

**Objective:** Build a deployable weekly-revenue forecaster for a multi-banner Texas regional grocery chain that gives category managers and inventory planners a defensible reference forecast for any item-store combination in the catalog, from product and store attributes that are known *before* the week begins (price, weight, pack size, shelf facings, store banner, region, age) — never from inputs that would only be known after the fact, like units sold.

**Iterative Development:** The build proceeded from a Decision Tree baseline (validation RMSE \\$28.76, R² 0.798) through a bagging family (Bagging and Random Forest at validation RMSE around \\$20.9, R² approximately 0.893) to the gradient-boosting family (Gradient Boosting at \\$16.95, XGBoost at \\$16.56, CatBoost at \\$15.14, R² 0.944 on cross-validation). The progression confirms that this dataset rewards the boosted-tree family over the bagging family and the single-tree baseline; the validation ranking matched the holdout ranking with no position swaps.

**Performance Analysis:** CatBoost wins on every metric examined — validation RMSE, holdout RMSE, holdout MAE, holdout MAPE, holdout R², and holdout adjusted R². XGBoost trails by roughly 0.8 percentage points of R² and 1.4 percentage points of MAPE on the held-out test set; the gap is consistent across cross-validation and holdout, not a single-split artifact. The remaining four candidates (Gradient Boosting, Bagging, Random Forest, Decision Tree) trail both CatBoost and XGBoost by a material margin and are retained as part of the bake-off record rather than as deployment options.

**Economic Impact:** MAPE 11.21% on a mean actual of \\$81.22 corresponds to MAE \\$8.86 — typical forecasts land within roughly \\$9 of actual weekly revenue per item-store row. For a regional grocer planning shelf allocation, promotional pricing, and inventory reorder across thousands of item-store combinations, that band supports defensible operational decisions: shelf-allocation reviews, promotional-pricing sign-off, and inventory-flag rules all sit inside the model's measured noise floor rather than being driven by per-row guesswork. Discrepancies of more than roughly 22% between forecast and actual (twice the noise floor) become a sortable list of action items for category review.

**Deployment Readiness:** All six trained candidates are serialized via `joblib` alongside the fitted preprocessor and a `model_registry.json` that records each model's slug, display name, test metrics, and primary/secondary flags. The deployment cells below produce the two HF Space asset directories (`deployment/backend_space_root/` and `deployment/frontend_space_root/`) on the next notebook execution: the backend Space runs a FastAPI inference service that loads the six joblibs plus the preprocessor; the frontend Space runs a Streamlit app that exposes an existing-store mode (operator picks a store from a dropdown populated by the training data's distinct stores) and a new-store mode (operator enters store attributes manually), plus an admin model-choice dropdown across the six candidates. **Enterprise:** deploy CatBoost as the production model; maintain XGBoost as a parallel challenger in shadow mode; revisit the comparison quarterly. **SMB:** deploy CatBoost; treat XGBoost as the secondary option inside the frontend's admin dropdown rather than as a separate production track.

**Next Steps:** The open development question is how to elevate XGBoost (or another candidate) into a stronger contender against CatBoost. Two paths to test: (1) additional feature engineering — interaction features between store attributes and product attributes, banner-region-department triple-encoded segments, or week-over-week lag features derived from historical revenue at the same item-store level (introducing temporal validation alongside it); (2) deeper hyperparameter exploration on XGBoost specifically — broader `learning_rate` / `n_estimators` / `max_depth` / `min_child_weight` / regularization grids than the modest bake-off grid carried here. Expanding the training set as new weekly data accumulates is the third path; CatBoost's lead may compress or widen with more rows."""


# ===========================================================================
# Deployment section (inserted between Model Serialization All Candidates code
# cell and the Expanded Executive Summary).
# ===========================================================================

CELL_DEPLOYMENT_OVERVIEW = """### **Deployment Assets**

**Process:** The three code cells below write the asset directories for two Hugging Face Spaces: a backend FastAPI inference service and a frontend Streamlit user interface. The backend Space loads the six serialized models plus the preprocessor and exposes them behind a JSON `POST /v1/predict` endpoint; the frontend Space presents an interactive forecaster with an existing-store mode, a new-store mode, and an admin model-choice dropdown across all six candidates. Locked Space names: `evagaiml/hill-country-grocer-revenue-pred-backend` and `evagaiml/hill-country-grocer-revenue-pred-frontend`. The notebook produces the asset directories; pushing them to Hugging Face is a separate step handled outside the notebook.

**Outcome:** After this section runs, `deployment/backend_space_root/` and `deployment/frontend_space_root/` carry every file each Space needs to start. The final code cell prints the resulting directory tree so the operator can verify the contents before pushing."""

CELL_BACKEND_INTRO = """### **Write Backend Space Assets**

**Process:** The backend Space root receives `app.py` (FastAPI inference service), `requirements.txt`, `Dockerfile`, `model_metadata.json`, and copies of the six model joblibs plus the preprocessor. Each text-format file is written via `textwrap.dedent` rather than embedded as a single triple-quoted blob, to avoid escape-character collisions when the embedded source itself contains Python string literals. The model artifacts are copied from the engagement's `models/` directory populated by the preceding serialization cells.

**Outcome:** The backend Space root is fully populated and ready to be pushed to `evagaiml/hill-country-grocer-revenue-pred-backend`."""

CELL_BACKEND_CODE = """# ------------------------------
# WRITE BACKEND SPACE ASSETS
# ------------------------------
# Materialize the backend HF Space directory: FastAPI app, requirements,
# Dockerfile, model_metadata.json, and the six serialized models plus the
# fitted preprocessor copied from models/.

import os
import json
import shutil
import textwrap

BACKEND_ROOT = "deployment/backend_space_root"
os.makedirs(BACKEND_ROOT, exist_ok=True)

# ---- 1. app.py (FastAPI inference service) ----
# Top-of-file documentation is written as ``#`` comments to keep this cell's
# outer source free of triple-quote nesting.
app_py = textwrap.dedent('''
    # FastAPI inference service for the Hill Country Grocer weekly revenue
    # forecaster. Loads the six serialized models plus the fitted preprocessor
    # and exposes them behind GET / (root info), GET /health (health check),
    # and POST /v1/predict (inference). The frontend Streamlit app at
    # evagaiml/hill-country-grocer-revenue-pred-frontend calls /v1/predict
    # with a JSON body specifying the model and one feature row per prediction.

    import json
    from typing import Any, Dict

    import joblib
    import pandas as pd
    from fastapi import FastAPI, HTTPException

    app = FastAPI(title="Hill Country Grocer Revenue Forecaster")

    with open("model_metadata.json", "r") as fh:
        METADATA = json.load(fh)

    PRIMARY_LABEL = METADATA["primary_label"]
    SECONDARY_LABEL = METADATA["secondary_label"]
    REGISTRY = METADATA["registry"]

    MODELS = {
        entry["display_name"]: joblib.load(entry["file"])
        for entry in REGISTRY["models"]
    }


    @app.get("/")
    def read_root() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "service": "hill-country-grocer-revenue-pred-backend",
            "primary_model": PRIMARY_LABEL,
            "secondary_model": SECONDARY_LABEL,
            "available_models": list(MODELS.keys()),
        }


    @app.get("/health")
    def health_check() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "primary_model": PRIMARY_LABEL,
            "secondary_model": SECONDARY_LABEL,
        }


    @app.post("/v1/predict")
    async def predict(request_body: Dict[str, Any]) -> Dict[str, Any]:
        model_name = request_body.get("model", PRIMARY_LABEL)
        rows = request_body.get("rows", [])

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="No feature rows provided for prediction.",
            )
        model = MODELS.get(model_name)
        if model is None:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_name}' not found. Available: {list(MODELS.keys())}",
            )
        try:
            df = pd.DataFrame(rows)
            predictions = [float(p) for p in model.predict(df).tolist()]
            return {
                "model_used": model_name,
                "predictions": predictions,
                "n_rows": len(predictions),
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
''').lstrip()

with open(os.path.join(BACKEND_ROOT, "app.py"), "w") as fh:
    fh.write(app_py)
print(f"  Wrote {BACKEND_ROOT}/app.py")

# ---- 2. requirements.txt ----
requirements_txt = textwrap.dedent('''
    fastapi==0.111.0
    uvicorn[standard]==0.30.1
    pydantic==2.7.4
    pandas==2.2.2
    numpy==2.0.2
    scikit-learn==1.6.1
    xgboost==2.1.4
    catboost==1.2.8
    joblib==1.4.2
''').lstrip()

with open(os.path.join(BACKEND_ROOT, "requirements.txt"), "w") as fh:
    fh.write(requirements_txt)
print(f"  Wrote {BACKEND_ROOT}/requirements.txt")

# ---- 3. Dockerfile ----
dockerfile = textwrap.dedent('''
    FROM python:3.12-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . .

    EXPOSE 7860
    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
''').lstrip()

with open(os.path.join(BACKEND_ROOT, "Dockerfile"), "w") as fh:
    fh.write(dockerfile)
print(f"  Wrote {BACKEND_ROOT}/Dockerfile")

# ---- 4. model_metadata.json (combines primary/secondary labels + full registry) ----
with open("models/model_registry.json", "r") as fh:
    full_registry = json.load(fh)

primary_label = next(
    m["display_name"] for m in full_registry["models"] if m["is_primary"]
)
secondary_label = next(
    m["display_name"] for m in full_registry["models"] if m["is_secondary"]
)

metadata = {
    "primary_label": primary_label,
    "secondary_label": secondary_label,
    "registry": full_registry,
}

with open(os.path.join(BACKEND_ROOT, "model_metadata.json"), "w") as fh:
    json.dump(metadata, fh, indent=2)
print(f"  Wrote {BACKEND_ROOT}/model_metadata.json (primary={primary_label}, secondary={secondary_label})")

# ---- 5. Copy model artifacts ----
model_files = [
    "catboost__hill-country-grocer.joblib",
    "xgboost__hill-country-grocer.joblib",
    "gradient-boosting__hill-country-grocer.joblib",
    "bagging__hill-country-grocer.joblib",
    "random-forest__hill-country-grocer.joblib",
    "decision-tree__hill-country-grocer.joblib",
    "preprocessor__hill-country-grocer.joblib",
]

for fname in model_files:
    src = os.path.join("models", fname)
    dst = os.path.join(BACKEND_ROOT, fname)
    shutil.copy(src, dst)
    print(f"  Copied {src} -> {dst}")

print("\\nBackend Space root populated.")"""


CELL_FRONTEND_INTRO = """### **Write Frontend Space Assets**

**Process:** The frontend Space root receives `src/streamlit_app.py` (Streamlit UI) and `requirements.txt`. The Streamlit app loads the Hill Country Grocer CSV at startup (cached via `@st.cache_data`) and uses the distinct values from the training data to populate the existing-store dropdown plus the categorical select widgets. An admin model-choice dropdown lets the operator pick any of the six serialized candidates; the default is CatBoost. The app calls the backend Space's `/v1/predict` endpoint, pinned to the locked Space name.

**Outcome:** The frontend Space root is fully populated and ready to be pushed to `evagaiml/hill-country-grocer-revenue-pred-frontend`."""

CELL_FRONTEND_CODE = """# ------------------------------
# WRITE FRONTEND SPACE ASSETS
# ------------------------------
# Materialize the frontend HF Space directory: Streamlit UI at
# src/streamlit_app.py plus requirements.txt.

import os
import textwrap

FRONTEND_ROOT = "deployment/frontend_space_root"
os.makedirs(os.path.join(FRONTEND_ROOT, "src"), exist_ok=True)

# ---- 1. src/streamlit_app.py ----
streamlit_app_py = textwrap.dedent('''
    # Streamlit frontend for the Hill Country Grocer weekly revenue forecaster.
    #
    # Modes:
    #   - Existing store: pick from the chain's known stores; remaining store
    #     attributes are inferred from the training data for that store.
    #   - New store: enter every store attribute by hand.
    #
    # Always: pick an admin model from the six serialized candidates (default
    # CatBoost). Calls the backend Space's /v1/predict endpoint with one
    # feature row per request.

    from typing import Any, Dict

    import pandas as pd
    import requests
    import streamlit as st

    BACKEND_URL = "https://evagaiml-hill-country-grocer-revenue-pred-backend.hf.space/v1/predict"
    DATA_URL = (
        "https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data"
        "/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp"
        "/data/raw/hill_country_grocer_weekly_sales.csv"
    )

    MODEL_OPTIONS = [
        "CatBoost",
        "XGBoost",
        "Gradient Boosting",
        "Random Forest",
        "Bagging",
        "Decision Tree",
    ]


    @st.cache_data
    def load_reference_data() -> pd.DataFrame:
        return pd.read_csv(DATA_URL)


    def build_feature_row(
        item_description: str,
        department: str,
        brand_type: str,
        net_weight_oz: float,
        pack_size: int,
        list_price: float,
        promo_price: float,
        shelf_facings: int,
        store_number: str,
        store_banner: str,
        store_region: str,
        store_sq_ft: int,
        store_open_year: int,
    ) -> Dict[str, Any]:
        list_price_safe = max(list_price, 0.01)
        discount_pct = (list_price - promo_price) / list_price_safe
        store_age = 2025 - store_open_year
        is_promo = 1 if promo_price < list_price else 0
        return {
            "Item_Description": item_description,
            "Department": department,
            "Brand_Type": brand_type,
            "Net_Weight_oz": net_weight_oz,
            "Pack_Size": pack_size,
            "List_Price_USD": list_price,
            "Promo_Price_USD": promo_price,
            "Shelf_Facings": shelf_facings,
            "Store_Number": store_number,
            "Store_Banner": store_banner,
            "Store_Region": store_region,
            "Store_Sq_Ft": store_sq_ft,
            "discount_pct": discount_pct,
            "store_age": store_age,
            "is_promo": is_promo,
        }


    def main() -> None:
        st.title("Hill Country Grocer — Weekly Revenue Forecaster")
        st.write(
            "Forecast Weekly_Revenue_USD for a single item-store combination "
            "from product and store attributes. Pick a store mode and a model below."
        )

        df = load_reference_data()
        departments = sorted(df["Department"].dropna().unique().tolist())
        brand_types = sorted(df["Brand_Type"].dropna().unique().tolist())
        store_numbers = sorted(df["Store_Number"].dropna().astype(str).unique().tolist())
        store_banners = sorted(df["Store_Banner"].dropna().unique().tolist())
        store_regions = sorted(df["Store_Region"].dropna().unique().tolist())
        item_descriptions = sorted(df["Item_Description"].dropna().unique().tolist())

        store_mode = st.radio("Store mode", options=["Existing store", "New store"], horizontal=True)

        st.subheader("Store attributes")
        if store_mode == "Existing store":
            store_number = st.selectbox("Store_Number", store_numbers)
            store_row = df[df["Store_Number"].astype(str) == str(store_number)].iloc[0]
            store_banner = store_row["Store_Banner"]
            store_region = store_row["Store_Region"]
            store_sq_ft = int(store_row["Store_Sq_Ft"])
            store_open_year = int(store_row["Store_Open_Year"])
            st.write(
                f"Banner: **{store_banner}**  |  Region: **{store_region}**  |  "
                f"Sq ft: **{store_sq_ft:,}**  |  Opened: **{store_open_year}**"
            )
        else:
            store_number = st.text_input("Store_Number", value="NEW_STORE_001")
            store_banner = st.selectbox("Store_Banner", store_banners)
            store_region = st.selectbox("Store_Region", store_regions)
            store_sq_ft = st.number_input(
                "Store_Sq_Ft", min_value=5000, max_value=200000, value=40000, step=1000
            )
            store_open_year = st.number_input(
                "Store_Open_Year", min_value=1950, max_value=2025, value=2010, step=1
            )

        st.subheader("Product attributes")
        item_description = st.selectbox("Item_Description", item_descriptions)
        department = st.selectbox("Department", departments)
        brand_type = st.selectbox("Brand_Type", brand_types)
        net_weight_oz = st.number_input(
            "Net_Weight_oz", min_value=0.1, max_value=1000.0, value=16.0, step=0.1
        )
        pack_size = st.number_input("Pack_Size", min_value=1, max_value=144, value=1, step=1)
        list_price = st.number_input(
            "List_Price_USD", min_value=0.01, max_value=1000.0, value=3.99, step=0.01
        )
        promo_price = st.number_input(
            "Promo_Price_USD", min_value=0.01, max_value=1000.0, value=3.49, step=0.01
        )
        shelf_facings = st.number_input(
            "Shelf_Facings", min_value=1, max_value=50, value=4, step=1
        )

        st.subheader("Model")
        model_choice = st.selectbox(
            "Admin: model choice across the six candidates", MODEL_OPTIONS, index=0
        )

        if st.button("Predict weekly revenue"):
            row = build_feature_row(
                item_description=item_description,
                department=department,
                brand_type=brand_type,
                net_weight_oz=float(net_weight_oz),
                pack_size=int(pack_size),
                list_price=float(list_price),
                promo_price=float(promo_price),
                shelf_facings=int(shelf_facings),
                store_number=str(store_number),
                store_banner=str(store_banner),
                store_region=str(store_region),
                store_sq_ft=int(store_sq_ft),
                store_open_year=int(store_open_year),
            )
            payload = {"model": model_choice, "rows": [row]}
            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()
                prediction = result["predictions"][0]
                st.success(f"Predicted Weekly_Revenue_USD: ${prediction:,.2f}")
                st.write(f"Model used: **{result['model_used']}**")
            except requests.exceptions.RequestException as exc:
                st.error(f"Backend request failed: {exc}")


    if __name__ == "__main__":
        main()
''').lstrip()

with open(os.path.join(FRONTEND_ROOT, "src", "streamlit_app.py"), "w") as fh:
    fh.write(streamlit_app_py)
print(f"  Wrote {FRONTEND_ROOT}/src/streamlit_app.py")

# ---- 2. requirements.txt ----
requirements_txt = textwrap.dedent('''
    streamlit==1.43.2
    requests==2.32.3
    pandas==2.2.2
''').lstrip()

with open(os.path.join(FRONTEND_ROOT, "requirements.txt"), "w") as fh:
    fh.write(requirements_txt)
print(f"  Wrote {FRONTEND_ROOT}/requirements.txt")

print("\\nFrontend Space root populated.")"""


CELL_SANITY_INTRO = """### **Verify Deployment Asset Tree**

**Process:** A single recursive listing prints every file under `deployment/backend_space_root/` and `deployment/frontend_space_root/` so the operator can verify the asset trees before pushing each Space to Hugging Face.

**Outcome:** Both directory trees are visible inline. Any missing file (missing model joblib, missing requirements.txt, missing streamlit_app.py) is immediately apparent."""

CELL_SANITY_CODE = """# ------------------------------
# VERIFY DEPLOYMENT ASSET TREE
# ------------------------------
# Walk the two Space root directories and print every file with its size.

import os

def _print_tree(root):
    print(f"\\n{root}/")
    if not os.path.isdir(root):
        print("  (directory does not exist)")
        return
    for dirpath, _dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        for fname in sorted(filenames):
            full = os.path.join(dirpath, fname)
            size_kb = os.path.getsize(full) / 1024
            rel_path = fname if rel_dir == "." else os.path.join(rel_dir, fname)
            print(f"  {rel_path}  ({size_kb:,.1f} KB)")

for space_root in ("deployment/backend_space_root", "deployment/frontend_space_root"):
    _print_tree(space_root)

print("\\nIf any expected file is missing, re-run the two write cells above before pushing to Hugging Face.")"""


# ===========================================================================
# Rewrite plan
# ===========================================================================
# Indexed by OLD cell index. Values are either:
#   ("replace", new_source)  — replace the source of the markdown cell at this index
#   ("drop", None)           — delete this cell
#   ("keep", None)           — leave the cell exactly as-is

REWRITE_PLAN: Dict[int, Any] = {
    0:  ("keep", None),
    1:  ("replace", CELL_COMBINED_TOP),
    2:  ("drop", None),
    3:  ("drop", None),
    4:  ("replace", CELL_CODE_EXECUTION_DIVIDER),
    5:  ("keep", None),
    6:  ("replace", CELL_LIBRARY_INSTALLATION),
    7:  ("keep", None),
    8:  ("replace", CELL_IMPORTS),
    9:  ("keep", None),
    10: ("replace", CELL_DATA_INGESTION),
    11: ("keep", None),
    12: ("replace", CELL_DATA_CHECKPOINT),
    13: ("keep", None),
    14: ("replace", CELL_DATA_UNDERSTANDING),
    15: ("keep", None),
    16: ("replace", CELL_DATA_QUALITY),
    17: ("keep", None),
    18: ("replace", CELL_EDA_UNIVARIATE_NUMERIC),
    19: ("keep", None),
    20: ("replace", CELL_EDA_UNIVARIATE_CATEGORICAL),
    21: ("keep", None),
    22: ("replace", CELL_EDA_BIVARIATE),
    23: ("keep", None),
    24: ("replace", CELL_CORRELATION_MATRIX),
    25: ("keep", None),
    26: ("replace", CELL_REVENUE_AGGREGATION),
    27: ("keep", None),
    28: ("replace", CELL_TARGET_LEAKAGE_CALLOUT),
    29: ("replace", CELL_FEATURE_ENGINEERING),
    30: ("keep", None),
    31: ("replace", CELL_TRAIN_TEST_SPLIT),
    32: ("keep", None),
    33: ("replace", CELL_PREPROCESSING_PIPELINE),
    34: ("keep", None),
    35: ("replace", CELL_MODEL_DEFINITIONS),
    36: ("keep", None),
    37: ("replace", CELL_MODEL_EVAL_UTILITIES),
    38: ("keep", None),
    39: ("replace", CELL_MODEL_TRAINING_LOOP),
    40: ("keep", None),
    41: ("replace", CELL_MODEL_COMPARISON),
    42: ("keep", None),
    43: ("replace", CELL_PRIMARY_SECONDARY),
    44: ("keep", None),
    45: ("replace", CELL_TEST_SET_EVAL),
    46: ("keep", None),
    47: ("keep", None),
    48: ("replace", CELL_BUSINESS_ALIGNMENT),
    49: ("keep", None),
    50: ("replace", CELL_SERIALIZATION_PRIMARY_SECONDARY),
    51: ("keep", None),
    52: ("replace", CELL_SERIALIZATION_ALL),
    53: ("keep", None),
    54: ("replace", CELL_EXPANDED_EXEC_SUMMARY),
}

DEPLOYMENT_CELLS = [
    ("markdown", CELL_DEPLOYMENT_OVERVIEW),
    ("markdown", CELL_BACKEND_INTRO),
    ("code",     CELL_BACKEND_CODE),
    ("markdown", CELL_FRONTEND_INTRO),
    ("code",     CELL_FRONTEND_CODE),
    ("markdown", CELL_SANITY_INTRO),
    ("code",     CELL_SANITY_CODE),
]


def _new_markdown_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def _new_code_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def _set_source(cell: Dict[str, Any], new_source: str) -> None:
    cell["source"] = new_source.splitlines(keepends=True)


def transform(nb: Dict[str, Any]) -> Dict[str, Any]:
    old_cells: List[Dict[str, Any]] = nb["cells"]

    if len(old_cells) != 55:
        raise SystemExit(
            f"Pre-flight failure: expected 55 input cells, found {len(old_cells)}. "
            "Restore from /tmp/hill_country_pre_pass2.ipynb and investigate."
        )

    rewritten: List[Dict[str, Any]] = []
    for idx, cell in enumerate(old_cells):
        action, payload = REWRITE_PLAN.get(idx, ("keep", None))
        if action == "drop":
            continue
        if action == "replace":
            assert cell["cell_type"] == "markdown", (
                f"Refusing to replace source on non-markdown cell at old index {idx}"
            )
            _set_source(cell, payload)
            rewritten.append(cell)
        elif action == "keep":
            rewritten.append(cell)
        else:
            raise SystemExit(f"Unknown rewrite action {action!r} at old index {idx}")

    # Insert deployment cells before the final cell (Expanded Exec Summary).
    final_cell = rewritten.pop()
    for cell_type, source in DEPLOYMENT_CELLS:
        if cell_type == "markdown":
            rewritten.append(_new_markdown_cell(source))
        elif cell_type == "code":
            rewritten.append(_new_code_cell(source))
        else:
            raise SystemExit(f"Unknown deployment cell type {cell_type!r}")
    rewritten.append(final_cell)

    nb["cells"] = rewritten
    return nb


# ---------------------------------------------------------------------------
# Post-condition checks
# ---------------------------------------------------------------------------

FORBIDDEN_TERMS = ("synthetic", "honest framing", "rigorous", "thorough", "careful methodology")
EXPECTED_TOTAL_CELLS = 60
EXPECTED_MD_CELLS = 33
EXPECTED_CODE_CELLS = 27
PRESERVED_EXECUTION_COUNTS = list(range(1, 25))


def post_condition_checks(nb: Dict[str, Any]) -> None:
    cells = nb["cells"]
    md_count = sum(1 for c in cells if c["cell_type"] == "markdown")
    code_count = sum(1 for c in cells if c["cell_type"] == "code")

    assert len(cells) == EXPECTED_TOTAL_CELLS, (
        f"Cell count mismatch: expected {EXPECTED_TOTAL_CELLS}, got {len(cells)}"
    )
    assert md_count == EXPECTED_MD_CELLS, (
        f"Markdown count mismatch: expected {EXPECTED_MD_CELLS}, got {md_count}"
    )
    assert code_count == EXPECTED_CODE_CELLS, (
        f"Code count mismatch: expected {EXPECTED_CODE_CELLS}, got {code_count}"
    )

    original_code_ecs: List[Any] = []
    new_code_count = 0
    for c in cells:
        if c["cell_type"] != "code":
            continue
        ec = c.get("execution_count")
        if ec is None:
            new_code_count += 1
            assert c.get("outputs", []) == [], (
                "New deployment code cell unexpectedly has outputs"
            )
        else:
            original_code_ecs.append(ec)

    assert original_code_ecs == PRESERVED_EXECUTION_COUNTS, (
        f"Original execution_count sequence not preserved: {original_code_ecs}"
    )
    assert new_code_count == 3, f"Expected 3 new code cells, got {new_code_count}"

    for idx, c in enumerate(cells):
        if c["cell_type"] != "markdown":
            continue
        text = "".join(c["source"]).lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                raise AssertionError(
                    f"Forbidden term {term!r} found in markdown cell at new index {idx}"
                )

    combined_top = "".join(cells[1]["source"])
    assert "evagaiml/hill-country-grocer-revenue-pred-frontend" in combined_top
    assert "evagaiml/hill-country-grocer-revenue-pred-backend" in combined_top


def main() -> int:
    if not NB_PATH.exists():
        print(f"ERROR: notebook not found at {NB_PATH}", file=sys.stderr)
        return 2

    with NB_PATH.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    nb = transform(nb)
    post_condition_checks(nb)

    with NB_PATH.open("w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    cells = nb["cells"]
    print(f"Rewrote {NB_PATH}")
    print(f"  Total cells: {len(cells)}")
    print(f"  Markdown:    {sum(1 for c in cells if c['cell_type']=='markdown')}")
    print(f"  Code:        {sum(1 for c in cells if c['cell_type']=='code')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
