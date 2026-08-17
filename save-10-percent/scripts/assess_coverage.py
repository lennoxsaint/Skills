#!/usr/bin/env python3
import argparse

from save10_core import assess_coverage, load_json, write_json

parser = argparse.ArgumentParser(description="Apply the preliminary and exhaustive source-coverage gates.")
parser.add_argument("transactions")
parser.add_argument("scope_declaration")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, assess_coverage(load_json(args.transactions), load_json(args.scope_declaration)))
