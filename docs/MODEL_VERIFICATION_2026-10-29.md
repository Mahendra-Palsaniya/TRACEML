# Local model verification report — 2026-10-29

Source: user-provided original `TRACE-ML-main.zip`, extracted in an isolated working directory. The checks below **do not** verify the migrated GitHub artifacts, the committed backend branch, or Docker.

## Commands executed

```bash
python - <<'PY'
from pathlib import Path
import json, joblib, torch
from model import Model
p=Path('artifacts')
m=Model(77,256,16)
m.load_state_dict(torch.load(p/'model.pth',map_location='cpu',weights_only=True))
print('VAE checkpoint load PASS')
for name in ['lgb.pkl','rf.pkl']:
    try: print(name, type(joblib.load(p/name)).__name__)
    except Exception as e: print(name, 'LOAD FAIL', type(e).__name__)
print('features', len(json.loads((p/'features_name.json').read_text())['feature_names']))
PY
```

## Actual results

- `model.pth` (740,177 bytes): VAE checkpoint loaded into `Model(77,256,16)` successfully.
- `lgb.pkl` (1,057,132 bytes): loaded successfully as `lightgbm.sklearn.LGBMClassifier`; `n_features_in_ == 46`.
- `rf.pkl` (2 bytes): deserialization failed with `KeyError: 13`. **Do not use for inference.**
- `features_name.json` (1,732 bytes): 77 feature names.
- `threshold.json`: `threshold = 76.25257873535156`.
- A scikit-learn version mismatch warning was observed while loading the original LightGBM pickle (serialized LabelEncoder version 1.9.0; runtime 1.8.0).
- Original VAE `Model.forward` uses stochastic reparameterization. On identical all-zero inputs, two reconstructions differed by maximum absolute value **1.0728552341461182** in one test; latent-mean reconstruction differed by **0.0**. These are implementation checks, not detection accuracy measurements.

## Required next actions

1. Restore the verified original `lgb.pkl` bytes to GitHub; confirm SHA-256 and loading after transfer.
2. Recover `rf.pkl` from trusted prior training output or retrain only with a documented dataset and evaluation split.
3. Confirm that the saved anomaly threshold is calibrated for the selected VAE inference procedure. Do not assume a deterministic decoder is equivalent to training-time stochastic reconstruction.
4. Run end-to-end tests on the exact GitHub branch before merging backend changes.

**Acceptance:** Model-integrity stage remains **BLOCKED** by `rf.pkl` and migrated binary verification.
