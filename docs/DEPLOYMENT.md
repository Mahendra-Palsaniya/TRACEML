# Deployment

## Local

1. Restore and verify the original trained artifacts. `artifacts/rf.pkl` is corrupted and the full MoE classifier will not work until retrained or recovered.
2. Install requirements in a Python virtual environment.
3. Start the API with `uvicorn main:app --host 0.0.0.0 --port 8000`.
4. Serve `frontend/` using `python -m http.server 5173 --directory frontend`.
5. Open the dashboard on port 5173.

## Docker

Run `docker compose up --build`. The API uses port 8000 and the static dashboard port 5173. This deployment has not been independently smoke-tested.

## Security

Do not expose this API publicly without authentication, strict CORS, upload limits, HTTPS and rate limiting. The API is a research prototype, not a validated live network IDS.
