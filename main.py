import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import compute
import json
from llm import summarize_alert
from pydantic import BaseModel
from typing import Any, Dict, List
import pandas as pd
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIRS = [
    os.path.join(BASE_DIR, "data"),
    BASE_DIR,
    os.path.join(BASE_DIR, "solarmainframe", "ids-intrusion-csv", "versions", "1"),
    BASE_DIR
]

def get_random_row_from_csv():
    import glob

    csv_files = []
    for d in DATA_DIRS:
        if os.path.exists(d):
            found = glob.glob(os.path.join(d, "*.csv"))
            if found:
                csv_files.extend(found)

    if not csv_files:
        # Fallback: create synthetic sample CSV in data/
        data_dir = os.path.join(BASE_DIR, "data")
        os.makedirs(data_dir, exist_ok=True)
        csv_files = [os.path.join(data_dir, "cicids_sample.csv")]
        if not os.path.exists(csv_files[0]):
            from run_pipeline import generate_synthetic_dataset
            generate_synthetic_dataset()

    chosen_file = random.choice(csv_files)
    df = pd.read_csv(chosen_file)

    if "Label" in df.columns:
        df = df.drop(columns=["Label"])

    df = df.replace([float("inf"), float("-inf")], 0).fillna(0)
    random_row = df.sample(1).to_dict(orient="records")[0]
    return random_row
app = FastAPI()


@app.exception_handler(ValueError)
async def invalid_input_handler(request, exc: ValueError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=422, content={"detail": str(exc)})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RowIn(BaseModel):
    row: Dict[str, Any]

    """
       Request schema for endpoints that analyze a *single* event/record.

       Frontend usage:
       - Send a JSON body with a `row` object containing the feature fields expected by the model.
       - Example:
         {
           "row": {
             "src_ip": "1.2.3.4",
             "dst_port": 443,
             "bytes_out": 1234,
             ...
           }
         }
       """


class BatchIn(BaseModel):
    """
    Request schema for endpoints that analyze a *batch* of events/records.

    Frontend usage:
    - Send a JSON body with a `rows` array; each element is a feature dict.
    - Example:
      {
        "rows": [
          {"src_ip": "1.2.3.4", "dst_port": 443, ...},
          {"src_ip": "5.6.7.8", "dst_port": 22, ...}
        ]
      }
    """
    rows: List[Dict[str, Any]]


@app.post("/analyze-batch",
          summary="Analyze a batch of rows (full model output)",
          description=(
                  "Runs the model on multiple input rows in one request.\n\n"
                  "- Calls `compute.predict(rows)`.\n"
                  "- Returns the raw output from the model for the entire batch.\n\n"
                  "Usage:\n"
                  "- Use this when you have a table/list view and want to score many rows at once.\n"
                  "- Good for bulk actions, precomputing UI badges, etc.\n\n"
                  "Response shape:\n"
                  "- Returns "
                  """
                {"is_anomaly": bool(flags[i]),
                "score": float(scores[i]),
                "threshold": float(vae_out["threshold"]),
                "attack_type": str(attack_label[i]),
                "attack_confidence": float(attack_conf[i]),
                "top_contributors": contrib,
                }
                optionally `input_issues`)."""),
          )
def analyze_batch(req: BatchIn):
    out = compute.predict(req.rows)
    return out


@app.post("/predict",
          summary="Predict anomaly + attack info for a single row",
          description=(
                  "Runs the model for a single row and returns a *flattened* subset of fields.\n\n"
                  "What it fetches/returns:\n"
                  "- `is_anomaly`: boolean anomaly flag\n"
                  "- `score`: anomaly score\n"
                  "- `threshold`: threshold used to decide anomaly\n"
                  "- `attack_type`: predicted attack label/category\n"
                  "- `attack_confidence`: confidence score for `attack_type`\n"
                  "- `top_contributors`: main features driving the decision (for explanations UI)\n"
                  "- `input_issues`: validation/quality issues detected in input (if any)\n\n"
                  "Usage:\n"
                  "- Use this for the primary 'Predict' action button. Basically if we want everything.\n"
          ),
          )
def predict_one(req: RowIn):
    out = compute.predict([req.row])
    result0 = out["results"][0]
    return {
        "is_anomaly": result0["is_anomaly"],
        "score": result0["score"],
        "threshold": result0["threshold"],
        "attack_type": result0["attack_type"],
        "attack_confidence": result0["attack_confidence"],
        "top_contributors": result0["top_contributors"],
        "input_issues": out.get("input_issues", {})
    }


@app.post("/attack-type",
          summary="Predict attack type for a single row",
          description=(
                  "Runs the model for a single row and returns only attack classification fields.\n\n"
                  "What it fetches/returns:\n"
                  "- `attack_type`\n"
                  "- `attack_confidence`\n\n"
                  "Usage:\n"
                  "- Use this only when attack type needs to be displayed i.e. for anomaly detected thing.\n"
          ),
          )
def predict_attack_type(req: RowIn):
    out = compute.predict([req.row])
    r = out["results"][0]
    return {"attack_type": r["attack_type"], "attack_confidence": r["attack_confidence"]}


@app.post("/anomaly-flag",
          summary="Predict only anomaly flag + score for a single row",
          description=(
                  "Runs the model for a single row and returns only anomaly-related fields.\n\n"
                  "What it fetches/returns:\n"
                  "- `is_anomaly`\n"
                  "- `score`\n"
                  "- `threshold`\n\n"
                  "Frontend usage:\n"
                  "- Use for checking if anomaly is there\n"
          ),
          )
def get_anomaly_flag(req: RowIn):
    out = compute.predict([req.row])
    r = out["results"][0]
    return {
        "is_anomaly": r["is_anomaly"],
        "score": r["score"],
        "threshold": r["threshold"],
    }


@app.post("/analyze",
          summary="Analyze single row (full model_output + curated llm_payload)",
          description=(
                  "Runs the model for a single row and returns:\n\n"
                  "1) `model_output`:\n"
                  "- The full raw per-row result object returned by the model.\n\n"
                  "2) `llm_payload`:\n"
                  "- A curated subset designed to feed an LLM/explainer component:\n"
                  "  - anomaly fields: `is_anomaly`, `score`, `threshold`\n"
                  "  - attack fields: `attack_type`, `attack_confidence`\n"
                  "  - explanation fields: `top_contributors`\n"
                  "  - `input_issues` if any\n\n"
                  "Frontend usage:\n"
                  "- This is what we will send to the LLM and LLM will return a response with fields like\n"
                  "{keywords: ..., text: ...} and we will use the text for generated output on right of the screen"
          ),
          )
def analyze(req: RowIn):
    out = compute.predict([req.row])
    r = out["results"][0]

    llm_payload = {
        "is_anomaly": r["is_anomaly"],
        "score": r["score"],
        "threshold": r["threshold"],
        "attack_type": r["attack_type"],
        "attack_confidence": r["attack_confidence"],
        "top_contributors": r["top_contributors"],
        "input_issues": out.get("input_issues", {}),
    }

    return {
        "model_output": r,
        "llm_payload": llm_payload
    }


@app.post("/summarize")
def summarize(req: dict):
    if not isinstance(req.get("llm_payload"), dict) or not isinstance(req.get("model_output"), dict):
        raise HTTPException(status_code=400, detail="Need llm_payload and model_output")

    return summarize_alert(req["llm_payload"], req["model_output"])

@app.get("/health")
def health():
    return {"status": "ok" if compute.moe is not None else "degraded", "models": compute.model_status()}

@app.get("/random-analyze")
def random_analyze():
    row = get_random_row_from_csv()
    out = compute.predict([row])
    result0 = out["results"][0]

    llm_payload = {
        "is_anomaly": result0["is_anomaly"],
        "score": result0["score"],
        "threshold": result0["threshold"],
        "attack_type": result0["attack_type"],
        "attack_confidence": result0["attack_confidence"],
        "top_contributors": result0["top_contributors"],
        "input_issues": out.get("input_issues", {}),
    }

    return {
        "model_output": result0,
        "llm_payload": llm_payload
    }

@app.post("/analyze-csv")
async def analyze_csv(file: UploadFile = File(...)):
    """Analyze up to 1,000 CICIDS flow records in a CSV file."""
    import csv
    import io
    import math
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A .csv file is required")
    try:
        raw = await file.read(5 * 1024 * 1024 + 1)
    finally:
        await file.close()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV exceeds 5 MiB limit")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        required = list(dict.fromkeys(compute.vae_feature_names + (compute.PIPELINE.moe.FEATURE_COLUMNS if compute.PIPELINE.moe is not None else [])))
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        missing = [name for name in required if name not in reader.fieldnames]
        if missing:
            raise ValueError("Missing feature columns: " + ", ".join(missing[:12]))
        rows = []
        for record in reader:
            if len(rows) >= 1000:
                raise ValueError("CSV exceeds 1,000-row limit")
            row = {key: float(record[key]) for key in required}
            if not all(math.isfinite(v) for v in row.values()):
                raise ValueError("Non-finite numeric feature")
            rows.append(row)
        if not rows:
            raise ValueError("CSV has no data rows")
    except (UnicodeDecodeError, ValueError, TypeError, KeyError, csv.Error) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return compute.predict(rows)
