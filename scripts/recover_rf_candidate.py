"""Explicit, isolated Random Forest recovery experiment on labeled CSV data.

Does not overwrite existing pretrained models. Not proof of real-world accuracy.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True, help="Trusted labeled flow CSV")
    parser.add_argument("--output", type=Path, default=Path("recovery_output"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--allow-synthetic-demo", action="store_true",
                        help="Explicitly permit synthetic sample CSV for demo-only model recovery")
    args = parser.parse_args()

    if args.dataset.name == "cicids_sample.csv" and not args.allow_synthetic_demo:
        parser.error("Synthetic demo CSV requires --allow-synthetic-demo; results are not real-world metrics")

    source = (Path(__file__).resolve().parents[1] / "run_pipeline.py").read_text()
    tree = ast.parse(source)
    MOE_FEATURE_COLUMNS = next(ast.literal_eval(node.value) for node in tree.body
                               if isinstance(node, ast.Assign) and
                               any(isinstance(target, ast.Name) and target.id == "MOE_FEATURE_NAMES"
                                   for target in node.targets))
    required = MOE_FEATURE_COLUMNS + ["Label"]
    frame = pd.read_csv(args.dataset)
    missing = [x for x in required if x not in frame.columns]
    if missing:
        parser.error("Missing required columns: " + ", ".join(missing))
    if frame.empty:
        parser.error("Dataset is empty")
    X = frame[MOE_FEATURE_COLUMNS].apply(pd.to_numeric, errors="raise").to_numpy(dtype=np.float64)
    if not np.isfinite(X).all():
        parser.error("Input contains NaN or infinity")
    label_encoder = joblib.load(args.artifact_dir / "label_encoder.pkl")
    scaler = joblib.load(args.artifact_dir / "scaler.pkl")
    y = label_encoder.transform(frame["Label"].astype(str))
    if X.shape[1] != scaler.n_features_in_:
        parser.error("Scaler feature dimension mismatch")

    # This split is for experiment evaluation only. A recovered RF is NOT guaranteed
    # to match the exact training data or gating distribution of the existing ensemble.
    indices = np.arange(len(frame))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, stratify=y, random_state=42
    )
    Xs = scaler.transform(X)
    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(Xs[train_idx], y[train_idx])
    predicted = model.predict(Xs[test_idx])
    args.output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output / "rf_candidate.pkl")
    digest = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    report = {
        "dataset": str(args.dataset),
        "dataset_sha256": digest,
        "demo_only": args.allow_synthetic_demo,
        "train_rows": len(train_idx),
        "test_rows": len(test_idx),
        "classes": label_encoder.classes_.tolist(),
        "classification_report": classification_report(y[test_idx], predicted, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y[test_idx], predicted).tolist(),
        "warning": "Candidate expert not calibrated or validated with saved MoE gating network.",
    }
    (args.output / "rf_candidate_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"saved_to": str(args.output), "test_rows": len(test_idx),
                      "demo_only": args.allow_synthetic_demo}, indent=2))


if __name__ == "__main__":
    main()
