#!/usr/bin/env python3
import argparse
from save10_core import load_json, validate_and_freeze, write_json

parser = argparse.ArgumentParser(description="Validate and optionally freeze an approved savings batch.")
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--approval", help="Exact owner approval text; omit for validation only")
args = parser.parse_args()
write_json(args.output, validate_and_freeze(load_json(args.input), args.approval))

