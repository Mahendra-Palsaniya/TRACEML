import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_check", ROOT / "scripts" / "check_artifacts.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_empty_artifact_directory_is_rejected(tmp_path):
    report = MODULE.inspect(tmp_path)
    assert report
    assert all(item["status"] == "missing" for item in report)


def test_tiny_pickle_is_suspicious(tmp_path):
    (tmp_path / "rf.pkl").write_bytes(b"\x80\x04")
    report = MODULE.inspect(tmp_path)
    rf = next(item for item in report if item["artifact"] == "rf.pkl")
    assert rf["status"] == "suspicious"


def test_feature_metadata_requires_77_unique_names(tmp_path):
    (tmp_path / "features_name.json").write_text('{"feature_names":["a","a"]}')
    report = MODULE.inspect(tmp_path)
    assert any(item["status"] == "invalid_feature_schema" for item in report)
