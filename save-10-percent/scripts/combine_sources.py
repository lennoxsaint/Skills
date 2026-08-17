#!/usr/bin/env python3
import argparse

from save10_core import combine_sources, load_json, write_json

parser = argparse.ArgumentParser(description="Combine normalized sources while rejecting duplicate files.")
parser.add_argument("inputs", nargs="+")
parser.add_argument("--output", required=True)
args = parser.parse_args()
write_json(args.output, combine_sources([load_json(path) for path in args.inputs]))
