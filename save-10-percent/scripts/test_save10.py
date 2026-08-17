#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from save10_core import (
    CaseStore,
    assess_execution_capabilities,
    assess_coverage,
    build_baseline,
    calculate_net_savings,
    combine_sources,
    detect_recurring,
    normalize_rows,
    optimize,
    parse_statement_text,
    reconcile_transactions,
    validate_and_freeze,
    validate_execution_preflight,
)


def monthly_rows(account_id="checking", months=4, merchant="Tool A", amount=-10):
    return [
        {
            "date": f"2026-{month:02d}-01",
            "merchant": merchant,
            "amount": amount,
            "account_id": account_id,
        }
        for month in range(1, months + 1)
    ]


def passing_coverage(state="preliminary_pass"):
    return {
        "schema_version": "2.0",
        "coverage_state": state,
        "coverage_hash": "a" * 64,
        "scope_confirmed": True,
    }


class TransactionSafetyTests(unittest.TestCase):
    def test_income_refunds_and_reversals_never_become_spend(self):
        rows = monthly_rows() + [
            {"date": "2026-01-02", "merchant": "Employer", "amount": 5000, "type": "credit"},
            {"date": "2026-01-03", "merchant": "Tool A refund", "amount": 10, "type": "refund"},
            {"date": "2026-01-04", "merchant": "Reversal", "amount": 10, "type": "reversal"},
        ]
        payload = normalize_rows(rows, account_id="checking", account_type="checking")
        recurring = detect_recurring(payload)
        self.assertEqual([item["merchant"] for item in recurring["recurring_items"]], ["TOOL A"])
        self.assertEqual(recurring["recurring_items"][0]["monthly_equivalent"], 10)
        directions = {item["direction"] for item in payload["transactions"]}
        self.assertTrue({"credit", "refund", "reversal", "debit"}.issubset(directions))

    def test_positive_amount_without_credit_debit_semantics_is_quarantined(self):
        payload = normalize_rows([
            {"date": "2026-01-01", "merchant": "Ambiguous", "amount": 19.99},
        ])
        self.assertEqual(payload["transactions"][0]["direction"], "unknown")
        self.assertFalse(payload["transactions"][0]["eligible_spend"])
        self.assertEqual(len(payload["quarantined"]), 1)

    def test_split_debit_and_credit_columns_are_direction_safe(self):
        payload = normalize_rows([
            {"date": "2026-01-01", "description": "Subscription", "debit": "20.00", "credit": ""},
            {"date": "2026-01-02", "description": "Refund", "debit": "", "credit": "20.00"},
        ])
        self.assertEqual(payload["transactions"][0]["signed_amount"], -20)
        self.assertEqual(payload["transactions"][0]["direction"], "debit")
        self.assertEqual(payload["transactions"][1]["signed_amount"], 20)
        self.assertEqual(payload["transactions"][1]["direction"], "credit")

    def test_explicit_us_date_order_prevents_silent_day_month_swap(self):
        payload = normalize_rows([
            {"date": "02/13/2026", "merchant": "US Tool", "amount": -10},
        ], date_order="MDY")
        self.assertEqual(payload["transactions"][0]["date"], "2026-02-13")

    def test_cross_account_card_payment_is_reconciled_without_hiding_card_spend(self):
        rows = [
            {"date": "2026-01-10", "merchant": "Credit Card Payment", "amount": -100, "account_id": "checking"},
            {"date": "2026-01-11", "merchant": "Payment received", "amount": 100, "account_id": "card", "type": "transfer"},
            {"date": "2026-01-03", "merchant": "Useful SaaS", "amount": -100, "account_id": "card"},
        ]
        reconciled = reconcile_transactions(normalize_rows(rows))
        transfers = [row for row in reconciled["transactions"] if row["direction"] == "transfer"]
        spend = [row for row in reconciled["transactions"] if row["eligible_spend"]]
        self.assertEqual(len(transfers), 2)
        self.assertEqual([row["merchant"] for row in spend], ["USEFUL SAAS"])

    def test_duplicate_rows_with_same_provider_transaction_id_are_removed(self):
        rows = [
            {"date": "2026-01-01", "merchant": "Tool", "amount": -10, "id": "bank-transaction-1"},
            {"date": "2026-01-01", "merchant": "Tool", "amount": -10, "id": "bank-transaction-1"},
        ]
        reconciled = reconcile_transactions(normalize_rows(rows))
        self.assertEqual(len(reconciled["transactions"]), 1)
        self.assertEqual(reconciled["reconciliation"]["duplicate_count"], 1)

    def test_legitimate_same_day_charges_with_distinct_ids_are_retained(self):
        rows = [
            {"date": "2026-01-01", "merchant": "Tool", "amount": -10, "id": "bank-transaction-1"},
            {"date": "2026-01-01", "merchant": "Tool", "amount": -10, "id": "bank-transaction-2"},
        ]
        reconciled = reconcile_transactions(normalize_rows(rows))
        self.assertEqual(len(reconciled["transactions"]), 2)
        self.assertEqual(reconciled["reconciliation"]["duplicate_count"], 0)

    def test_same_day_identical_rows_without_provider_ids_are_not_silently_dropped(self):
        rows = monthly_rows(months=1) * 2
        reconciled = reconcile_transactions(normalize_rows(rows))
        self.assertEqual(len(reconciled["transactions"]), 2)
        self.assertEqual(reconciled["reconciliation"]["duplicate_candidate_count"], 2)

    def test_same_merchant_on_two_accounts_remains_two_liabilities(self):
        rows = monthly_rows("card-a", 3, "Music") + monthly_rows("card-b", 3, "Music")
        recurring = detect_recurring(normalize_rows(rows))
        self.assertEqual(len(recurring["recurring_items"]), 2)
        self.assertNotEqual(
            recurring["recurring_items"][0]["liability_id"],
            recurring["recurring_items"][1]["liability_id"],
        )

    def test_same_merchant_and_account_with_distinct_liability_hints_remain_separate(self):
        rows = []
        for month in range(1, 4):
            rows.extend([
                {"date": f"2026-{month:02d}-01", "merchant": "Suite", "amount": -10, "account_id": "card", "subscription_id": "product-a"},
                {"date": f"2026-{month:02d}-02", "merchant": "Suite", "amount": -20, "account_id": "card", "subscription_id": "product-b"},
            ])
        recurring = detect_recurring(normalize_rows(rows))
        self.assertEqual(len(recurring["recurring_items"]), 2)
        self.assertTrue(all(item["unique_liability_confirmed"] for item in recurring["recurring_items"]))

    def test_long_vendor_name_is_not_erased_as_an_identifier(self):
        payload = normalize_rows(monthly_rows(merchant="ElevenLabs", months=2))
        self.assertEqual(payload["transactions"][0]["merchant"], "ELEVENLABS")

    def test_duplicate_source_content_is_not_combined_twice(self):
        source = normalize_rows(monthly_rows(months=2))
        source["source_manifest"] = {
            "source_id": "source-a",
            "source_content_hash": "a" * 64,
        }
        combined = combine_sources([source, source])
        self.assertEqual(len(combined["transactions"]), 2)
        self.assertEqual(combined["duplicate_sources"], ["source-a"])

    def test_detects_fortnightly_monthly_and_annual(self):
        rows = [
            {"date": "2026-01-01", "merchant": "Fortnight", "amount": -10},
            {"date": "2026-01-15", "merchant": "Fortnight", "amount": -10},
            {"date": "2026-01-29", "merchant": "Fortnight", "amount": -10},
        ] + monthly_rows(merchant="Monthly", amount=-20) + [
            {"date": "2025-01-10", "merchant": "Annual", "amount": -120},
            {"date": "2026-01-10", "merchant": "Annual", "amount": -120},
        ]
        recurring = detect_recurring(normalize_rows(rows))
        values = {item["merchant"]: item for item in recurring["recurring_items"]}
        self.assertEqual(values["FORTNIGHT"]["cadence"], "fortnightly")
        self.assertEqual(values["FORTNIGHT"]["monthly_equivalent"], 21.67)
        self.assertEqual(values["MONTHLY"]["monthly_equivalent"], 20)
        self.assertEqual(values["ANNUAL"]["monthly_equivalent"], 10)


class CoverageAndSavingsTests(unittest.TestCase):
    def test_coverage_blocks_missing_declared_account(self):
        payload = normalize_rows(monthly_rows("checking", 4))
        coverage = assess_coverage(payload, {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}, {"account_id": "card"}],
        })
        self.assertEqual(coverage["coverage_state"], "blocked")
        self.assertIn("card", coverage["missing_accounts"])

    def test_coverage_blocks_unexpected_account_and_unresolved_duplicate_candidates(self):
        rows = monthly_rows("checking", 4) + monthly_rows("undeclared", 4)
        duplicate = rows + [dict(rows[0])]
        coverage = assess_coverage(reconcile_transactions(normalize_rows(duplicate)), {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}],
        })
        self.assertEqual(coverage["coverage_state"], "blocked")
        self.assertIn("undeclared", coverage["unexpected_accounts"])
        self.assertIn("unresolved_duplicate_candidates", coverage["blockers"])

    def test_coverage_blocks_ambiguous_direction(self):
        rows = monthly_rows("checking", 4) + [
            {"date": "2026-02-02", "merchant": "Unknown", "amount": 9.99, "account_id": "checking"},
        ]
        coverage = assess_coverage(normalize_rows(rows), {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}],
        })
        self.assertEqual(coverage["coverage_state"], "blocked")
        self.assertEqual(coverage["ambiguous_direction_count"], 1)

    def test_progressive_gate_passes_preliminary_then_annual_evidence(self):
        payload = normalize_rows(monthly_rows("checking", 4))
        preliminary = assess_coverage(payload, {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}],
        })
        exhaustive = assess_coverage(payload, {
            "scope_confirmed": True,
            "annual_evidence_complete": True,
            "accounts": [{"account_id": "checking"}],
        })
        self.assertEqual(preliminary["coverage_state"], "preliminary_pass")
        self.assertEqual(exhaustive["coverage_state"], "exhaustive_pass")

    def test_exhaustive_history_requires_thirteen_distinct_calendar_months(self):
        twelve_months = [
            {"date": f"2025-{month:02d}-01", "merchant": "Tool", "amount": -10, "account_id": "checking"}
            for month in range(1, 13)
        ]
        thirteen_months = twelve_months + [
            {"date": "2026-01-02", "merchant": "Tool", "amount": -10, "account_id": "checking"}
        ]
        declaration = {"scope_confirmed": True, "accounts": [{"account_id": "checking"}]}
        self.assertEqual(assess_coverage(normalize_rows(twelve_months), declaration)["coverage_state"], "preliminary_pass")
        self.assertEqual(assess_coverage(normalize_rows(thirteen_months), declaration)["coverage_state"], "exhaustive_pass")

    def test_coverage_blocks_short_history_and_material_gap(self):
        short = assess_coverage(normalize_rows(monthly_rows("checking", 2)), {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}],
        })
        gapped_rows = [
            {"date": "2026-01-01", "merchant": "A", "amount": -10, "account_id": "checking"},
            {"date": "2026-01-15", "merchant": "B", "amount": -10, "account_id": "checking"},
            {"date": "2026-04-30", "merchant": "C", "amount": -10, "account_id": "checking"},
        ]
        gapped = assess_coverage(normalize_rows(gapped_rows), {
            "scope_confirmed": True,
            "accounts": [{"account_id": "checking"}],
        })
        self.assertEqual(short["coverage_state"], "blocked")
        self.assertEqual(gapped["coverage_state"], "blocked")
        self.assertTrue(gapped["account_coverage"][0]["material_gap"])

    def test_baseline_requires_passing_coverage_and_excludes_other_currency(self):
        items = {"recurring_items": [
            {"liability_id": "a", "merchant": "AUD TOOL", "currency": "AUD", "monthly_equivalent": 50},
            {"liability_id": "b", "merchant": "USD TOOL", "currency": "USD", "monthly_equivalent": 50},
        ]}
        with self.assertRaises(ValueError):
            build_baseline(items, {"coverage_state": "blocked"})
        baseline = build_baseline(items, passing_coverage(), "AUD")
        self.assertEqual(baseline["monthly_controllable_spend"], 50)
        self.assertEqual(baseline["ten_percent_target"], 5)
        self.assertEqual(len(baseline["excluded"]), 1)

    def test_protected_services_are_excluded_and_bound_into_baseline_hash(self):
        items = {"recurring_items": [
            {"liability_id": "required", "merchant": "Required Tool", "currency": "AUD", "monthly_equivalent": 80},
            {"liability_id": "optional", "merchant": "Optional Tool", "currency": "AUD", "monthly_equivalent": 20},
        ]}
        protected = build_baseline(items, passing_coverage(), "AUD", ["Required Tool"])
        unprotected = build_baseline(items, passing_coverage(), "AUD", [])
        self.assertEqual(protected["monthly_controllable_spend"], 20)
        self.assertEqual(protected["protected_services"], ["Required Tool"])
        self.assertNotEqual(protected["baseline_hash"], unprotected["baseline_hash"])

    def test_net_savings_deducts_replacement_and_one_off_costs(self):
        result = calculate_net_savings({
            "current_monthly_cost": 100,
            "future_monthly_cost": 25,
            "exit_fees": 60,
            "setup_costs": 60,
            "lost_bundle_value_12m": 120,
            "migration_costs": 0,
        })
        self.assertEqual(result["gross_12_month_saving"], 900)
        self.assertEqual(result["net_12_month_saving"], 660)
        self.assertEqual(result["net_monthly_equivalent"], 55)

    def test_optimizer_uses_net_reduction_and_keeps_shortfall_honest(self):
        opportunities = {"opportunities": [
            {"liability_id": "protected", "eligible": True, "protected": True, "risk": "low", "net_monthly_equivalent": 50},
            {"liability_id": "safe", "eligible": True, "protected": False, "risk": "low", "net_monthly_equivalent": 5},
        ]}
        result = optimize(opportunities, {"monthly_controllable_spend": 100, "ten_percent_target": 10, "baseline_hash": "b" * 64})
        self.assertFalse(result["target_met"])
        self.assertEqual(result["shortfall"], 5)
        self.assertEqual([row["liability_id"] for row in result["selected"]], ["safe"])


class ApprovalAndPersistenceTests(unittest.TestCase):
    def action_row(self):
        return {
            "liability_id": "liability-1",
            "provider": "Vendor",
            "account_id": "card",
            "action": "cancel",
            "current_plan": "Pro",
            "target_plan": "Cancelled",
            "current_monthly_cost": 20,
            "future_monthly_cost": 0,
            "currency": "AUD",
            "renewal": "monthly",
            "net_monthly_equivalent": 20,
            "evidence_snapshot_id": "evidence-1",
            "consequence": "Access ends",
            "recovery_path": "Reactivate",
            "execution_gate": "live-preflight",
            "risk": "low",
        }

    def test_freeze_binds_baseline_and_expiry(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        frozen = validate_and_freeze(
            {"selected": [self.action_row()], "baseline_hash": "b" * 64},
            approval="Approve exact batch",
            now=now,
        )
        self.assertEqual(frozen["proof_state"], "approved")
        self.assertEqual(len(frozen["batch_hash"]), 64)
        self.assertEqual(frozen["expires_at"], "2026-01-02T00:00:00+00:00")

    def test_preflight_stops_expired_or_changed_action(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        frozen = validate_and_freeze(
            {"selected": [self.action_row()], "baseline_hash": "b" * 64},
            approval="Approve exact batch",
            now=now,
        )
        expired = validate_execution_preflight(frozen, [self.action_row()], now=now + timedelta(days=2))
        self.assertFalse(expired["ready"])
        self.assertEqual(expired["status"], "expired_approval")

        changed = self.action_row()
        changed["current_monthly_cost"] = 25
        drift = validate_execution_preflight(frozen, [changed], now=now + timedelta(hours=1))
        self.assertFalse(drift["ready"])
        self.assertIn("current_monthly_cost", drift["items"][0]["changed_fields"])

    def test_high_risk_action_requires_item_confirmation_and_annual_commitment_fails(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        row = self.action_row()
        row["risk"] = "high"
        frozen = validate_and_freeze(
            {"selected": [row], "baseline_hash": "b" * 64},
            approval="Approve exact batch",
            now=now,
        )
        self.assertTrue(frozen["selected"][0]["item_level_confirmation_required"])
        missing = validate_execution_preflight(frozen, [row], now=now + timedelta(minutes=5))
        self.assertFalse(missing["ready"])
        self.assertIn("item_level_confirmation_required", missing["items"][0]["changed_fields"])
        confirmed = validate_execution_preflight(
            frozen,
            [row],
            now=now + timedelta(minutes=5),
            item_confirmations={
                "liability-1": {
                    "batch_hash": frozen["batch_hash"],
                    "confirmed_at": "2026-01-01T00:04:00+00:00",
                    "confirmation": "Confirm this high-risk item",
                }
            },
        )
        self.assertTrue(confirmed["ready"])
        row["annual_commitment"] = True
        with self.assertRaises(ValueError):
            validate_and_freeze({"selected": [row], "baseline_hash": "b" * 64})

    def test_freeze_requires_currency_and_renewal_terms(self):
        row = self.action_row()
        del row["currency"]
        with self.assertRaisesRegex(ValueError, "currency"):
            validate_and_freeze({"selected": [row], "baseline_hash": "b" * 64})

    def test_case_store_replays_and_rejects_invalid_jump(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore.create(Path(directory), "AUD", ["Required Tool"])
            store.transition("scope", {"scope_confirmed": True})
            store.record("answer", {"protected": ["Required Tool"]})
            replayed = CaseStore.open(store.case_dir)
            self.assertEqual(replayed.snapshot["state"], "scope")
            self.assertEqual(replayed.snapshot["answers"][0]["protected"], ["Required Tool"])
            with self.assertRaises(ValueError):
                replayed.transition("execute", {})

    def test_case_log_hash_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore.create(Path(directory), "AUD", [])
            events = store.events_path.read_text().splitlines()
            payload = json.loads(events[0])
            payload["payload"]["currency"] = "USD"
            store.events_path.write_text(json.dumps(payload) + "\n")
            with self.assertRaises(ValueError):
                CaseStore.open(store.case_dir)

    def test_case_store_rejects_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore.create(Path(directory), "AUD", [])
            with self.assertRaises(ValueError):
                store.record("answer", {"api_key": "must-never-be-stored"})
            with self.assertRaises(ValueError):
                store.record("answer", {"note": "my password is must-never-be-stored"})

    def test_scheduled_provider_change_is_a_first_class_state(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore.create(Path(directory), "AUD", [])
            for state in (
                "scope", "acquire_sources", "coverage", "normalize", "reconcile", "recurring",
                "vendor_review", "net_candidates", "freeze_or_shortfall", "approval", "preflight", "execute",
            ):
                store.transition(state, {})
            store.transition("scheduled", {"effective_at": "2026-02-01"})
            self.assertEqual(store.snapshot["state"], "scheduled")
            store.transition("provider_confirmed", {"confirmation_id": "redacted"})
            self.assertEqual(store.snapshot["state"], "provider_confirmed")

    def test_browser_execution_falls_back_unless_every_capability_is_proven(self):
        missing = assess_execution_capabilities({"authenticated_browser": True})
        complete = assess_execution_capabilities({
            "authenticated_browser": True,
            "live_account_readback": True,
            "before_after_capture": True,
            "interruptible_security_prompts": True,
            "durable_receipts": True,
        })
        self.assertEqual(missing["mode"], "guided_checklist")
        self.assertFalse(missing["autonomous_execution_allowed"])
        self.assertEqual(complete["mode"], "autonomous_browser")
        self.assertTrue(complete["autonomous_execution_allowed"])


class PdfExtractionTests(unittest.TestCase):
    def test_text_statement_parser_requires_confident_transaction_lines(self):
        text = """
        01/01/2026 Project Board Pro -40.00
        01/02/2026 Project Board Pro -40.00
        01/03/2026 Project Board Pro -40.00
        """
        rows, confidence = parse_statement_text(text)
        self.assertEqual(len(rows), 3)
        self.assertGreaterEqual(confidence, 0.95)
        self.assertEqual(rows[0]["merchant"], "Project Board Pro")

    def test_text_statement_parser_fails_closed_on_ambiguous_pdf(self):
        with self.assertRaises(ValueError):
            parse_statement_text("Balance 100.00\nNothing resembling a transaction")


if __name__ == "__main__":
    unittest.main()
