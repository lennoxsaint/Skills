#!/usr/bin/env python3
import argparse
from save10_core import read_transactions, write_json

parser = argparse.ArgumentParser(description="Normalize CSV, JSON, OFX/QFX, QIF, or confidence-gated text-PDF transactions.")
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("--currency", default="AUD")
parser.add_argument("--account-id", default="default")
parser.add_argument("--account-type", default="unknown")
parser.add_argument("--date-order", choices=("DMY", "MDY"), default="DMY")
args = parser.parse_args()
write_json(
    args.output,
    read_transactions(args.input, args.currency, args.account_id, args.account_type, args.date_order),
)
