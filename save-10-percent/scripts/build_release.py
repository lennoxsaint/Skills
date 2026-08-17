#!/usr/bin/env python3
import argparse
import hashlib
import os
import zipfile
from pathlib import Path


parser = argparse.ArgumentParser(description="Build a deterministic, skill-folder-only release ZIP.")
parser.add_argument("skill_dir")
parser.add_argument("output")
args = parser.parse_args()

skill_dir = Path(args.skill_dir).resolve()
output = Path(args.output).resolve()
output.parent.mkdir(parents=True, exist_ok=True)
files = sorted(
    path for path in skill_dir.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.parts
    and path.suffix not in {".pyc", ".pyo"}
    and not path.name.startswith("test_")
)
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in files:
        relative = Path(skill_dir.name) / path.relative_to(skill_dir)
        info = zipfile.ZipInfo(str(relative), date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
        archive.writestr(info, path.read_bytes())
digest = hashlib.sha256(output.read_bytes()).hexdigest()
print(f"{digest}  {output.name}")
