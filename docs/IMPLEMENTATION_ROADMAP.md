# TRACE Implementation Roadmap

Last reviewed: 2026-10-29. Branch: `work/trace-roadmap-and-integrity`.

## Ground truth

Existing code: FastAPI (`main.py`), VAE and MoE (`compute.py`), VAE architecture (`model.py`), training (`run_pipeline.py`), Gemini fallback (`llm.py`), static frontend (`frontend/`), Docker Compose and 2 regression tests. Source-level audit: `docs/REPOSITORY_AUDIT.md`.

**Current state is NOT production-ready.** Model binaries are not all verified, a Random Forest artifact is only ~2 bytes, and LightGBM may have been migrated as an empty Git blob. The VAE latent-mean inference change also needs threshold-calibration verification. Existing tests have not been executed in a clean CI environment.

## Stage gates

| Order | Milestone | Current state | Gate to advance |
|---|---|---|---|
| 1 | Artifact integrity and model loading | IN PROGRESS | All artifacts inspected; models load or are explicitly marked unavailable |
| 2 | Backend stabilization | IN PROGRESS | Clean startup, safe errors, deterministic documented inference, passing tests |
| 3 | VAE/MoE inference and evaluation | BLOCKED by artifacts | Exact features, scalers, probabilities and held-out metrics verified |
| 4 | API contract and integration tests | NOT STARTED | Every supported endpoint tested |
| 5 | Streamlit dashboard | NOT STARTED | Streamlit talks to FastAPI; upload and error states tested |
| 6 | CI and regression coverage | PARTIAL | GitHub Actions tests pass |
| 7 | Persistent alerts and security | NOT STARTED | Auth, retention, storage, logs tested |
| 8 | Authorized offline PCAP ingestion | NOT STARTED | Feature-equivalent flow extraction proven |
| 9 | Local Docker deployment | UNVERIFIED | Build, startup and health tests pass |
| 10 | Hosted deployment | NOT STARTED | HTTPS endpoint, health, sample inference, dashboard and rollback verified |
| 11 | Final documentation/demo | NOT STARTED | Reproducible college demonstration accepted |

## Deployment target decision

Use a container-capable host only after local Docker smoke tests. A cloud service cannot be marked deployed without selecting a provider, configuring secrets and validating running URLs. The static dashboard is an existing optional UI; Streamlit remains to be implemented. Live capture is a separate authorized-only milestone.

## Immediate commands

```bash
python scripts/check_artifacts.py
python -m pytest -q
uvicorn main:app --host 127.0.0.1 --port 8000
# Once backend is healthy:
docker compose up --build
```

## Known risks

- `artifacts/rf.pkl`: damaged binary; do not load blindly or replace with a fabricated classifier.
- `artifacts/lgb.pkl`: verify exact bytes; may be empty in Git.
- PyTorch checkpoints and joblib pickles: deserialize only if trusted; prefer `weights_only=True` for tensor state dictionaries.
- `run_pipeline.py`: regenerates synthetic data and cannot establish real-world IDS accuracy.
- Existing VAE threshold may not be calibrated for deterministic latent-mean decoding.
- Current API lacks authentication, storage, and comprehensive input limits.

## Required report per milestone

Files inspected, files changed, findings, fixes, exact commands, actual outputs, remaining blockers, acceptance verdict, commit SHA.
