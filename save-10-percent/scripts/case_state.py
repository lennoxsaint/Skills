#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from save10_core import CaseStore

parser = argparse.ArgumentParser(description="Create, resume, and advance a durable Save 10% case.")
subparsers = parser.add_subparsers(dest="command", required=True)

create = subparsers.add_parser("create")
create.add_argument("--root", default=str(Path.home() / ".save10" / "cases"))
create.add_argument("--currency", default="AUD")
create.add_argument("--protected", action="append", default=[])
create.add_argument("--case-id")

show = subparsers.add_parser("show")
show.add_argument("case_dir")

transition = subparsers.add_parser("transition")
transition.add_argument("case_dir")
transition.add_argument("to_state")
transition.add_argument("--data", default="{}", help="JSON object; secrets are rejected")

record = subparsers.add_parser("record")
record.add_argument("case_dir")
record.add_argument("event_type", choices=("answer", "artifact", "approval", "error"))
record.add_argument("--data", required=True, help="JSON object; secrets are rejected")

args = parser.parse_args()
if args.command == "create":
    store = CaseStore.create(args.root, args.currency, args.protected, args.case_id)
elif args.command == "show":
    store = CaseStore.open(args.case_dir)
elif args.command == "transition":
    store = CaseStore.open(args.case_dir)
    store.transition(args.to_state, json.loads(args.data))
else:
    store = CaseStore.open(args.case_dir)
    store.record(args.event_type, json.loads(args.data))
print(json.dumps({"case_dir": str(store.case_dir), "snapshot": store.snapshot}, indent=2))
