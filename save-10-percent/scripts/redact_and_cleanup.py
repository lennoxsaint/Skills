#!/usr/bin/env python3
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from save10_core import write_json

parser = argparse.ArgumentParser(description="Delete raw working inputs and write a deletion receipt.")
parser.add_argument("receipt")
parser.add_argument("paths", nargs="+")
parser.add_argument("--confirm-delete", action="store_true", required=True)
parser.add_argument("--case-id")
args = parser.parse_args()
deleted, failures = [], []
protected_artifacts = {"events.jsonl", "case.json", "frozen-batch.json", "execution-receipts.json", "realization-report.md"}
for raw in args.paths:
    path = Path(raw).expanduser().resolve()
    try:
        if path.name in protected_artifacts:
            raise ValueError("refusing to delete a durable proof artifact")
        if path.is_symlink() or not path.is_file():
            raise ValueError("cleanup accepts regular files only")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        size = path.stat().st_size
        path.unlink()
        deleted.append({"path_hash": hashlib.sha256(str(path).encode()).hexdigest(), "content_hash": digest, "bytes": size})
    except Exception as exc:
        failures.append({"path_hash": hashlib.sha256(str(path).encode()).hexdigest(), "error_class": type(exc).__name__})
write_json(args.receipt, {"schema_version": "2.0", "case_id": args.case_id, "deleted_at": datetime.now().astimezone().isoformat(timespec="seconds"), "deleted": deleted, "failures": failures, "note": "Files were unlinked; forensic erasure is not guaranteed on modern filesystems."})
if failures:
    raise SystemExit(1)
