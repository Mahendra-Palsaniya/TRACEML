"""Non-executing artifact integrity check. Never deserializes untrusted pickle files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
REQUIRED = {
    "model.pth": 1024,
    "threshold.json": 2,
    "features_name.json": 10,
    "scaler_train_benign.pkl": 128,
    "scaler.pkl": 128,
    "label_encoder.pkl": 128,
    "xgb.json": 1024,
    "lgb.pkl": 128,
    "rf.pkl": 128,
    "gb.pkl": 128,
    "lr.pkl": 128,
    "svm.pkl": 128,
    "small_mlp.pt": 1024,
    "deep_mlp.pt": 1024,
    "gating.pt": 1024,
}


def inspect(directory: Path = ARTIFACTS) -> list[dict]:
    report = []
    for name, minimum in REQUIRED.items():
        path = directory / name
        size = path.stat().st_size if path.is_file() else None
        status = "missing" if size is None else "suspicious" if size < minimum else "present_unverified"
        report.append({"artifact": name, "bytes": size, "status": status})
    names = directory / "features_name.json"
    if names.is_file():
        try:
            data = json.loads(names.read_text(encoding="utf-8"))
            feature_names = data["feature_names"]
            if len(feature_names) != 77 or len(set(feature_names)) != 77:
                report.append({"artifact": names.name, "status": "invalid_feature_schema"})
        except (OSError, ValueError, KeyError, TypeError):
            report.append({"artifact": names.name, "status": "invalid_json"})
    return report


def main() -> int:
    report = inspect()
    print(json.dumps(report, indent=2))
    return int(any(item["status"] not in {"present_unverified"} for item in report))


if __name__ == "__main__":
    raise SystemExit(main())
