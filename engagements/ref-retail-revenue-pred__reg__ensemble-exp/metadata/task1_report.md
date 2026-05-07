# Task 1 Report — Dataset migration

**Engagement:** `ref-retail-revenue-pred__reg__ensemble-exp`
**Date:** 2026-05-07
**Authority:** `procedures/run-catalog-entry.md` v1.1
**Source URL:** `https://raw.githubusercontent.com/EvagAIML/020_Model_Deployment/main/RetailPrediction%20copy.csv`
**Destination path:** `engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv`

---

## 1. Local file verification

**File size:** `862264 bytes` (~842 KB) — within expected ~600 KB–1 MB range.

**`head -3` output:**

```
Product_Id,Product_Weight,Product_Sugar_Content,Product_Allocated_Area,Product_Type,Product_MRP,Store_Id,Store_Establishment_Year,Store_Size,Store_Location_City_Type,Store_Type,Product_Store_Sales_Total
FD6114,12.66,Low Sugar,0.027,Frozen Foods,117.08,OUT004,2009,Medium,Tier 2,Supermarket Type2,2842.4
FD7839,16.54,Low Sugar,0.144,Dairy,171.43,OUT003,1999,Medium,Tier 1,Departmental Store,4830.02
```

All 12 expected columns present in the expected order: `Product_Id`, `Product_Weight`, `Product_Sugar_Content`, `Product_Allocated_Area`, `Product_Type`, `Product_MRP`, `Store_Id`, `Store_Establishment_Year`, `Store_Size`, `Store_Location_City_Type`, `Store_Type`, `Product_Store_Sales_Total`.

Total line count: `8764` (header + 8,763 data rows).

---

## 2. LFS exclusion check

**Command:**

```
git -C /Users/eriksvagshenian/Desktop/000-smb-consulting-reference-data check-attr filter engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv
```

**Output:**

```
engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv: filter: unspecified
```

`filter: unspecified` confirms no `.gitattributes` rule assigns the LFS filter (or any other filter) to this path. The file is committed as raw bytes via Git's normal blob storage, not as an LFS pointer. A supplementary `git check-attr -a` returned empty output, confirming no attributes of any kind are set on the path.

---

## 3. Slug-pattern URL verification

**Command:**

```
curl -sI "https://raw.githubusercontent.com/EvagAIML/000-smb-consulting-reference-data/main/engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv"
```

**Response headers (full, verbatim from the second run — Fastly edge HIT, steady state):**

```
HTTP/2 200
cache-control: max-age=300
content-security-policy: default-src 'none'; style-src 'unsafe-inline'; sandbox
content-type: text/plain; charset=utf-8
etag: "8929809f9be1460fcc960133a6a5b0d807c93ec7057542917fc3f41848d60212"
strict-transport-security: max-age=31536000
x-content-type-options: nosniff
x-frame-options: deny
x-xss-protection: 1; mode=block
x-github-request-id: F5F8:2F91D0:37C0AC:438D0A:69FD02EE
accept-ranges: bytes
date: Thu, 07 May 2026 21:27:31 GMT
via: 1.1 varnish
x-served-by: cache-dfw-ktki8620066-DFW
x-cache: HIT
x-cache-hits: 0
x-timer: S1778189251.388921,VS0,VE2
vary: Authorization,Accept-Encoding
access-control-allow-origin: *
cross-origin-resource-policy: cross-origin
x-fastly-request-id: 733e7eff94845f980f5cb65ae5e48c3f0d0137a8
expires: Thu, 07 May 2026 21:32:31 GMT
source-age: 211
content-length: 862264
```

**Key signals:**

- `HTTP/2 200` — URL resolves.
- `content-type: text/plain; charset=utf-8` — served as text, not as an HTML error page or binary download.
- `content-length: 862264` — exact byte match with the local file. Not a ~130-byte LFS pointer.
- `cross-origin-resource-policy: cross-origin` — fetchable from a HuggingFace Space's runtime (matters for Task 2 when `pd.read_csv(url)` runs).
- `etag` was identical between two runs three minutes apart, confirming the same blob is being served.

---

## 4. Git commit and push

**Commit SHA (full):** `b78f71f423285b9790ed5fb31886a9295fdc9118`
**Commit SHA (short):** `b78f71f`
**Branch:** `main`
**Commit message:** `Add engagement: ref-retail-revenue-pred__reg__ensemble-exp (data + scaffolding — Task 1 of 3)`

**Files in commit:**

- `engagements/ref-retail-revenue-pred__reg__ensemble-exp/CLAUDE_CODE_INSTRUCTIONS.md`
- `engagements/ref-retail-revenue-pred__reg__ensemble-exp/HF_DEPLOY_GUIDE.md`
- `engagements/ref-retail-revenue-pred__reg__ensemble-exp/data/raw/retail_prediction.csv`
- `engagements/ref-retail-revenue-pred__reg__ensemble-exp/notebooks/working.ipynb`

The `working.ipynb` file was operator-staged in the engagement folder before this task ran; `git add` of the engagement folder picked it up. It will be replaced by `executed.ipynb` in Task 3e.

The pre-staged `.github/workflows/keep-alive-ref-retail-revenue-pred__reg__ensemble-exp.yml` was deliberately **not** included in this commit (deferred to Task 3h, per instructions, so the workflow's first cron run does not ping nonexistent Spaces).

**`git push origin main` output:**

```
To https://github.com/EvagAIML/000-smb-consulting-reference-data.git
   f80e4c6..b78f71f  main -> main
```

Push confirmed. `main` advanced from `f80e4c6` to `b78f71f`.

---

## 5. Summary

- Dataset downloaded from the source URL with HTTP 200 and full byte content.
- File matches the expected schema (12 columns) and row count (~8,800).
- File is committed as raw bytes, not as an LFS pointer (`filter: unspecified`).
- Commit `b78f71f` pushed to `origin/main`.
- Slug-pattern URL serves the file with HTTP 200, `text/plain`, and `content-length` matching the local file size byte-for-byte.

Task 1 is complete. Awaiting operator approval before proceeding to Task 2.
