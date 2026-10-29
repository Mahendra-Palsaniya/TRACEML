# TRACE Repository Audit — Phase 1

**Audit date:** 2026-10-29  
**Scope:** `trace-implementation` branch at audit branch creation, including the 32 tracked paths visible in the GitHub comparison against `main`.  
**Audit branch:** `audit/phase-1-2026-10-29`  
**Status:** **Completed as a source-level inventory; runtime/model verification NOT passed.**  
**Evidence:** GitHub file reads, source-line inspection, artifact presence/encoded-length checks. No clean-environment install, model-deserialization, API request, Docker build, or deployment was performed during this phase.

## Inventory and architecture

| Path(s) | Purpose | Audit classification |
|---|---|---|
| `main.py` | FastAPI routes, random sample selection, CSV upload | Partially implemented |
| `compute.py` | VAE, eight-expert MoE, gating, inference and feature checks | Partially implemented; full classifier broken |
| `model.py` | VAE architecture and training loss | Implemented but unverified |
| `run_pipeline.py` | Synthetic-data generation, training, evaluation, artifact export | Implemented but unverified |
| `llm.py` | Gemini summary and rule-based fallback | Implemented but unverified |
| `requirements.txt` | Python dependencies | Implemented but unverified |
| `Dockerfile`, `docker-compose.yml` | API container and static dashboard | Implemented but unverified |
| `.env.example`, `.gitignore` | Configuration template and exclusions | Partially implemented |
| `frontend/index.html`, `frontend/style.css`, `frontend/app.js` | Existing static JavaScript dashboard | Implemented but unverified; NOT Streamlit |
| `README.md`, `docs/DEPLOYMENT.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/WORK_STATUS.md` | Setup and status documents | Partially implemented |
| `artifacts/` | VAE and MoE model weights, encoders and preprocessing | Partially present; integrity defects |
| `tests/` | Automated regression suite | Missing |
| Streamlit dashboard | Requested frontend | Missing |
| Live flow collector and PCAP conversion | Authorized traffic ingestion | Missing |
| Persistent alerts/database | Investigation history | Missing |
| Authentication and rate limiting | Production security | Missing |
| GitHub Actions workflow | CI checks | Missing |

No complete working-tree or untracked-file inspection was possible through GitHub's remote API. The inventory is limited to repository paths visible in the branch comparison, not a local checkout.

## Artifact inventory

These files are present as Git objects on the audit branch; **presence is not proof of valid serialization**:

| Artifact | GitHub object SHA | Finding |
|---|---|---|
| `artifacts/model.pth` | `1c9aaf32` | Present, not loaded in this audit |
| `artifacts/threshold.json` | `63f4fb3e` | Present, schema not runtime-tested |
| `artifacts/features_name.json` | `a82d03f0` | Present; `compute.py:262-263` expects 77 names |
| `artifacts/scaler_train_benign.pkl` | `c5455dfc` | Present, not deserialized |
| `artifacts/scaler.pkl` | `ecf241d5` | Present, not deserialized |
| `artifacts/label_encoder.pkl` | `12a78deb` | Present, not deserialized |
| `artifacts/xgb.json` | `7f4f6e84` | Present, not loaded |
| `artifacts/lgb.pkl` | `e69de29b` | **Broken/suspicious:** GitHub base64 content returned empty |
| `artifacts/rf.pkl` | `d3f5a12f` | **Broken:** GitHub base64 content only 5 characters; previously identified as a 2-byte artifact |
| `artifacts/gb.pkl` | `2543b2ac` | Present, not loaded |
| `artifacts/lr.pkl` | `1644f2ad` | Present, not loaded |
| `artifacts/svm.pkl` | `685e5a27` | Present, not loaded |
| `artifacts/small_mlp.pt` | `cf01e534` | Present, not loaded |
| `artifacts/deep_mlp.pt` | `263c34bf` | Present, not loaded |
| `artifacts/gating.pt` | `43d032cf` | Present, not loaded |

**Critical:** `compute.py:75-76` loads `lgb.pkl` and `rf.pkl` unconditionally. `compute.py:266-272` catches MoE initialization errors and falls back to VAE-only mode. That fallback is explicitly labelled unavailable for anomalous traffic at `compute.py:238-240`; it must not be confused with a verified eight-expert classifier.

## API inventory

Source: `main.py`:

| Method | Path | Function / lines | Classification |
|---|---|---|---|
| POST | `/analyze-batch` | `analyze_batch`, 100-123 | Implemented, unverified |
| POST | `/predict` | `predict_one`, 126-153 | Implemented, unverified |
| POST | `/attack-type` | `predict_attack_type`, 156-170 | Partially implemented; MoE unavailable |
| POST | `/anomaly-flag` | `get_anomaly_flag`, 173-192 | Implemented, unverified |
| POST | `/analyze` | `analyze`, 195-229 | Implemented, unverified |
| POST | `/summarize` | `summarize`, 232-237 | Implemented, unverified |
| GET | `/health` | `health`, 239-241 | Partially implemented |
| GET | `/random-analyze` | `random_analyze`, 243-261 | Partially implemented |
| POST | `/analyze-csv` | `analyze_csv`, 264-295 | Implemented, unverified |

Single-input requests use `RowIn(row: Dict[str, Any])` (`main.py:63-64`). Batch requests use `BatchIn(rows: List[Dict[str, Any]])` (`main.py:83-96`). `/analyze-csv` accepts multipart field `file`, with 5 MiB and 1,000-row limits. Responses generally derive from `compute.predict`: `results` plus `input_issues`. There are no endpoint-level integration tests yet.

## Prioritized findings

### P0 — blockers

1. **Model integrity:** `artifacts/rf.pkl` is unusably small and `artifacts/lgb.pkl` returned empty content. `compute.py:68-95` loads both during MoE initialization. Verify Git blob bytes locally, recover from a trusted source, or retrain with a documented dataset; never substitute fake models.
2. **Training data provenance:** `run_pipeline.py:180-241` generates synthetic CICIDS-like samples and `load_dataset()` always regenerates them. Reported evaluation metrics from this pipeline cannot be presented as measured CICIDS2017 or real-world IDS accuracy.
3. **Missing tests:** No `tests/` files are in the audited branch. Actual VAE and API acceptance criteria are unverified.

### P1 — backend and API

4. `main.py:13-18` repeats `BASE_DIR` in `DATA_DIRS`; `main.py:30-37` automatically generates synthetic CSV when no file exists. Demo source must be explicit and labeled.
5. `main.py:45` replaces infinity/NaN with zeros in random-row selection, masking data-quality problems.
6. `compute.py:302-316` raises raw `ValueError` on invalid inputs; `main.py:121-229` does not map this to a controlled HTTP 422, risking server errors.
7. `compute.py:284-294` only validates MoE columns when the MoE has loaded; feature validation changes based on model readiness.
8. `compute.py:156-198` VAE inference needs deterministic evaluation and numerical checks; `model.py:29-36` uses stochastic reparameterization even in evaluation mode.
9. `main.py:52-60` permits broad methods/headers; no API authentication, rate limiting or request-size middleware.
10. `compute.py:269-270` exposes exception text and filesystem details through model status; sanitize before public use.
11. `llm.py` uses optional Gemini credentials and a fallback, but the external API and output schema have not been tested.

### P2 — deployment and frontend

12. `requirements.txt` contains numerous unpinned, apparently unrelated packages (Hugging Face, ChromaDB, notebook tooling), increasing dependency and container-build risk.
13. `Dockerfile` and `docker-compose.yml` are present but not built or smoke-tested.
14. `frontend/` is a static HTML/JS dashboard, not the Streamlit dashboard requested by the new implementation specification.
15. No PCAP-to-flow converter, live sensor, database, structured alert history or cloud deployment was found.

## Model and data contracts

- `compute.py:97-115` defines **46 MoE feature names** in a fixed order.
- `compute.py:258-263` reads **77 VAE feature names** from `artifacts/features_name.json`.
- `compute.py:199-256` implements the VAE-to-MoE handoff and returns anomaly score, threshold, attack label, confidence and top contributors.
- `run_pipeline.py:239-241` regenerates synthetic data rather than loading a verified real dataset.
- `main.py:264-295` requires CICIDS-style CSV columns and converts numeric values; it does not establish provenance or ground truth.

## Acceptance verdict

**Phase 1 source-level audit deliverable: prepared.**  
**Phase 1 runtime verification: NOT passed.** No source architecture was modified during this audit. Phase 2 must begin with artifact-byte integrity checks, dependency setup, and real model-load tests before extending functionality.

## Implementation priorities

1. Reproduce a clean local environment and verify actual artifact bytes and model loading.
2. Repair only confirmed model-load and request-validation failures; retain VAE and MoE semantics.
3. Add tests using verified samples; distinguish synthetic demonstration data from real CICIDS traffic.
4. Build Streamlit against stable API endpoints.
5. Implement security, persistence, offline flow validation and deployment only after core inference tests pass.
