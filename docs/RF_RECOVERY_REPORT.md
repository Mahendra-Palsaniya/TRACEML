# Random Forest recovery experiment — 2026-10-29

**Status: experimental, NOT accepted for production or full MoE accuracy.**

## Prior-work inspection

- The repository's original `rf.pkl` is **2 bytes** and fails deserialization (`KeyError: 13`).
- Original `lgb.pkl` is **1,057,132 bytes** and loads locally. The GitHub artifact currently returns zero base64 characters and must be restored.
- `run_pipeline.py` uses a **synthetic** 10,000-row, three-class dataset; `cicids_sample.csv` is synthetic and is not CICIDS2017 ground truth.
- Original MoE input has 46 ordered features; original scaler expects 46 features; label encoder classes are `Benign`, `FTP-BruteForce`, `SSH-Bruteforce`.
- Previously committed Phase 2 changes have not passed clean-branch CI and are **not merged**.

## Isolated RF recovery experiment (local, actual execution)

Dataset: original uploaded `cicids_sample.csv`, 10,000 rows, synthetic. Stratified 80/20 train/test split (random_state=42). Existing original MoE scaler and label encoder reused. Candidate: `RandomForestClassifier(n_estimators=100,max_depth=15,random_state=42,n_jobs=-1)`. Output stored separately, **original rf.pkl not overwritten**.

- Candidate size: **4,109,265 bytes**.
- Held-out synthetic demo rows: **2,000**.
- Synthetic demo accuracy: **0.9775** (NOT real-world detection performance).
- Confusion matrix, class order `[Benign, FTP-BruteForce, SSH-Bruteforce]`:

```text
[[1296, 1, 4],
 [13, 339, 12],
 [14, 1, 320]]
```

### Eight-expert MoE smoke test (local)

The candidate RF was substituted **only in an isolated artifact directory**, alongside original available model files. `MoEPredictor` loaded eight experts and the gating network successfully. On 16 synthetic CSV rows: `probs.shape == (16,3)`, all values finite, and every probability row summed to approximately 1.0. This is a **technical compatibility smoke test only**. It does not validate the trained gate's calibration after RF replacement, and is not a valid end-to-end IDS accuracy estimate.

### Compatibility warnings

Original scikit-learn artifacts report serialization version 1.9.0; local runtime was 1.8.0. LightGBM also warned about absent feature names on NumPy inference. Reproduce with a version-matched environment before release.

## Required before merging runtime code

1. Recover the original RF from a trusted checkpoint if available; otherwise document the new RF as a retrained candidate.
2. Restore original `lgb.pkl` bytes to GitHub and verify SHA-256.
3. Re-train or revalidate the gating network with the replacement expert; the existing gate was trained against different expert outputs.
4. Test VAE anomaly threshold calibration and end-to-end VAE-to-MoE behavior on a provenance-controlled evaluation set.
5. Run the full committed test suite and Docker smoke tests; then open a non-draft PR into `main`.

## Reproduce candidate (explicitly synthetic demo)

```bash
python scripts/recover_rf_candidate.py --dataset cicids_sample.csv --artifact-dir artifacts --allow-synthetic-demo --output recovery_output
```

**Do not commit `recovery_output/` or the generated candidate as a validated model.**
