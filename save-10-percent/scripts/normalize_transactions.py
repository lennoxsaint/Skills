#!/usr/bin/env python3
import argparse
from save10_core import read_transactions, write_json

parser = argparse.ArgumentParser(description="Normalize CSV, JSON, OFX/QFX, or QIF transactions.")
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--currency", default="AUD")
args = parser.parse_args()
write_json(args.output, read_transactions(args.input, args.currency))

