import csv
import io
from typing import Any, Dict, List

import requests
import streamlit as st

BACKEND_URL = "https://EvagAIML-smb-retail-revenue-pred-backend.hf.space/v1/predict"
MODEL_OPTIONS = ["CatBoost", "Random Forest"]

NUMERIC_FIELDS = {
    "Product_Weight": float,
    "Product_Allocated_Area": float,
    "Product_MRP": float,
    "Store_Age_Years": float,
}

# Realistic lower bounds. These are slightly below the observed notebook minima
# to support scenario planning while still preventing unrealistic values.
MIN_RULES = {
    "Product_Weight": 2.0,
    "Product_Allocated_Area": 0.001,
    "Product_MRP": 20.0,
}

# Defaults for editable fields only.
DEFAULTS = {
    "Store_Id": "NEW_STORE",
    "Store_Type": "Supermarket Type2",
    "Store_Size": "Medium",
    "Store_Location_City_Type": "Tier 2",
    "Store_Age_Years": 23.0,
    "Product_Id_char": "FD",
    "Product_Weight": 12.65,
    "Product_Allocated_Area": 0.069,
    "Product_MRP": 147.03,
    "Product_Type": "Fruits and Vegetables",
    "Product_Sugar_Content": "Low Sugar",
}

STORE_PROFILES = {
    "OUT001": {
        "Store_Type": "Supermarket Type1",
        "Store_Size": "High",
        "Store_Location_City_Type": "Tier 2",
        "Store_Age_Years": 38,
    },
    "OUT002": {
        "Store_Type": "Food Mart",
        "Store_Size": "Small",
        "Store_Location_City_Type": "Tier 3",
        "Store_Age_Years": 27,
    },
    "OUT003": {
        "Store_Type": "Departmental Store",
        "Store_Size": "Medium",
        "Store_Location_City_Type": "Tier 1",
        "Store_Age_Years": 26,
    },
    "OUT004": {
        "Store_Type": "Supermarket Type2",
        "Store_Size": "Medium",
        "Store_Location_City_Type": "Tier 2",
        "Store_Age_Years": 16,
    },
}

STORE_OPTIONS = ["OUT001", "OUT002", "OUT003", "OUT004", "NEW_STORE"]
STORE_TYPE_OPTIONS = [
    "Departmental Store",
    "Food Mart",
    "Supermarket Type1",
    "Supermarket Type2",
]
STORE_SIZE_OPTIONS = ["Small", "Medium", "High"]
CITY_TIER_OPTIONS = ["Tier 1", "Tier 2", "Tier 3"]

PRODUCT_ID_CHAR_OPTIONS = ["FD", "NC", "DR"]
PRODUCT_TYPES = [
    "Baking Goods",
    "Breads",
    "Breakfast",
    "Canned",
    "Dairy",
    "Frozen Foods",
    "Fruits and Vegetables",
    "Hard Drinks",
    "Health and Hygiene",
    "Household",
    "Meat",
    "Others",
    "Seafood",
    "Snack Foods",
    "Soft Drinks",
    "Starchy Foods",
]
ALL_SUGAR_OPTIONS = ["Low Sugar", "Regular", "No Sugar"]

CATEGORY_TO_PRODUCT_TYPES = {
    "FD": [
        "Baking Goods",
        "Breads",
        "Breakfast",
        "Canned",
        "Dairy",
        "Frozen Foods",
        "Fruits and Vegetables",
        "Meat",
        "Seafood",
        "Snack Foods",
        "Starchy Foods",
    ],
    "NC": [
        "Health and Hygiene",
        "Household",
        "Others",
    ],
    "DR": [
        "Hard Drinks",
        "Soft Drinks",
    ],
}

CATEGORY_TO_SUGAR_CONTENT = {
    "FD": ["Low Sugar", "Regular"],
    "NC": ["No Sugar"],
    "DR": ["Low Sugar", "Regular"],
}

PERISHABLES = {
    "Dairy",
    "Meat",
    "Fruits and Vegetables",
    "Breakfast",
    "Breads",
    "Seafood",
    "Starchy Foods",
}

PRODUCT_CATEGORY_DISPLAY = {
    "FD": "Food (FD)",
    "NC": "Non-Consumable (NC)",
    "DR": "Drink (DR)",
}

STORE_DISPLAY = {
    "OUT001": "OUT001 (Supermarket Type1)",
    "OUT002": "OUT002 (Food Mart)",
    "OUT003": "OUT003 (Departmental Store)",
    "OUT004": "OUT004 (Supermarket Type2)",
    "NEW_STORE": "NEW_STORE (Custom store profile)",
}

STORE_SIZE_DISPLAY = {
    "Small": "Small (relative size band)",
    "Medium": "Medium (relative size band)",
    "High": "High (relative size band)",
}

CITY_TIER_DISPLAY = {
    "Tier 1": "Tier 1",
    "Tier 2": "Tier 2",
    "Tier 3": "Tier 3",
}


def derive_product_type_category(product_type: str) -> str:
    return "Perishables" if product_type in PERISHABLES else "Non Perishables"


def enrich_store_fields(row: Dict[str, Any]) -> Dict[str, Any]:
    store_id = row.get("Store_Id", "NEW_STORE")
    if store_id in STORE_PROFILES:
        row.update(STORE_PROFILES[store_id])
    return row


def _coerce_row_types(row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            continue

        if key in NUMERIC_FIELDS:
            try:
                out[key] = NUMERIC_FIELDS[key](value)
            except Exception:
                out[key] = value
        else:
            out[key] = value

    if out.get("Product_Sugar_Content") == "reg":
        out["Product_Sugar_Content"] = "Regular"

    store_id = out.get("Store_Id", "NEW_STORE")
    out["Store_Id"] = store_id if store_id else "NEW_STORE"
    out = enrich_store_fields(out)

    if "Product_Type" in out and "Product_Type_Category" not in out:
        out["Product_Type_Category"] = derive_product_type_category(out["Product_Type"])

    return out


def validate_business_row(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for field, minimum in MIN_RULES.items():
        value = row.get(field)
        if value is None:
            errors.append(f"{field} is required.")
            continue
        try:
            numeric_value = float(value)
        except Exception:
            errors.append(f"{field} must be numeric.")
            continue

        if numeric_value < minimum:
            errors.append(f"{field} must be at least {minimum}.")

    category = row.get("Product_Id_char")
    product_type = row.get("Product_Type")
    sugar_content = row.get("Product_Sugar_Content")

    if category in CATEGORY_TO_PRODUCT_TYPES:
        valid_types = CATEGORY_TO_PRODUCT_TYPES[category]
        if product_type not in valid_types:
            errors.append(
                f"Product_Type must be valid for Product_Id_char={category}."
            )

    if category in CATEGORY_TO_SUGAR_CONTENT:
        valid_sugar = CATEGORY_TO_SUGAR_CONTENT[category]
        if sugar_content not in valid_sugar:
            errors.append(
                f"Product_Sugar_Content must be valid for Product_Id_char={category}."
            )

    return errors


def rows_to_csv_string(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def call_backend(model_name: str, rows: List[Dict[str, Any]], timeout_s: int = 60) -> Dict[str, Any]:
    payload = {"model": model_name, "rows": rows}
    response = requests.post(BACKEND_URL, json=payload, timeout=timeout_s)
    if response.status_code != 200:
        raise RuntimeError(f"Backend error ({response.status_code}): {response.text}")
    return response.json()


def field_header(title: str, csv_name: str = "", meta: str = "") -> None:
    subtitle_parts = []
    if csv_name:
        subtitle_parts.append(f"csv: {csv_name}")
    if meta:
        subtitle_parts.append(meta)
    subtitle = " · ".join(subtitle_parts)

    st.markdown(
        f'''
        <div class="form-field-header">
            <div class="form-field-title">{title}</div>
            <div class="form-field-subtitle">{subtitle}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def admin_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'''
        <div class="form-field-header">
            <div class="form-field-title">{title}</div>
            <div class="form-field-subtitle">{subtitle}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_unavailable(label: str, values: List[str]) -> None:
    if not values:
        return
    st.markdown(
        (
            '<div class="form-field-unavailable">'
            f'{label}: {", ".join(values)}'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Retail Revenue Forecast", layout="centered")

st.markdown(
    '''
    <style>
        .form-field-header {
            margin-top: 1.35rem;
            margin-bottom: 0.65rem;
        }

        .form-field-title {
            font-size: 1.55rem;
            font-weight: 700;
            line-height: 1.2;
            color: inherit;
            margin-bottom: 0.2rem;
        }

        .form-field-subtitle {
            font-size: 0.95rem;
            line-height: 1.35;
            color: #6b7280;
        }

        .form-field-unavailable {
            opacity: 0.55;
            font-size: 0.98rem;
            line-height: 1.5;
            margin-top: -0.15rem;
            margin-bottom: 1.25rem;
            color: #6b7280;
        }

        .section-gap {
            margin-top: 2.5rem;
        }

        .batch-total-note {
            color: #6b7280;
            font-size: 0.95rem;
            margin-top: -0.35rem;
            margin-bottom: 0.9rem;
        }

        .stSelectbox div[data-baseweb="select"] > div,
        .stTextInput div[data-baseweb="input"] > div,
        .stNumberInput div[data-baseweb="input"] > div {
            min-height: 4.3rem;
        }

        .stSelectbox div[data-baseweb="select"] span,
        .stTextInput input,
        .stNumberInput input {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 1.08rem;
        }

        .stSelectbox,
        .stTextInput,
        .stNumberInput,
        .stFileUploader {
            margin-bottom: 1.2rem;
        }

        @media (max-width: 640px) {
            .stSelectbox div[data-baseweb="select"] > div,
            .stTextInput div[data-baseweb="input"] > div,
            .stNumberInput div[data-baseweb="input"] > div {
                min-height: 4rem;
            }

            .stSelectbox div[data-baseweb="select"] span,
            .stTextInput input,
            .stNumberInput input {
                font-size: 1rem;
            }
        }
    </style>
    ''',
    unsafe_allow_html=True,
)

st.title("Retail Revenue Forecast")
st.caption(
    "Predict product-store revenue using the live backend API. Supports single prediction, "
    "batch scoring, and top-two model switching."
)

st.divider()
st.subheader("Administration")

admin_header("Forecasting Model", "Select the deployed model used for prediction.")
model_choice = st.selectbox(
    "Forecasting Model",
    MODEL_OPTIONS,
    index=0,
    key="model_choice",
    label_visibility="collapsed",
)

show_raw = st.checkbox("Show raw JSON response", value=False, key="show_raw")

admin_header(
    "Batch Prediction File",
    "Upload a CSV with raw training column names so the backend can map the rows directly.",
)
uploaded = st.file_uploader(
    "Batch Prediction File",
    type=["csv"],
    key="csv_uploader",
    label_visibility="collapsed",
)

if uploaded is not None:
    try:
        raw = uploaded.getvalue().decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(raw))
        rows_in = [row for row in reader]

        if not rows_in:
            st.warning("No rows found in CSV.")
        else:
            st.write("Detected columns:", reader.fieldnames)
            st.write("Preview (first 3 rows):")
            st.json(rows_in[:3])

            if st.button("Predict Batch", key="predict_batch"):
                prepared_rows = []
                validation_errors = []

                for idx, row_in in enumerate(rows_in, start=1):
                    prepared = _coerce_row_types(row_in)
                    row_errors = validate_business_row(prepared)
                    if row_errors:
                        validation_errors.append(
                            {"row_number": idx, "errors": row_errors}
                        )
                    prepared_rows.append(prepared)

                if validation_errors:
                    st.error("Batch validation failed. Fix the rows below before scoring.")
                    st.json(validation_errors[:20])
                else:
                    result = call_backend(model_choice, prepared_rows, timeout_s=60)
                    st.success(f"Batch prediction complete (Model: {result.get('model_used', model_choice)})")

                    preds = result.get("predictions", [])
                    display_rows = []
                    for original_row, pred in zip(rows_in, preds):
                        new_row = dict(original_row)
                        new_row["Predicted_Revenue"] = pred
                        display_rows.append(new_row)

                    if display_rows:
                        st.write("Predictions:")
                        st.json(display_rows[:20])

                        csv_output = rows_to_csv_string(display_rows)
                        st.download_button(
                            label="Download Predictions as CSV",
                            data=csv_output,
                            file_name="predictions.csv",
                            mime="text/csv",
                            key="download_csv",
                        )

                    overall_total = result.get("overall_total")
                    if overall_total is not None:
                        st.metric("Overall Total Revenue", f"{float(overall_total):,.2f}")
                        st.markdown(
                            '<div class="batch-total-note">Calculated for Batch Predictions</div>',
                            unsafe_allow_html=True,
                        )

                    store_totals = result.get("store_totals", {})
                    if store_totals:
                        st.write("Batch Store Totals:", store_totals)

                    if show_raw:
                        st.json(result)

    except Exception as exc:
        st.error(f"Error processing batch: {exc}")

st.divider()
st.subheader("Single Prediction")

# Store section above product section
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
st.subheader("Store Information")

field_header("Store ID", "Store_Id", "Select a known store or choose a custom profile.")
store_id = st.selectbox(
    "Store ID",
    STORE_OPTIONS,
    index=STORE_OPTIONS.index(DEFAULTS["Store_Id"]),
    format_func=lambda v: STORE_DISPLAY.get(v, v),
    label_visibility="collapsed",
)

known_store = store_id in STORE_PROFILES
store_profile = STORE_PROFILES.get(store_id, {})

if known_store:
    store_type = store_profile["Store_Type"]
    store_size = store_profile["Store_Size"]
    store_city_tier = store_profile["Store_Location_City_Type"]
    store_age_years = float(store_profile["Store_Age_Years"])

    field_header("Store Type", "Store_Type", "Locked from Store ID.")
    st.text_input(
        "Store Type",
        value=store_type,
        disabled=True,
        label_visibility="collapsed",
    )

    field_header("Store Size", "Store_Size", "Categorical size band.")
    st.text_input(
        "Store Size",
        value=STORE_SIZE_DISPLAY.get(store_size, store_size),
        disabled=True,
        label_visibility="collapsed",
    )

    field_header("City Tier", "Store_Location_City_Type", "Categorical city tier.")
    st.text_input(
        "City Tier",
        value=CITY_TIER_DISPLAY.get(store_city_tier, store_city_tier),
        disabled=True,
        label_visibility="collapsed",
    )

    field_header("Store Age", "Store_Age_Years", "Unit: years. Locked from Store ID.")
    st.text_input(
        "Store Age",
        value=f"{store_age_years:.0f} years",
        disabled=True,
        label_visibility="collapsed",
    )
else:
    field_header("Store Type", "Store_Type", "Store format category.")
    store_type = st.selectbox(
        "Store Type",
        STORE_TYPE_OPTIONS,
        index=STORE_TYPE_OPTIONS.index(DEFAULTS["Store_Type"]),
        label_visibility="collapsed",
    )

    field_header("Store Size", "Store_Size", "Categorical size band.")
    store_size = st.selectbox(
        "Store Size",
        STORE_SIZE_OPTIONS,
        index=STORE_SIZE_OPTIONS.index(DEFAULTS["Store_Size"]),
        format_func=lambda v: STORE_SIZE_DISPLAY.get(v, v),
        label_visibility="collapsed",
    )

    field_header("City Tier", "Store_Location_City_Type", "Categorical city tier.")
    store_city_tier = st.selectbox(
        "City Tier",
        CITY_TIER_OPTIONS,
        index=CITY_TIER_OPTIONS.index(DEFAULTS["Store_Location_City_Type"]),
        format_func=lambda v: CITY_TIER_DISPLAY.get(v, v),
        label_visibility="collapsed",
    )

    field_header("Store Age", "Store_Age_Years", "Unit: years.")
    store_age_years = st.number_input(
        "Store Age",
        min_value=0.0,
        value=DEFAULTS["Store_Age_Years"],
        step=1.0,
        format="%.0f",
        label_visibility="collapsed",
    )

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
st.subheader("Product Information")

field_header("Product Category ID", "Product_Id_char", "Codes: FD = Food, NC = Non-Consumable, DR = Drink.")
product_id_char = st.selectbox(
    "Product Category ID",
    PRODUCT_ID_CHAR_OPTIONS,
    index=PRODUCT_ID_CHAR_OPTIONS.index(DEFAULTS["Product_Id_char"]),
    format_func=lambda v: PRODUCT_CATEGORY_DISPLAY.get(v, v),
    label_visibility="collapsed",
)

valid_product_types = CATEGORY_TO_PRODUCT_TYPES[product_id_char]
unavailable_product_types = [pt for pt in PRODUCT_TYPES if pt not in valid_product_types]

if "product_type_choice" not in st.session_state:
    st.session_state["product_type_choice"] = DEFAULTS["Product_Type"]

if st.session_state["product_type_choice"] not in valid_product_types:
    st.session_state["product_type_choice"] = valid_product_types[0]

field_header("Product Type", "Product_Type", "Filtered by Product Category ID.")
product_type = st.selectbox(
    "Product Type",
    valid_product_types,
    index=valid_product_types.index(st.session_state["product_type_choice"]),
    key="product_type_choice",
    label_visibility="collapsed",
)

render_unavailable("Unavailable for this product category", unavailable_product_types)

valid_sugar_content = CATEGORY_TO_SUGAR_CONTENT[product_id_char]
unavailable_sugar_content = [sc for sc in ALL_SUGAR_OPTIONS if sc not in valid_sugar_content]

if "product_sugar_content_choice" not in st.session_state:
    st.session_state["product_sugar_content_choice"] = DEFAULTS["Product_Sugar_Content"]

if st.session_state["product_sugar_content_choice"] not in valid_sugar_content:
    st.session_state["product_sugar_content_choice"] = valid_sugar_content[0]

field_header("Sugar Content", "Product_Sugar_Content", "Filtered by Product Category ID.")
product_sugar_content = st.selectbox(
    "Sugar Content",
    valid_sugar_content,
    index=valid_sugar_content.index(st.session_state["product_sugar_content_choice"]),
    key="product_sugar_content_choice",
    label_visibility="collapsed",
)

render_unavailable("Unavailable for this product category", unavailable_sugar_content)

field_header("Product Weight", "Product_Weight", "Unit not specified in source data.")
product_weight = st.number_input(
    "Product Weight",
    min_value=MIN_RULES["Product_Weight"],
    value=DEFAULTS["Product_Weight"],
    step=0.1,
    format="%.2f",
    label_visibility="collapsed",
)

field_header("Product Allocated Area", "Product_Allocated_Area", "Share of display area (0–1 ratio).")
product_allocated_area = st.number_input(
    "Product Allocated Area",
    min_value=MIN_RULES["Product_Allocated_Area"],
    value=DEFAULTS["Product_Allocated_Area"],
    step=0.001,
    format="%.3f",
    label_visibility="collapsed",
)

field_header("Product MRP", "Product_MRP", "Source currency not specified in source data.")
product_mrp = st.number_input(
    "Product MRP",
    min_value=MIN_RULES["Product_MRP"],
    value=DEFAULTS["Product_MRP"],
    step=1.0,
    format="%.2f",
    label_visibility="collapsed",
)

product_type_category = derive_product_type_category(product_type)

row = {
    "Product_Weight": product_weight,
    "Product_Sugar_Content": product_sugar_content,
    "Product_Allocated_Area": product_allocated_area,
    "Product_MRP": product_mrp,
    "Store_Id": store_id,
    "Store_Size": store_size,
    "Store_Location_City_Type": store_city_tier,
    "Store_Type": store_type,
    "Product_Id_char": product_id_char,
    "Store_Age_Years": store_age_years,
    "Product_Type": product_type,
    "Product_Type_Category": product_type_category,
}
row = _coerce_row_types(row)

if st.button("Predict Revenue", type="primary", key="predict_single"):
    row_errors = validate_business_row(row)

    if row_errors:
        st.error("Please correct the business inputs before prediction.")
        for err in row_errors:
            st.write(f"- {err}")
    else:
        try:
            result = call_backend(model_choice, [row], timeout_s=30)
            st.success(f"Model used: {result.get('model_used', model_choice)}")

            preds = result.get("predictions", [])
            if preds:
                st.metric("Predicted Revenue", f"{float(preds[0]):,.2f}")

            store_totals = result.get("store_totals", {})
            if store_totals:
                st.write("Store Totals:", store_totals)

            if show_raw:
                st.json(result)

        except Exception as exc:
            st.error(f"Error: {exc}")
