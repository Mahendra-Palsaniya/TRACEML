# Uploaded recovery inputs — 2026-10-29

This record describes the three files supplied by the project owner and inspected without executing pickle payloads.

| File | Size / rows | SHA-256 | Finding |
| --- | --- | --- | --- |
| `lgb.pkl` | 1,057,132 bytes | `389cfbe579d320a45d201c1b5ffefb15552bbb298bf92bd41381c6b782f9f46a` | Matches expected original LightGBM SHA-256 in restoration script; must be committed as binary and runtime-tested. |
| `rf.pkl` | 2 bytes | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` | Contains only CRLF (`0d0a`); not a recoverable serialized Random Forest. |
| `cicids_sample.csv` | 10,000 rows, 78 columns | `12792c940b67ea664a3c7867423bbc3c004057b8d0cb379d522e80b3878090aa` | Exact hash of previously documented synthetic demo dataset; not verified original CICIDS2017 held-out data. |

CSV labels: Benign=6506; FTP-BruteForce=1817; SSH-Bruteforce=1677.

## Next release steps

1. From a checkout with the uploaded file available, run `python scripts/restore_lgb_from_zip.py /path/to/lgb.pkl`; inspect and commit `artifacts/lgb.pkl` (binary). The connected GitHub text-file interface cannot directly read local binary bytes, and this environment cannot resolve github.com for a git push.
2. Do not commit the 2-byte RF as a valid expert. Recover a genuine original RF checkpoint, or train a replacement on provenance-controlled CICIDS2017 training data and independently evaluate the entire MoE/gating network.
3. Run tests and Docker against the actual GitHub branch before merging.

**No claim of production readiness or CICIDS2017 performance is made.**
