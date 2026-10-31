"""Restore the original LightGBM artifact from a trusted local .pkl or ZIP.

Verifies SHA-256 before writing. Does not deserialize pickle or push to GitHub.
Only use a file whose provenance you trust.
"""
import hashlib
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA256 = "389cfbe579d320a45d201c1b5ffefb15552bbb298bf92bd41381c6b782f9f46a"
ARCHIVE_MEMBER = "TRACE-ML-main/artifacts/lgb.pkl"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/restore_lgb_from_zip.py /path/to/lgb.pkl|TRACE-ML-main.zip")
        return 2
    source = Path(sys.argv[1])
    if not source.is_file():
        print(f"ERROR: source not found: {source}")
        return 1
    try:
        if source.suffix.lower() == ".zip":
            with zipfile.ZipFile(source) as archive:
                data = archive.read(ARCHIVE_MEMBER)
        else:
            data = source.read_bytes()
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        print(f"ERROR: could not read source: {exc}")
        return 1
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        print(f"ERROR: SHA-256 mismatch ({digest}); refusing restoration")
        return 1
    target = Path(__file__).resolve().parents[1] / "artifacts" / "lgb.pkl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f"Restored {target}: {len(data)} bytes, sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
