#!/usr/bin/env python3
import argparse
from save10_core import build_baseline, load_json, write_json

parser = argparse.ArgumentParser(description="Build the controllable recurring-spend baseline.")
parser.add_argument("input")
parser.add_argument("coverage")
parser.add_argument("output")
parser.add_argument("--currency", default="AUD")
parser.add_argument("--protected-services", help="JSON list or case object containing protected_services")
args = parser.parse_args()
protected_services = []
if args.protected_services:
    protected_payload = load_json(args.protected_services)
    protected_services = (
        protected_payload.get("protected_services", [])
        if isinstance(protected_payload, dict)
        else protected_payload
    )
write_json(
    args.output,
    build_baseline(load_json(args.input), load_json(args.coverage), args.currency, protected_services),
)
