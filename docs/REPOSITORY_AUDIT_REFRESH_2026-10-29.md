# TRACE Repository Audit — Phase 1 Refresh (2026-10-29)

**Baseline:** `main`, tree SHA `5276be9dd2446ffde8af4a65cbc425f2e6bad24d`.
**Audit branch:** `audit/phase-1-refresh-2026-10-29`.
**Verdict:** Source-level review performed; **Phase 1 acceptance NOT fully passed** because local working-tree inspection, runtime execution, and complete line-by-line review of the 36 KB training script remain outstanding. No functional source changes made.

## Inventory (tracked Git tree)

Root: `.env.example`, `.gitignore`, `Dockerfile`, `README.md`, `compute.py`, `docker-compose.yml`, `llm.py`, `main.py`, `model.py`, `requirements.txt`, `run_pipeline.py`.
Frontend: `frontend/index.html`, `frontend/style.css`, `frontend/app.js`.
Scripts: `scripts/check_artifacts.py`.
Docs: `docs/DEPLOYMENT.md`, `docs/IMPLEMENTATION_ROADMAP.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/MODEL_VERIFICATION_2026-10-29.md`, `docs/REPOSITORY_AUDIT.md`, `docs/WORK_STATUS.md`.
Artifacts: `deep_mlp.pt`, `features_name.json`, `gating.pt`, `gb.pkl`, `label_encoder.pkl`, `lgb.pkl`, `lr.pkl`, `model.pth`, `rf.pkl`, `scaler.pkl`, `scaler_train_benign.pkl`, `small_mlp.pt`, `svm.pkl`, `threshold.json`, `xgb.json` under `artifacts/`.

No tracked `tests/`, `.github/workflows/`, Streamlit app, persistent alert database, or flow collector in this tree. GitHub API cannot inspect uncommitted local work.

## Evidence-based classifications

| Classification | Finding and evidence |
|---|---|
| Broken | `artifacts/lgb.pkl` is 0 bytes on main; `artifacts/rf.pkl` is 2 bytes. `compute.py` MoEPredictor loads both unconditionally. |
| Partially implemented | `compute.py` catches MoE initialization failure and exposes VAE-only operation; full eight-expert classification unavailable. |
| Implemented but unverified | `artifacts/model.pth` 740177 bytes, `gating.pt` 24137 bytes, `xgb.json` 729649 bytes and other nonempty weights; file presence is not model-load proof. |
| Implemented but unverified | `main.py` FastAPI endpoints; no actual request tests in this audit. |
| Partially implemented | `main.py:get_random_row_from_csv` silently generates synthetic demonstration CSV when absent. |
| Partially implemented | `main.py` request types `RowIn(row: Dict[str, Any])`, `BatchIn(rows: List[Dict[str, Any]])`; feature checks delegated to `compute.predict`. |
| Implemented but unverified | `llm.py:summarize_alert` Gemini integration and no-key fallback; exception text included in failure output. |
| Implemented but unverified | `frontend/` static HTML/CSS/JS CSV dashboard; not Streamlit. |
| Implemented but unverified | `Dockerfile`, `docker-compose.yml`; no build/start verification. |
| Missing | Tracked automated tests, CI workflows, alert persistence, authenticated ingestion, exact PCAP-to-77-feature mapping, live sensor. |
| Partially implemented | `.env.example` only defines Gemini settings; other runtime configuration not centralized. |
| Implemented but unverified | `scripts/check_artifacts.py` checks file sizes and 77-name JSON metadata, not model deserialization. |

## Model and data contract

`artifacts/features_name.json` declares 77 VAE features; `compute.py` contains an ordered 46-feature MoE subset. `artifacts/threshold.json` contains `76.25257873535156`. `model.py:Model.forward` calls stochastic `reparameterize` even in eval mode; threshold equivalence must be established before changing inference. `run_pipeline.py` includes synthetic-data generation, so its results must never be described as held-out CICIDS2017 accuracy without independent provenance.

The existing `docs/MODEL_VERIFICATION_2026-10-29.md` reports that an original local LightGBM file (1057132 bytes) loaded successfully, while the current GitHub file is empty. That local result does not validate GitHub's committed bytes.

## API route inventory (source inspection, not runtime tests)

`POST /analyze-batch`, `POST /predict`, `POST /attack-type`, `POST /anomaly-flag`, `POST /analyze`, `POST /summarize`, `GET /health`, `GET /random-analyze`, `POST /analyze-csv`. `/analyze-csv` accepts multipart `file`, with documented 5 MiB and 1000-row limits. `compute.predict` rejects empty batches and batches above 5000, and checks finite numeric VAE features. Exact endpoint error responses remain unverified.

## Configuration, security and dependency concerns

`main.py` duplicates `BASE_DIR` in `DATA_DIRS` and includes a repository-relative `solarmainframe/ids-intrusion-csv/versions/1` directory. `requirements.txt` is unpinned and contains training, notebook, embeddings, and vector DB packages beyond API needs. `docker-compose.yml` publishes API port 8000; no authentication is evident. `llm.py` includes exception text in fallback output. `compute.py` constructs models at import time and may expose initialization details via status. `frontend/app.js` uses localStorage for API URL and treats HTTP health as online, not proof of MoE readiness.

## Prioritized phase plan

1. **P0:** Recover original LightGBM bytes with checksums and trusted provenance; investigate RF source/retraining data. Do not fabricate a replacement.
2. **P0:** Run exact committed artifact integrity and safe load checks in a clean environment; verify feature order and scaler dimensions.
3. **P1:** Repair only demonstrated backend initialization, validation, and error-handling defects.
4. **P1:** Add true inference regression tests and independently sourced evaluation examples.
5. **P2:** Stabilize API and dashboard, then security, offline authorized flow integration, and Docker.

## Execution record

- GitHub repository metadata and recursive `main` tree inspected.
- Existing audit, roadmap, model verification, deployment and status docs read.
- `main.py`, `compute.py`, `model.py`, `llm.py`, `requirements.txt`, Docker configuration, frontend files, `scripts/check_artifacts.py`, configuration, feature JSON, and threshold JSON inspected; `run_pipeline.py` partially inspected.
- No local shell commands, pytest, Docker, or model-deserialization tests executed. All runtime results **NOT RUN**.
- No functional files changed; this refresh document is the only intended audit deliverable.
- **Acceptance: NOT PASSED** pending complete source review and local checkout/runtime checks.
