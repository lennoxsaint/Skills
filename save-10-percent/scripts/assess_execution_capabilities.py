#!/usr/bin/env python3
import argparse

from save10_core import assess_execution_capabilities, load_json, write_json

parser = argparse.ArgumentParser(description="Choose autonomous browser execution or a guided checklist.")
parser.add_argument("capabilities")
parser.add_argument("output")
args = parser.parse_args()
write_json(args.output, assess_execution_capabilities(load_json(args.capabilities)))
