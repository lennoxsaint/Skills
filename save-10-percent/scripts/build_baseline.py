#!/usr/bin/env python3
import argparse
from save10_core import build_baseline, load_json, write_json

parser = argparse.ArgumentParser(description="Build the controllable recurring-spend baseline.")
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--currency", default="AUD")
args = parser.parse_args()
write_json(args.output, build_baseline(load_json(args.input), args.currency))

