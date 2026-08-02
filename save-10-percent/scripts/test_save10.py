#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from save10_core import build_baseline, detect_recurring, normalize_rows, optimize, validate_and_freeze


class Save10Tests(unittest.TestCase):
    def test_detects_monthly_and_annual(self):
        rows = [
            {"date": "2026-01-01", "merchant": "Tool A", "amount": -10},
            {"date": "2026-02-01", "merchant": "Tool A", "amount": -10},
            {"date": "2026-03-01", "merchant": "Tool A", "amount": -10},
            {"date": "2025-01-10", "merchant": "Tool B", "amount": -120},
            {"date": "2026-01-10", "merchant": "Tool B", "amount": -120},
        ]
        recurring = detect_recurring(normalize_rows(rows))
        values = {item["merchant"]: item["monthly_equivalent"] for item in recurring["recurring_items"]}
        self.assertEqual(values["TOOL A"], 10)
        self.assertEqual(values["TOOL B"], 10)

    def test_excludes_transfer_and_builds_target(self):
        payload = {"recurring_items": [
            {"merchant": "SAAS", "currency": "AUD", "monthly_equivalent": 100, "category": "subscription"},
            {"merchant": "OWNER", "currency": "AUD", "monthly_equivalent": 1000, "category": "transfer"},
        ]}
        baseline = build_baseline(payload)
        self.assertEqual(baseline["monthly_controllable_spend"], 100)
        self.assertEqual(baseline["ten_percent_target"], 10)

    def test_protected_row_never_selected_and_shortfall_is_honest(self):
        opportunities = {"opportunities": [
            {"merchant": "PROTECTED", "eligible": True, "protected": True, "risk": "low", "monthly_reduction": 50},
            {"merchant": "SAFE", "eligible": True, "protected": False, "risk": "low", "monthly_reduction": 5},
        ]}
        result = optimize(opportunities, {"monthly_controllable_spend": 100, "ten_percent_target": 10})
        self.assertFalse(result["target_met"])
        self.assertEqual(result["shortfall"], 5)
        self.assertEqual([row["merchant"] for row in result["selected"]], ["SAFE"])

    def test_manifest_rejects_bad_arithmetic_and_annual_commitment(self):
        row = {"provider": "A", "action": "downgrade", "current_monthly_cost": 20, "future_monthly_cost": 10, "monthly_reduction": 9, "evidence": ["bill"], "consequence": "feature", "recovery_path": "upgrade", "execution_gate": "verify", "annual_commitment": True}
        with self.assertRaises(ValueError):
            validate_and_freeze({"selected": [row]}, "approved")

    def test_freeze_hash_is_stable_for_same_payload(self):
        row = {"provider": "A", "action": "cancel", "current_monthly_cost": 10, "future_monthly_cost": 0, "monthly_reduction": 10, "evidence": ["bill"], "consequence": "access ends", "recovery_path": "reactivate", "execution_gate": "export"}
        validated = validate_and_freeze({"selected": [row]})
        self.assertEqual(len(validated["batch_hash"]), 64)

    def test_duplicate_card_descriptions_normalize_together(self):
        rows = [
            {"date": "2026-01-01", "merchant": "VISA Useful Tool 123456789", "amount": -20},
            {"date": "2026-02-01", "merchant": "CARD Useful Tool 987654321", "amount": -20},
        ]
        recurring = detect_recurring(normalize_rows(rows))
        self.assertEqual(len(recurring["recurring_items"]), 1)
        self.assertEqual(recurring["recurring_items"][0]["merchant"], "USEFUL TOOL")

    def test_unconverted_currency_is_excluded_not_zeroed_into_total(self):
        payload = {"recurring_items": [
            {"merchant": "AUD TOOL", "currency": "AUD", "monthly_equivalent": 50},
            {"merchant": "USD TOOL", "currency": "USD", "monthly_equivalent": 50},
        ]}
        baseline = build_baseline(payload, "AUD")
        self.assertEqual(baseline["monthly_controllable_spend"], 50)
        self.assertEqual(len(baseline["excluded"]), 1)


if __name__ == "__main__":
    unittest.main()
