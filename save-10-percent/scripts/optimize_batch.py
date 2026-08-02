#!/usr/bin/env python3
import argparse
from save10_core import load_json, optimize, write_json

parser = argparse.ArgumentParser(description="Select the lowest-risk batch that reaches 10 percent.")
parser.add_argument("opportunities")
parser.add_argument("baseline")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, optimize(load_json(args.opportunities), load_json(args.baseline)))

