"""Restore the trusted original LightGBM artifact from a local TRACE ZIP.

Run in a Git checkout. This script writes only artifacts/lgb.pkl; it does not
commit, push, or load pickle code. Review the resulting Git diff before commit.
"""
import hashlib
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA256 = "389cfbe579d320a45d201c1b5ffefb15552bbb298bf92bd41381c6b782f9f46a"
ARCHIVE_MEMBER = "TRACE-ML-main/artifacts/lgb.pkl"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/restore_lgb_from_zip.py /path/to/TRACE-ML-main.zip")
        return 2
    archive = Path(sys.argv[1])
    target = Path(__file__).resolve().parents[1] / "artifacts" / "lgb.pkl"
    with zipfile.ZipFile(archive) as z:
        data = z.read(ARCHIVE_MEMBER)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        print("ERROR: original artifact SHA-256 mismatch; refusing restoration")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f"Restored {target}: {len(data)} bytes, sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
