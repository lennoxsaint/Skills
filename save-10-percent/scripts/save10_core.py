#!/usr/bin/env python3
"""Stdlib-only deterministic helpers for Save 10%."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
EXCLUDED_CATEGORIES = {"payroll", "tax", "transfer", "debt", "personal", "cogs", "refund"}
RISK_ORDER = {"low": 0, "medium": 1, "medium_high": 2, "high": 3}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_date(value: Any) -> str:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y%m%d", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(raw[: len(datetime.now().strftime(fmt))], fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Unrecognized date: {raw}") from exc


def normalize_merchant(value: Any) -> str:
    text = str(value or "unknown").upper().strip()
    text = re.sub(r"\b(VISA|MASTERCARD|DEBIT|CREDIT|PURCHASE|PAYMENT|CARD)\b", " ", text)
    text = re.sub(r"\b[A-Z0-9]{8,}\b", " ", text)
    text = re.sub(r"[^A-Z0-9&+.' -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text or "UNKNOWN"


def spend_amount(value: Any, debit_hint: Any = None) -> float:
    raw = str(value or "0").replace(",", "").replace("$", "").strip()
    amount = float(raw)
    if debit_hint is not None and str(debit_hint).lower() in {"debit", "dr", "withdrawal"}:
        return abs(amount)
    return abs(amount) if amount < 0 else amount


def _pick(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {str(k).lower().strip(): v for k, v in row.items()}
    for name in names:
        if name in lowered and lowered[name] not in (None, ""):
            return lowered[name]
    return None


def normalize_rows(rows: list[dict[str, Any]], default_currency: str = "AUD") -> dict[str, Any]:
    normalized = []
    warnings = []
    for index, row in enumerate(rows, start=1):
        try:
            date = parse_date(_pick(row, ("date", "transaction date", "posted", "dtposted")))
            description = _pick(row, ("merchant", "description", "name", "payee", "memo"))
            amount = spend_amount(_pick(row, ("amount", "value", "debit", "trnamt")), _pick(row, ("type", "transaction type")))
            currency = str(_pick(row, ("currency", "ccy")) or default_currency).upper()
            if amount == 0:
                warnings.append(f"row {index}: zero amount skipped")
                continue
            normalized.append({
                "date": date,
                "merchant": normalize_merchant(description),
                "amount": round(amount, 2),
                "currency": currency,
                "source_row_hash": hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:12],
            })
        except (TypeError, ValueError) as exc:
            warnings.append(f"row {index}: {exc}")
    normalized.sort(key=lambda item: (item["merchant"], item["date"], item["amount"]))
    return {"schema_version": SCHEMA_VERSION, "transactions": normalized, "warnings": warnings}


def read_transactions(path: str | Path, default_currency: str = "AUD") -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        with source.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    elif suffix == ".json":
        payload = load_json(source)
        rows = payload.get("transactions", payload) if isinstance(payload, dict) else payload
    elif suffix == ".qif":
        rows, current = [], {}
        for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
            if line == "^":
                if current:
                    rows.append(current)
                current = {}
            elif line.startswith("D"):
                current["date"] = line[1:]
            elif line.startswith("T"):
                current["amount"] = line[1:]
            elif line.startswith("P"):
                current["merchant"] = line[1:]
            elif line.startswith("M") and "merchant" not in current:
                current["description"] = line[1:]
        if current:
            rows.append(current)
    elif suffix in {".ofx", ".qfx"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        rows = []
        for block in re.findall(r"<STMTTRN>(.*?)(?:</STMTTRN>|<STMTTRN>)", text, flags=re.I | re.S):
            def field(name: str) -> str:
                match = re.search(rf"<{name}>([^<\r\n]+)", block, flags=re.I)
                return match.group(1).strip() if match else ""
            rows.append({"dtposted": field("DTPOSTED"), "trnamt": field("TRNAMT"), "name": field("NAME") or field("MEMO")})
    else:
        raise ValueError("Supported inputs: CSV, JSON, OFX/QFX, QIF")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Input must contain a list of transaction objects")
    return normalize_rows(rows, default_currency)


def cadence_for_days(days: float) -> tuple[str, float]:
    if 5 <= days <= 9:
        return "weekly", 52 / 12
    if 25 <= days <= 35:
        return "monthly", 1
    if 80 <= days <= 100:
        return "quarterly", 1 / 3
    if 330 <= days <= 400:
        return "annual", 1 / 12
    return "irregular", 0


def detect_recurring(payload: dict[str, Any]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for transaction in payload.get("transactions", []):
        groups[(transaction["merchant"], transaction.get("currency", "AUD"))].append(transaction)
    items = []
    for (merchant, currency), transactions in groups.items():
        if len(transactions) < 2:
            continue
        ordered = sorted(transactions, key=lambda item: item["date"])
        dates = [datetime.fromisoformat(item["date"]).date() for item in ordered]
        intervals = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
        if not intervals:
            continue
        cadence, factor = cadence_for_days(statistics.median(intervals))
        if cadence == "irregular":
            continue
        amounts = [float(item["amount"]) for item in ordered]
        median_amount = statistics.median(amounts)
        variation = (max(amounts) - min(amounts)) / median_amount if median_amount else 1
        items.append({
            "merchant": merchant,
            "currency": currency,
            "cadence": cadence,
            "occurrences": len(ordered),
            "first_seen": ordered[0]["date"],
            "last_seen": ordered[-1]["date"],
            "median_charge": round(median_amount, 2),
            "monthly_equivalent": round(median_amount * factor, 2),
            "confidence": "high" if len(ordered) >= 3 and variation <= 0.15 else "medium",
            "source_row_hashes": [item["source_row_hash"] for item in ordered],
        })
    items.sort(key=lambda item: item["monthly_equivalent"], reverse=True)
    return {"schema_version": SCHEMA_VERSION, "recurring_items": items, "source_warnings": payload.get("warnings", [])}


def build_baseline(items_payload: dict[str, Any], currency: str = "AUD") -> dict[str, Any]:
    included, excluded, total = [], [], 0.0
    for item in items_payload.get("recurring_items", []):
        category = str(item.get("category", "subscription")).lower()
        in_scope = item.get("in_scope", True) and category not in EXCLUDED_CATEGORIES
        if in_scope and item.get("currency", currency) == currency:
            included.append(item)
            total += float(item["monthly_equivalent"])
        else:
            excluded.append({"merchant": item.get("merchant"), "reason": "out_of_scope_or_currency_unconverted"})
    total = round(total, 2)
    return {
        "schema_version": SCHEMA_VERSION,
        "currency": currency,
        "monthly_controllable_spend": total,
        "ten_percent_target": round(total * 0.10, 2),
        "included": included,
        "excluded": excluded,
        "coverage_state": "requires_usage_and_provider_review",
    }


def merge_usage(opportunities: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    evidence_by_merchant = {normalize_merchant(key): value for key, value in evidence.items()}
    rows = []
    for row in opportunities.get("opportunities", opportunities.get("recurring_items", [])):
        merged = dict(row)
        merged.update(evidence_by_merchant.get(normalize_merchant(row.get("merchant")), {}))
        state = merged.get("usage_state", "unverified")
        merged["eligible"] = bool(not merged.get("protected", False) and state in {"owner_confirmed_unused", "probable_unused", "verified_used"} and merged.get("monthly_reduction", 0) > 0)
        rows.append(merged)
    return {"schema_version": SCHEMA_VERSION, "opportunities": rows}


def optimize(opportunities: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    target = float(baseline["ten_percent_target"])
    candidates = [row for row in opportunities.get("opportunities", []) if row.get("eligible") and not row.get("protected")]
    candidates.sort(key=lambda row: (RISK_ORDER.get(row.get("risk", "high"), 9), -float(row.get("monthly_reduction", 0))))
    selected, total = [], 0.0
    for row in candidates:
        selected.append(row)
        total += float(row.get("monthly_reduction", 0))
        if total + 1e-9 >= target:
            break
    total = round(total, 2)
    return {
        "schema_version": SCHEMA_VERSION,
        "proof_state": "candidate",
        "baseline_monthly": baseline["monthly_controllable_spend"],
        "target_monthly": target,
        "selected": selected,
        "projected_monthly_saving": total,
        "projected_percent": round((total / float(baseline["monthly_controllable_spend"])) * 100, 2) if baseline["monthly_controllable_spend"] else 0,
        "target_met": total + 1e-9 >= target,
        "shortfall": round(max(0, target - total), 2),
    }


def canonical_hash(payload: dict[str, Any]) -> str:
    cleaned = dict(payload)
    cleaned.pop("batch_hash", None)
    return hashlib.sha256(json.dumps(cleaned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def validate_and_freeze(payload: dict[str, Any], approval: str | None = None) -> dict[str, Any]:
    required = {"provider", "action", "current_monthly_cost", "future_monthly_cost", "monthly_reduction", "evidence", "consequence", "recovery_path", "execution_gate"}
    errors = []
    rows = payload.get("selected", payload.get("recommended_batch", []))
    for index, row in enumerate(rows):
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")
        if float(row.get("monthly_reduction", 0)) < 0:
            errors.append(f"row {index}: negative saving")
        expected = round(float(row.get("current_monthly_cost", 0)) - float(row.get("future_monthly_cost", 0)), 2)
        if "monthly_reduction" in row and abs(expected - float(row["monthly_reduction"])) > 0.01:
            errors.append(f"row {index}: saving arithmetic mismatch")
        if row.get("annual_commitment"):
            errors.append(f"row {index}: unapproved annual commitment")
    if errors:
        raise ValueError("; ".join(errors))
    frozen = dict(payload)
    if approval:
        frozen["proof_state"] = "approved"
        frozen["owner_approval"] = approval
        frozen["approved_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    frozen["batch_hash"] = canonical_hash(frozen)
    return frozen

