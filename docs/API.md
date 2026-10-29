# TRACE API and Streamlit dashboard

## Local API

Start the backend using the repository's Python requirements and `uvicorn main:app --host 127.0.0.1 --port 8000`.
The backend needs its existing VAE artifacts to start. If the MoE experts are unavailable, `GET /health` reports `degraded`; this is **not** evidence of a fully operational IDS.

## Routes

- `GET /health`: model readiness.
- `POST /predict`, `/attack-type`, `/anomaly-flag`, `/analyze`: JSON `{"row": {<feature-name>: <number>, ...}}`.
- `POST /analyze-batch`: JSON `{"rows": [{...}]}`, between 1 and 5000 records.
- `POST /analyze-csv`: multipart upload with form field `file`; .csv, at most 5 MiB and 1000 rows. Missing columns, invalid numbers, or non-finite values return 422.
- `POST /summarize`: JSON `{"llm_payload": {...}, "model_output": {...}}`. Non-object values return 422.
- `GET /random-analyze`: demo-only randomly sampled CSV row; **not live traffic**.

Invalid feature data returns HTTP 422. API readiness depends on available model artifacts.

## Dashboard

Run locally:

```sh
python -m pip install -r dashboard/requirements.txt
TRACE_API_URL=http://localhost:8000 streamlit run dashboard/app.py
```

Docker Compose with the existing API and new Streamlit service:

```sh
docker compose -f docker-compose.yml -f docker-compose.streamlit.yml up --build
```

Open the Streamlit dashboard on port 8501. Existing static dashboard remains on port 5173.
Streamlit shows API health, CSV preview, anomaly count, filtering, attack-class chart and results download.
It never fabricates predictions or labels demo CSV data as live network traffic.

## Verification limits

The new API tests mock the compute/LLM modules; they do not prove model inference. The original LightGBM and Random Forest artifacts remain invalid in GitHub until restored and verified. Do not expose the unauthenticated API to the public Internet or treat this Docker configuration as production deployment.

## Real-time deployment prerequisites

Authorized capture source; verified flow extraction for the exact 77 VAE and 46 MoE features; end-to-end PCAP tests; persistence and access controls; successful Docker smoke test; validated model artifacts. Without these, a running dashboard is not a real-time IDS.
