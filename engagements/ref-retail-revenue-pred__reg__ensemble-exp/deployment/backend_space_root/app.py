from fastapi import FastAPI, HTTPException
from typing import Any, Dict
import json
import joblib
import pandas as pd

app = FastAPI()

with open("model_metadata.json", "r") as fh:
    metadata = json.load(fh)

PRIMARY_LABEL = metadata["primary_label"]
SECONDARY_LABEL = metadata["secondary_label"]

MODELS = {
    PRIMARY_LABEL: joblib.load("primary_model.joblib"),
    SECONDARY_LABEL: joblib.load("secondary_model.joblib"),
}

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "message": "Retail Prediction Backend is running. Use /v1/predict for predictions.",
        "primary_model": PRIMARY_LABEL,
        "secondary_model": SECONDARY_LABEL,
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "primary_model": PRIMARY_LABEL,
        "secondary_model": SECONDARY_LABEL,
    }

@app.post("/v1/predict")
async def predict(request_body: Dict[str, Any]):
    model_name = request_body.get("model", PRIMARY_LABEL)
    rows = request_body.get("rows", [])

    if not rows:
        raise HTTPException(status_code=400, detail="No data rows provided for prediction.")

    model = MODELS.get(model_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")
    try:
        df = pd.DataFrame(rows)
        predictions = model.predict(df).tolist()

        overall_total = sum(predictions)

        store_totals = {}
        if "Store_Id" in df.columns:
            temp = df.copy()
            temp["predictions"] = predictions
            store_totals = temp.groupby("Store_Id")["predictions"].sum().to_dict()

        return {
            "model_used": model_name,
            "predictions": predictions,
            "overall_total": overall_total,
            "store_totals": store_totals,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
