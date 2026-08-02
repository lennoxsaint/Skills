#!/usr/bin/env python3
import argparse
from save10_core import load_json, merge_usage, write_json

parser = argparse.ArgumentParser(description="Merge usage evidence into recurring-cost opportunities.")
parser.add_argument("opportunities")
parser.add_argument("evidence")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, merge_usage(load_json(args.opportunities), load_json(args.evidence)))

