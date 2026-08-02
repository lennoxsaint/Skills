#!/usr/bin/env python3
import argparse
from save10_core import detect_recurring, load_json, write_json

parser = argparse.ArgumentParser(description="Detect recurring charges in normalized transactions.")
parser.add_argument("input")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, detect_recurring(load_json(args.input)))

