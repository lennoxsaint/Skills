#!/usr/bin/env python3
import argparse

from save10_core import load_json, reconcile_transactions, write_json

parser = argparse.ArgumentParser(description="Deduplicate transactions and reconcile cross-account transfers.")
parser.add_argument("input")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, reconcile_transactions(load_json(args.input)))
