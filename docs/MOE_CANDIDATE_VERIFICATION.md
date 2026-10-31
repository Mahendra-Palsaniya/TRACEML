# MoE candidate verification — 2026-10-29

**Status: isolated local experiment only; NOT an accepted real-world IDS evaluation.**

## Inputs and provenance

- Candidate RF: `/mnt/data/rf_recovery/rf_candidate.pkl` (4,109,265 bytes), trained on synthetic demonstration flows with `random_state=42`.
- Remaining experts, scalers, encoder, and gating network: original uploaded TRACE project archive.
- Synthetic demonstration CSV: 10,000 rows, SHA-256 `12792c940b67ea664a3c7867423bbc3c004057b8d0cb379d522e80b3878090aa`.
- Evaluation subset: 2,000 rows from stratified 80/20 split, random seed 42. The candidate RF was fitted on the other 8,000 rows.
- **Critical limitation:** Existing non-RF experts and the saved gating network may have been trained on data overlapping this synthetic CSV. Therefore these results are *not an independent held-out evaluation of the entire MoE*. No real CICIDS2017 evaluation was conducted.

## Actual isolated run

- Eight experts and original gating network loaded successfully.
- Output probabilities shape `(2000, 3)`; maximum row-sum deviation from 1: `2.384185791015625e-07`.
- Gated MoE synthetic-demo accuracy: **0.9815**.
- Uniform-average synthetic-demo accuracy: **0.9800**.
- Candidate RF synthetic-demo accuracy: **0.9775**.
- Per-expert synthetic-demo accuracy in original order [XGBoost, LightGBM, RF candidate, Gradient Boosting, Logistic Regression, SVM, small MLP, deep MLP]: `[0.9815, 0.9815, 0.9775, 0.98, 0.943, 0.96, 0.955, 0.951]`.
- Gated MoE confusion matrix, class order `[Benign, FTP-BruteForce, SSH-Bruteforce]`:

```text
[[1296, 1, 4],
 [13, 347, 4],
 [14, 1, 320]]
```

- Mean gate weights across 2,000 flows: `[0.230399, 0.231743, 0.100219, 0.099618, 0.084135, 0.082324, 0.073617, 0.097944]`.

## Gating retraining decision

The existing gate is **technically compatible** with the replacement RF, and on this synthetic subset its output remains normalized. Its weight on the RF candidate averages about 10%. **This does not prove that retraining is unnecessary**: the gate was trained with a different RF, and the entire original ensemble lacks a provenance-controlled external evaluation set. Defer any gate retraining until a documented, disjoint validation dataset is available. Do not silently replace the original gate.

## Artifact restoration blocker

The original `lgb.pkl` (1,057,132 bytes) loads locally, but the GitHub copy at `artifacts/lgb.pkl` returns zero encoded content. Container networking cannot resolve GitHub, and the GitHub connector does not accept local file paths. The binary was **not** restored by this work. The candidate RF also remains local and is **not** committed to GitHub.

## Release blockers

1. Restore LightGBM binary to GitHub, check SHA-256 and deserialization.
2. Recover original RF if possible, or explicitly approve a retrained replacement after independent evaluation.
3. Obtain a provenance-controlled held-out dataset not used to train any expert or the gate.
4. Test complete VAE-to-MoE pipeline, including saved threshold and feature mapping, on committed code.
5. Run CI and Docker tests; only then merge inference changes.

## VAE-to-MoE integration smoke test (additional local run)

Using the original VAE checkpoint, original feature metadata, original gate and seven experts, and the isolated candidate RF, `ThreatPipeline.predict_batch` processed the first 64 rows of the synthetic demo CSV. **64 results** were returned, **20 anomaly flags**, **20 classified flagged flows**, and all anomaly scores were finite. Output keys: `is_anomaly`, `score`, `threshold`, `attack_type`, `attack_confidence`, `top_contributors`. Attack labels across 64 results: `BENIGN=44`, `SSH-Bruteforce=11`, `FTP-BruteForce=8`, `Benign=1`. This last `Benign` label on a VAE-flagged flow is a real observed VAE/MoE disagreement, not a test failure; it needs explicit UI handling. **This is not a GitHub-branch test or independent accuracy evaluation.**
