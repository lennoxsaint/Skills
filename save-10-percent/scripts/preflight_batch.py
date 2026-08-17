#!/usr/bin/env python3
import argparse

from save10_core import load_json, validate_execution_preflight, write_json

parser = argparse.ArgumentParser(description="Compare a frozen approved batch with live provider state.")
parser.add_argument("frozen_batch")
parser.add_argument("live_items")
parser.add_argument("output")
parser.add_argument("--item-confirmations", help="JSON confirmations bound to the approved batch hash")
args = parser.parse_args()
write_json(
    args.output,
    validate_execution_preflight(
        load_json(args.frozen_batch),
        load_json(args.live_items),
        item_confirmations=load_json(args.item_confirmations) if args.item_confirmations else None,
    ),
)
