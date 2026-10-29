# TRACE — AI-Powered Network Intrusion Detection (Research Prototype)

This repository contains the migrated TRACE VAE anomaly detector, an eight-expert Mixture of Experts (MoE) attack classifier, a FastAPI API, a CSV analysis endpoint, and a static browser dashboard.

**Status:** The original `artifacts/rf.pkl` is corrupt (2 bytes). The application can operate in degraded VAE-only mode, but MoE attack classification is **not working** until a trusted model is recovered or retrained. This is not yet a production-ready live IDS.

## Run locally

Python 3.10+ recommended. Create a virtual environment and run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
python -m http.server 5173 --directory frontend
```

Open the dashboard at http://localhost:5173 and API documentation at http://localhost:8000/docs.

The CSV endpoint is `POST /analyze-csv` (multipart form field `file`, max 5 MiB, max 1,000 records). It requires the 77 CICIDS-style features defined in `artifacts/features_name.json`. The API reports `degraded` status on `GET /health` if the MoE model cannot load.

## Docker

```bash
docker compose up --build
```

This Docker configuration has not yet been smoke-tested. Do not expose the API publicly without authentication, HTTPS, strict origin restrictions and request rate limiting.

## Remaining work

1. Restore/retrain the corrupt Random Forest expert and verify the complete MoE ensemble.
2. Validate model metrics against a held-out labeled dataset.
3. Implement authorized flow collection with exact feature equivalence.
4. Add authenticated ingestion, persistent alert storage, and a production-ready deployment.

See `docs/IMPLEMENTATION_STATUS.md` and `docs/DEPLOYMENT.md`.
