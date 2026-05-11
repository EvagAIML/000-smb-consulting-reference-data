# Claude Code prompt — author `hill_country_grocer__reg__ensemble.ipynb`

You are authoring a new Colab notebook for the consulting-system reference build. The engagement is `ref-retail-revenue-pred__reg__ensemble-exp` and lives in the sibling repo `000-smb-consulting-reference-data`. Your working directory is `/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data`.

## Context

The previous run of this engagement used a 12-column retail CSV pulled from an external GitHub repo. That dataset has been replaced. The new dataset is a 16-column synthetic Hill Country Grocer (Texas regional grocer) panel that the operator generated in a previous Claude session. It is located at:

```
engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/hill_country_grocer_weekly_sales.csv
```

**Before you do anything else, verify this file exists and has the expected shape.** If it doesn't, halt and report — do not proceed.

Expected:
- 8,881 lines (1 header + 8,880 rows)
- File size ~1.38 MB
- MD5 `2c9fcb8b5494ac720097bb93eb6c8991`
- Header columns: `UPC, Item_Description, Department, Brand_Type, Net_Weight_oz, Pack_Size, List_Price_USD, Promo_Price_USD, Shelf_Facings, Store_Number, Store_Banner, Store_Region, Store_Sq_Ft, Store_Open_Year, Weekly_Units_Sold, Weekly_Revenue_USD`
- Target column: `Weekly_Revenue_USD`

## Authoritative references (read these first, in this order)

1. `/Users/eriksvagshenian/Desktop/000-smb-consulting-system-private/notebook-style-guide.md` — canonical authority on notebook structure, cell patterns, naming. Follow this strictly. The newer notebooks (visa, turbine, seed, medical) define the standard; retail is older and should NOT be used as the primary reference.

2. `/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data/engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/colab_authored.ipynb` — the prior generation of this engagement's notebook, written against the 12-column retail CSV. Use it for reference on cell sequencing and the ensemble architecture, but do NOT copy it cell-for-cell. The new dataset is different (16 columns, different feature semantics, weekly panel structure) and the new notebook must be authored from scratch against the new schema.

3. `/Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data/engagements/ref-retail-revenue-pred__reg__ensemble-exp/CLAUDE_CODE_INSTRUCTIONS.md` — task-1 work for the prior generation. Skim for context on engagement conventions; the task list itself is stale.

## What you are producing

A single new notebook file:

```
engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/hill_country_grocer__reg__ensemble.ipynb
```

This is the unexecuted authored notebook. Do NOT attempt to execute it locally — execution happens in Colab by the operator. Your job is to produce a well-formed `.ipynb` file with all cells in the correct sequence, populated, and conforming to the style guide.

The existing `colab_authored.ipynb` and `executed.ipynb` files in the same `notebooks/` folder must remain untouched. Your new file sits alongside them, it does not replace them.

## Notebook requirements

### Structure (per `notebook-style-guide.md`)

Every notebook must include, in this order:
- Title cell (markdown, `# **Use Case Name**: Problem Type Full Description`)
- Value Proposition (markdown, top)
- Executive Summary (markdown, top, short)
- 16-step model building lifecycle as cell sections — not every step needs to appear, but ordering is fixed
- Expanded Executive Summary (markdown, bottom)

Every markdown cell explaining a step must include **Summary/Process** and **Observations/Outcome** lines — no exceptions. Leave Observations/Outcome as a placeholder if the cell describes work that hasn't run yet (e.g. `_Observations/Outcome: to be populated after execution._`). Do not omit the line.

Every code cell must:
- Open with a `# -----` banner comment block
- Include a plain-English description directly under the banner
- Have an inline comment on every import explaining its purpose

### Modeling architecture

Regression problem. Target: `Weekly_Revenue_USD`. The notebook is an ensemble-experiment build (`__reg__ensemble-exp`). Use the same ensemble family as the prior `colab_authored.ipynb` (Random Forest, Gradient Boosting / XGBoost, possibly CatBoost or LightGBM as members) — but the implementation is yours to write against the new schema. Do NOT carry over feature-engineering code from the prior notebook without adapting it; the column semantics are different.

Feature notes specific to this dataset:
- `UPC` is a 12-digit identifier (high cardinality) — treat as categorical, do not numerically encode
- `Item_Description`, `Department`, `Brand_Type`, `Store_Number`, `Store_Banner`, `Store_Region` are categorical
- `Pack_Size`, `Net_Weight_oz`, `List_Price_USD`, `Promo_Price_USD`, `Shelf_Facings`, `Store_Sq_Ft`, `Store_Open_Year` are numeric
- **`Weekly_Units_Sold` MUST be dropped from the feature set.** Units sold × price effectively equals revenue, making it a target-leakage feature that trivializes prediction and is useless in deployment (a revenue forecaster requiring you to know units sold to predict revenue is not useful). The notebook should explicitly call out the leakage in the relevant markdown cell and document the drop as an intentional modeling choice.
- Derived features worth engineering: `discount_pct = (List_Price - Promo_Price) / List_Price`, `store_age = current_year - Store_Open_Year`, `is_promo = Promo_Price < List_Price`

### Target metric range (informational, not a gate)

The operator is targeting R² in the 0.85–0.95 range with MAPE 8–15% on this dataset. You are not expected to hit those numbers in authoring — actual values come from Colab execution. But if your modeling choices look like they'd land outside that range (e.g. linear regression only, no ensemble at all), reconsider.

### Naming convention

The notebook filename `hill_country_grocer__reg__ensemble.ipynb` is locked. Inside the notebook, the canonical engagement slug is `hill-country-grocer__reg__ensemble-exp` (note the engagement folder retains the older `ref-retail-revenue-pred` name for backward compatibility — do not rename the folder). Use the new slug in any in-notebook references to the build identity.

## Three halt points

**Halt 1 — after reading references, before authoring.** Once you've read the style guide, the prior `colab_authored.ipynb`, and verified the dataset is on disk, report back:
- A one-paragraph summary of the modeling approach you intend to take
- The list of cell sections you plan to author, in order
- Any ambiguities or disagreements with the prior notebook's approach that you want the operator to resolve

Wait for explicit operator approval before writing the notebook.

**Halt 2 — after authoring the notebook, before any git operations.** Once the `.ipynb` file is on disk, report:
- Cell count and total line count
- Confirmation that every markdown cell has Summary/Process and Observations/Outcome lines
- Confirmation that every code cell has a banner comment and inline import comments
- Any style-guide deviations and your reasoning for them

Do NOT commit or push. Wait for the operator to review the notebook in Jupyter / Colab and approve.

**Halt 3 — after operator approval, for the commit.** Once the operator says the notebook is good, commit it with this message:

```
Add Hill Country Grocer notebook: hill_country_grocer__reg__ensemble.ipynb

New 16-column synthetic Texas grocer dataset replaces prior 12-column retail
CSV for this engagement. Notebook authored fresh against new schema per
notebook-style-guide.md v2.1. Ensemble architecture (RF + GBM + variant).
Awaits Colab execution by operator.
```

Push to `origin main`. After push, report the commit SHA and confirm the file is visible on GitHub at the expected slug-pattern URL.

## What you do NOT do

- Do not execute the notebook
- Do not modify `colab_authored.ipynb` or `executed.ipynb`
- Do not touch any file under `models/`, `deployment/`, or `metadata/`
- Do not update `CLAUDE_CODE_INSTRUCTIONS.md` or `HF_DEPLOY_GUIDE.md`
- Do not modify `lessons/lessons.md` or `catalog/v1.yaml` in `000-smb-consulting-system-private` — those updates happen after Colab execution, in a separate task
- Do not commit anything before Halt 3

## If something is wrong

If at any point the dataset doesn't match the spec, the style guide reads differently than this prompt implies, or a code path you're about to take feels like it contradicts the operator's intent — halt and ask. The operator prefers a clarifying question over a wrong commit.

Begin with reading the three reference files and verifying the dataset on disk. Then halt at Halt 1.
