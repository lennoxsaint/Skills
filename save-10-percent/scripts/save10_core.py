#!/usr/bin/env python3
"""Deterministic, local-first helpers for the Save 10% skill."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2.0"
PASSING_COVERAGE_STATES = {"preliminary_pass", "exhaustive_pass"}
EXCLUDED_CATEGORIES = {"payroll", "tax", "transfer", "debt", "personal", "cogs", "refund"}
RISK_ORDER = {"low": 0, "medium": 1, "medium_high": 2, "high": 3, "irreversible": 4}
SECRET_KEY_PATTERN = re.compile(r"password|passcode|token|secret|cookie|api.?key|credential", re.I)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\b(?:password|passcode|api[ _-]?key|access[ _-]?token|secret|cookie)\s*(?:is|=|:)\s*\S+", re.I),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(?:sk|gh[pousr])[-_][A-Za-z0-9_-]{16,}\b"),
)

CASE_TRANSITIONS = {
    "intake": {"scope"},
    "scope": {"acquire_sources"},
    "acquire_sources": {"coverage"},
    "coverage": {"acquire_sources", "normalize"},
    "normalize": {"reconcile"},
    "reconcile": {"recurring", "acquire_sources"},
    "recurring": {"vendor_review"},
    "vendor_review": {"vendor_review", "alternative_research", "net_candidates"},
    "alternative_research": {"vendor_review", "net_candidates"},
    "net_candidates": {"vendor_review", "freeze_or_shortfall"},
    "freeze_or_shortfall": {"approval", "cleanup"},
    "approval": {"preflight", "expired_approval"},
    "preflight": {"execute", "stopped_material_change", "expired_approval"},
    "execute": {"scheduled", "provider_confirmed", "failed", "blocked"},
    "scheduled": {"provider_confirmed", "effective", "failed", "blocked"},
    "provider_confirmed": {"effective"},
    "effective": {"statement_realized"},
    "statement_realized": {"cleanup"},
    "blocked": {"acquire_sources", "vendor_review", "preflight"},
    "failed": {"preflight", "execute"},
    "stopped_material_change": {"vendor_review", "approval"},
    "expired_approval": {"approval"},
    "cleanup": set(),
    "insufficient_coverage": {"acquire_sources"},
    "user_aborted": set(),
}
EXCEPTION_STATES = {"blocked", "failed", "insufficient_coverage", "user_aborted"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime | None = None) -> str:
    return (value or utc_now()).astimezone(timezone.utc).isoformat(timespec="seconds")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def parse_date(value: Any, date_order: str = "DMY") -> str:
    raw = str(value or "").strip()
    slash_formats = (
        ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y")
        if date_order.upper() == "DMY"
        else ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y")
    )
    formats = (
        "%Y-%m-%d",
        "%Y%m%d",
        "%Y%m%d%H%M%S",
    ) + slash_formats
    for fmt in formats:
        try:
            return datetime.strptime(raw[:19], fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Unrecognized date: {raw}") from exc


def normalize_merchant(value: Any) -> str:
    text = str(value or "unknown").upper().strip()
    text = re.sub(r"^(?:(?:VISA|MASTERCARD|DEBIT|CREDIT|PURCHASE|CARD)\s+)+", "", text)
    text = re.sub(r"\b(?=[A-Z0-9]{8,}\b)(?=[A-Z0-9]*\d)[A-Z0-9]+\b", " ", text)
    text = re.sub(r"[^A-Z0-9&+.' -]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text or "UNKNOWN"


def _pick(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {str(key).lower().strip(): value for key, value in row.items()}
    for name in names:
        if name in lowered and lowered[name] not in (None, ""):
            return lowered[name]
    return None


def _decimal(value: Any) -> float:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("missing amount")
    negative_parentheses = raw.startswith("(") and raw.endswith(")")
    cleaned = re.sub(r"[^0-9.\-+]", "", raw)
    if cleaned in {"", "+", "-", "."}:
        raise ValueError(f"invalid amount: {raw}")
    amount = float(cleaned)
    return -abs(amount) if negative_parentheses else amount


def _direction_and_amount(row: dict[str, Any], description: str) -> tuple[str, float]:
    debit = _pick(row, ("debit", "withdrawal", "money out"))
    credit = _pick(row, ("credit", "deposit", "money in"))
    type_hint = str(_pick(row, ("type", "transaction type", "trntype")) or "").lower().strip()

    if debit is not None:
        return "debit", -abs(_decimal(debit))
    if credit is not None:
        return "credit", abs(_decimal(credit))

    amount = _decimal(_pick(row, ("amount", "value", "trnamt")))
    combined = f"{type_hint} {description}".lower()

    if any(word in type_hint for word in ("refund", "return")):
        return "refund", abs(amount)
    if "reversal" in type_hint or "reversal" in combined:
        return "reversal", abs(amount)
    if "reimburse" in type_hint or "reimburse" in combined:
        return "reimbursement", abs(amount)
    if "interest" in type_hint:
        return "interest", abs(amount)
    if any(word in type_hint for word in ("credit", "deposit", "payroll", "salary")):
        return "credit", abs(amount)
    if any(word in type_hint for word in ("debit", "withdrawal", "purchase", "fee", "payment")):
        direction = "fee" if "fee" in type_hint else "debit"
        return direction, -abs(amount)
    transfer_markers = (
        "transfer",
        "credit card payment",
        "card payment",
        "payment received",
        "payment thank you",
    )
    if any(marker in combined for marker in transfer_markers):
        return "transfer", amount
    if amount < 0:
        return "debit", amount
    return "unknown", amount


def normalize_rows(
    rows: list[dict[str, Any]],
    default_currency: str = "AUD",
    account_id: str = "default",
    account_type: str = "unknown",
    source_id: str = "inline",
    date_order: str = "DMY",
) -> dict[str, Any]:
    transactions: list[dict[str, Any]] = []
    warnings: list[str] = []
    quarantined: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        try:
            date = parse_date(_pick(row, ("date", "transaction date", "posted", "dtposted")), date_order)
            description = str(_pick(row, ("merchant", "description", "name", "payee", "memo")) or "UNKNOWN")
            direction, signed_amount = _direction_and_amount(row, description)
            if signed_amount == 0:
                warnings.append(f"row {index}: zero amount skipped")
                continue
            currency = str(_pick(row, ("currency", "ccy")) or default_currency).upper()
            row_account = str(_pick(row, ("account_id", "account", "acctid")) or account_id)
            row_account_type = str(_pick(row, ("account_type", "account type")) or account_type)
            merchant = normalize_merchant(description)
            source_row_hash = hashlib.sha256(canonical_json(row).encode()).hexdigest()
            external_transaction_id = _pick(
                row,
                ("fitid", "transaction id", "transaction_id", "bank transaction id", "bank_transaction_id", "id"),
            )
            external_transaction_id_hash = (
                hashlib.sha256(str(external_transaction_id).encode()).hexdigest()[:24]
                if external_transaction_id not in (None, "")
                else None
            )
            liability_hint = _pick(
                row,
                ("liability_id", "subscription id", "subscription_id", "contract id", "contract_id", "plan id", "plan_id"),
            )
            liability_hint_hash = (
                hashlib.sha256(str(liability_hint).encode()).hexdigest()[:24]
                if liability_hint not in (None, "")
                else None
            )
            transaction_id = hashlib.sha256(
                f"{source_id}|{index}|{row_account}|{date}|{signed_amount:.8f}|{currency}|{merchant}|{source_row_hash}".encode()
            ).hexdigest()[:24]
            transaction = {
                "transaction_id": transaction_id,
                "date": date,
                "merchant": merchant,
                "descriptor_hash": hashlib.sha256(description.encode()).hexdigest()[:16],
                "signed_amount": round(signed_amount, 2),
                "amount": round(abs(signed_amount), 2),
                "currency": currency,
                "direction": direction,
                "eligible_spend": direction in {"debit", "fee"},
                "account_id": row_account,
                "account_type": row_account_type,
                "source_id": source_id,
                "source_row_hash": source_row_hash[:16],
                "external_transaction_id_hash": external_transaction_id_hash,
                "liability_hint_hash": liability_hint_hash,
            }
            transactions.append(transaction)
            if direction == "unknown":
                quarantined.append({
                    "transaction_id": transaction_id,
                    "reason": "ambiguous_direction",
                    "date": date,
                    "account_id": row_account,
                    "amount": round(abs(signed_amount), 2),
                    "currency": currency,
                })
        except (TypeError, ValueError) as exc:
            warnings.append(f"row {index}: {exc}")

    transactions.sort(key=lambda item: (item["account_id"], item["date"], item["merchant"], item["signed_amount"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "transactions": transactions,
        "quarantined": quarantined,
        "warnings": warnings,
    }


def parse_statement_text(text: str) -> tuple[list[dict[str, Any]], float]:
    pattern = re.compile(
        r"^\s*(\d{1,4}[/-]\d{1,2}[/-]\d{1,4})\s+(.+?)\s+([(-]?[A-Z$€£]?\s*[0-9][0-9,.]*\.\d{2}\)?)\s*$"
    )
    rows: list[dict[str, Any]] = []
    candidate_lines = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"\d{1,4}[/-]\d{1,2}[/-]\d{1,4}", stripped) or re.search(r"\d+\.\d{2}", stripped):
            candidate_lines += 1
        match = pattern.match(line)
        if match:
            rows.append({"date": match.group(1), "merchant": match.group(2).strip(), "amount": match.group(3)})
    confidence = len(rows) / candidate_lines if candidate_lines else 0.0
    if len(rows) < 2 or confidence < 0.95:
        raise ValueError(
            "PDF extraction confidence is below 95%; request CSV, OFX/QFX, QIF, JSON, or a text-based statement export"
        )
    return rows, round(confidence, 4)


def _read_pdf_rows(source: Path) -> tuple[list[dict[str, Any]], float]:
    executable = shutil.which("pdftotext")
    if not executable:
        raise ValueError("PDF support requires the local pdftotext command; request a CSV/OFX/QIF/JSON export instead")
    result = subprocess.run(
        [executable, "-layout", str(source), "-"],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise ValueError(f"PDF text extraction failed with exit code {result.returncode}")
    return parse_statement_text(result.stdout)


def read_transactions(
    path: str | Path,
    default_currency: str = "AUD",
    account_id: str = "default",
    account_type: str = "unknown",
    date_order: str = "DMY",
) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    suffix = source.suffix.lower()
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    parser_confidence = 1.0

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
        parsed_account = re.search(r"<ACCTID>([^<\r\n]+)", text, flags=re.I)
        if parsed_account and account_id == "default":
            account_id = parsed_account.group(1).strip()
        rows = []
        for block in re.findall(r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|$)", text, flags=re.I | re.S):
            def field(name: str) -> str:
                match = re.search(rf"<{name}>([^<\r\n]+)", block, flags=re.I)
                return match.group(1).strip() if match else ""

            rows.append({
                "dtposted": field("DTPOSTED"),
                "trnamt": field("TRNAMT"),
                "name": field("NAME") or field("MEMO"),
                "trntype": field("TRNTYPE"),
                "fitid": field("FITID"),
            })
    elif suffix == ".pdf":
        rows, parser_confidence = _read_pdf_rows(source)
    else:
        raise ValueError("Supported inputs: CSV, JSON, OFX/QFX, QIF, and confidence-gated text PDF")

    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Input must contain a list of transaction objects")
    source_id = source_digest[:16]
    normalized = normalize_rows(rows, default_currency, account_id, account_type, source_id, date_order)
    normalized["source_manifest"] = {
        "source_id": source_id,
        "source_name_hash": hashlib.sha256(source.name.encode()).hexdigest()[:16],
        "source_content_hash": source_digest,
        "format": suffix.lstrip("."),
        "parser_version": SCHEMA_VERSION,
        "parser_confidence": parser_confidence,
        "date_order": date_order.upper(),
        "account_id": account_id,
        "period_start": min((row["date"] for row in normalized["transactions"]), default=None),
        "period_end": max((row["date"] for row in normalized["transactions"]), default=None),
        "row_count": len(rows),
        "accepted_count": len(normalized["transactions"]),
        "quarantined_count": len(normalized["quarantined"]),
    }
    return normalized


def combine_sources(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    transactions: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    warnings: list[str] = []
    manifests: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    duplicate_sources: list[str] = []
    for payload in payloads:
        manifest = payload.get("source_manifest")
        if manifest:
            digest = manifest["source_content_hash"]
            if digest in seen_sources:
                duplicate_sources.append(manifest["source_id"])
                continue
            seen_sources.add(digest)
            manifests.append(manifest)
        transactions.extend(payload.get("transactions", []))
        quarantined.extend(payload.get("quarantined", []))
        warnings.extend(payload.get("warnings", []))
    return {
        "schema_version": SCHEMA_VERSION,
        "transactions": transactions,
        "quarantined": quarantined,
        "warnings": warnings,
        "source_manifests": manifests,
        "duplicate_sources": duplicate_sources,
    }


def _transfer_hint(transaction: dict[str, Any]) -> bool:
    if transaction.get("direction") == "transfer":
        return True
    merchant = transaction.get("merchant", "").lower()
    return any(marker in merchant for marker in ("transfer", "card payment", "payment received", "payment thank you"))


def reconcile_transactions(payload: dict[str, Any]) -> dict[str, Any]:
    deduped: list[dict[str, Any]] = []
    seen_external_ids: set[tuple[Any, ...]] = set()
    duplicate_ids: list[str] = []
    for transaction in payload.get("transactions", []):
        external_id = transaction.get("external_transaction_id_hash")
        if external_id:
            external_key = (
                transaction.get("account_id"),
                transaction.get("currency"),
                external_id,
            )
            if external_key in seen_external_ids:
                duplicate_ids.append(transaction["transaction_id"])
                continue
            seen_external_ids.add(external_key)
        deduped.append(dict(transaction))

    heuristic_groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for transaction in deduped:
        if transaction.get("external_transaction_id_hash"):
            continue
        heuristic_key = (
            transaction.get("account_id"),
            transaction.get("date"),
            transaction.get("signed_amount"),
            transaction.get("currency"),
            transaction.get("merchant"),
        )
        heuristic_groups[heuristic_key].append(transaction["transaction_id"])
    duplicate_candidates = [
        transaction_id
        for transaction_ids in heuristic_groups.values()
        if len(transaction_ids) > 1
        for transaction_id in transaction_ids
    ]

    matched: set[str] = set()
    transfer_pairs: list[dict[str, Any]] = []
    for index, left in enumerate(deduped):
        if left["transaction_id"] in matched:
            continue
        for right in deduped[index + 1 :]:
            if right["transaction_id"] in matched:
                continue
            if left.get("account_id") == right.get("account_id") or left.get("currency") != right.get("currency"):
                continue
            if abs(float(left.get("signed_amount", 0)) + float(right.get("signed_amount", 0))) > 0.01:
                continue
            left_date = datetime.fromisoformat(left["date"]).date()
            right_date = datetime.fromisoformat(right["date"]).date()
            if abs((left_date - right_date).days) > 3:
                continue
            if not (_transfer_hint(left) or _transfer_hint(right)):
                continue
            pair_id = hashlib.sha256(
                "|".join(sorted((left["transaction_id"], right["transaction_id"]))).encode()
            ).hexdigest()[:20]
            for item in (left, right):
                item["direction"] = "transfer"
                item["eligible_spend"] = False
                item["transfer_pair_id"] = pair_id
                matched.add(item["transaction_id"])
            transfer_pairs.append({"pair_id": pair_id, "transaction_ids": [left["transaction_id"], right["transaction_id"]]})
            break

    unresolved = [item["transaction_id"] for item in deduped if item.get("direction") == "transfer" and item["transaction_id"] not in matched]
    output = dict(payload)
    output["transactions"] = sorted(
        deduped,
        key=lambda item: (item["account_id"], item["date"], item["merchant"], item["signed_amount"]),
    )
    output["reconciliation"] = {
        "duplicate_count": len(duplicate_ids),
        "duplicate_transaction_ids": duplicate_ids,
        "duplicate_candidate_count": len(duplicate_candidates),
        "duplicate_candidate_transaction_ids": duplicate_candidates,
        "transfer_pairs": transfer_pairs,
        "unresolved_transfer_count": len(unresolved),
        "unresolved_transfer_ids": unresolved,
    }
    output["reconciliation_hash"] = content_hash(output["reconciliation"])
    return output


def cadence_for_days(days: float) -> tuple[str, float]:
    if 5 <= days <= 9:
        return "weekly", 52 / 12
    if 12 <= days <= 16:
        return "fortnightly", 26 / 12
    if 25 <= days <= 35:
        return "monthly", 1
    if 55 <= days <= 70:
        return "bimonthly", 1 / 2
    if 80 <= days <= 100:
        return "quarterly", 1 / 3
    if 165 <= days <= 200:
        return "semiannual", 1 / 6
    if 330 <= days <= 400:
        return "annual", 1 / 12
    return "irregular", 0


def detect_recurring(payload: dict[str, Any]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for transaction in payload.get("transactions", []):
        if not transaction.get("eligible_spend"):
            continue
        groups[(
            transaction.get("account_id", "default"),
            transaction["merchant"],
            transaction.get("currency", "AUD"),
            transaction.get("liability_hint_hash") or "unverified",
        )].append(transaction)

    items: list[dict[str, Any]] = []
    for (account_id, merchant, currency, liability_hint_hash), transactions in groups.items():
        if len(transactions) < 2:
            continue
        ordered = sorted(transactions, key=lambda item: item["date"])
        dates = [datetime.fromisoformat(item["date"]).date() for item in ordered]
        intervals = [(later - earlier).days for earlier, later in zip(dates, dates[1:]) if (later - earlier).days > 0]
        if not intervals:
            continue
        median_interval = statistics.median(intervals)
        cadence, factor = cadence_for_days(median_interval)
        if cadence == "irregular":
            continue
        amounts = [float(item["amount"]) for item in ordered]
        median_amount = statistics.median(amounts)
        variation = (max(amounts) - min(amounts)) / median_amount if median_amount else 1
        liability_id = hashlib.sha256(
            f"{account_id}|{merchant}|{currency}|{liability_hint_hash}".encode()
        ).hexdigest()[:20]
        next_expected = dates[-1] + timedelta(days=round(median_interval))
        items.append({
            "liability_id": liability_id,
            "liability_identity_state": "source_bound" if liability_hint_hash != "unverified" else "merchant_group_unverified",
            "unique_liability_confirmed": liability_hint_hash != "unverified",
            "merchant": merchant,
            "account_id": account_id,
            "currency": currency,
            "cadence": cadence,
            "occurrences": len(ordered),
            "first_seen": ordered[0]["date"],
            "last_seen": ordered[-1]["date"],
            "next_expected": next_expected.isoformat(),
            "median_charge": round(median_amount, 2),
            "monthly_equivalent": round(median_amount * factor, 2),
            "amount_variation": round(variation, 4),
            "confidence": "high" if len(ordered) >= 3 and variation <= 0.15 else "medium",
            "transaction_ids": [item["transaction_id"] for item in ordered],
        })
    items.sort(key=lambda item: (-item["monthly_equivalent"], item["merchant"], item["account_id"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "recurring_items": items,
        "source_warnings": payload.get("warnings", []),
        "reconciliation": payload.get("reconciliation", {}),
    }


def assess_coverage(payload: dict[str, Any], declaration: dict[str, Any]) -> dict[str, Any]:
    declared = [str(item["account_id"]) for item in declaration.get("accounts", []) if item.get("account_id")]
    scope_confirmed = bool(declaration.get("scope_confirmed"))
    by_account: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in payload.get("transactions", []):
        by_account[str(transaction.get("account_id", "default"))].append(transaction)
    present = sorted(by_account)
    missing = sorted(set(declared) - set(present))
    unexpected = sorted(set(present) - set(declared))
    ambiguous_count = sum(1 for item in payload.get("transactions", []) if item.get("direction") == "unknown")
    unresolved_transfers = int(payload.get("reconciliation", {}).get("unresolved_transfer_count", 0))
    unresolved_duplicate_candidates = int(payload.get("reconciliation", {}).get("duplicate_candidate_count", 0))
    duplicate_sources = list(payload.get("duplicate_sources", []))
    source_manifests = list(payload.get("source_manifests", []))
    if payload.get("source_manifest"):
        source_manifests.append(payload["source_manifest"])
    source_content_hashes = sorted({
        manifest["source_content_hash"]
        for manifest in source_manifests
        if manifest.get("source_content_hash")
    })
    reconciliation_hash = payload.get("reconciliation_hash")

    account_coverage: list[dict[str, Any]] = []
    preliminary_complete = True
    exhaustive_by_history = True
    for account_id in declared:
        transactions = sorted(by_account.get(account_id, []), key=lambda item: item["date"])
        if not transactions:
            preliminary_complete = False
            exhaustive_by_history = False
            continue
        dates = [datetime.fromisoformat(item["date"]).date() for item in transactions]
        span_days = (dates[-1] - dates[0]).days + 1
        covered_calendar_months = len({(date.year, date.month) for date in dates})
        gaps = [(later - earlier).days for earlier, later in zip(dates, dates[1:])]
        max_gap = max(gaps, default=0)
        material_gap = max_gap > 45 and len(transactions) >= 3
        if span_days < 90 or material_gap:
            preliminary_complete = False
        if span_days < 365 or covered_calendar_months < 13:
            exhaustive_by_history = False
        account_coverage.append({
            "account_id": account_id,
            "first_date": dates[0].isoformat(),
            "last_date": dates[-1].isoformat(),
            "span_days": span_days,
            "covered_calendar_months": covered_calendar_months,
            "max_gap_days": max_gap,
            "material_gap": material_gap,
            "transaction_count": len(transactions),
        })

    blockers: list[str] = []
    if not scope_confirmed:
        blockers.append("scope_not_confirmed")
    if not declared:
        blockers.append("no_accounts_declared")
    if missing:
        blockers.append("declared_accounts_missing")
    if unexpected:
        blockers.append("undeclared_accounts_present")
    if ambiguous_count:
        blockers.append("ambiguous_transaction_direction")
    if unresolved_transfers:
        blockers.append("unresolved_cross_account_transfers")
    if unresolved_duplicate_candidates:
        blockers.append("unresolved_duplicate_candidates")
    if duplicate_sources:
        blockers.append("duplicate_sources")
    if not preliminary_complete:
        blockers.append("preliminary_history_incomplete")

    if blockers:
        state = "blocked"
    elif exhaustive_by_history or declaration.get("annual_evidence_complete"):
        state = "exhaustive_pass"
    else:
        state = "preliminary_pass"

    report = {
        "schema_version": SCHEMA_VERSION,
        "coverage_state": state,
        "scope_confirmed": scope_confirmed,
        "declared_accounts": declared,
        "present_accounts": present,
        "missing_accounts": missing,
        "unexpected_accounts": unexpected,
        "account_coverage": account_coverage,
        "ambiguous_direction_count": ambiguous_count,
        "unresolved_transfer_count": unresolved_transfers,
        "unresolved_duplicate_candidate_count": unresolved_duplicate_candidates,
        "duplicate_sources": duplicate_sources,
        "source_content_hashes": source_content_hashes,
        "reconciliation_hash": reconciliation_hash,
        "annual_evidence_complete": bool(declaration.get("annual_evidence_complete")),
        "blockers": blockers,
    }
    report["coverage_hash"] = content_hash(report)
    return report


def build_baseline(
    items_payload: dict[str, Any],
    coverage: dict[str, Any],
    currency: str = "AUD",
    protected_services: list[str] | None = None,
) -> dict[str, Any]:
    if coverage.get("coverage_state") not in PASSING_COVERAGE_STATES:
        raise ValueError("Coverage gate must pass before freezing a recurring-cost baseline")
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    total = 0.0
    protected_services = sorted({str(item).strip() for item in (protected_services or []) if str(item).strip()})
    protected_keys = {normalize_merchant(item) for item in protected_services}
    for item in items_payload.get("recurring_items", []):
        category = str(item.get("category", "subscription")).lower()
        identity_keys = {
            normalize_merchant(item.get("merchant", "")),
            normalize_merchant(item.get("provider", "")),
            str(item.get("liability_id", "")),
        }
        explicitly_protected = bool(item.get("protected", False) or protected_keys.intersection(identity_keys))
        in_scope = item.get("in_scope", True) and category not in EXCLUDED_CATEGORIES and not explicitly_protected
        if in_scope and item.get("currency", currency) == currency:
            included.append(item)
            total += float(item["monthly_equivalent"])
        else:
            reason = "protected" if explicitly_protected else ("out_of_scope" if not in_scope else "currency_unconverted")
            excluded.append({"liability_id": item.get("liability_id"), "merchant": item.get("merchant"), "reason": reason})
    total = round(total, 2)
    baseline = {
        "schema_version": SCHEMA_VERSION,
        "currency": currency,
        "coverage_state": coverage["coverage_state"],
        "coverage_hash": coverage["coverage_hash"],
        "protected_services": protected_services,
        "monthly_controllable_spend": total,
        "ten_percent_target": round(total * 0.10, 2),
        "included": included,
        "excluded": excluded,
    }
    baseline["baseline_hash"] = content_hash({
        "currency": currency,
        "coverage_hash": coverage["coverage_hash"],
        "protected_services": protected_services,
        "included": [
            {"liability_id": row.get("liability_id"), "monthly_equivalent": row.get("monthly_equivalent")}
            for row in included
        ],
    })
    return baseline


def calculate_net_savings(row: dict[str, Any]) -> dict[str, Any]:
    current = float(row.get("current_monthly_cost", 0))
    future = float(row.get("future_monthly_cost", 0))
    gross = max(0.0, (current - future) * 12)
    one_off = sum(float(row.get(key, 0) or 0) for key in (
        "exit_fees",
        "setup_costs",
        "lost_bundle_value_12m",
        "migration_costs",
    ))
    net = gross - one_off
    return {
        "gross_12_month_saving": round(gross, 2),
        "one_off_and_switching_costs": round(one_off, 2),
        "net_12_month_saving": round(net, 2),
        "net_monthly_equivalent": round(net / 12, 2),
    }


def merge_usage(opportunities: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    evidence_by_id = {str(key): value for key, value in evidence.items()}
    rows: list[dict[str, Any]] = []
    for row in opportunities.get("opportunities", opportunities.get("recurring_items", [])):
        merged = dict(row)
        key = str(row.get("liability_id") or normalize_merchant(row.get("merchant")))
        merged.update(evidence_by_id.get(key, {}))
        if "current_monthly_cost" in merged and "future_monthly_cost" in merged:
            merged.update(calculate_net_savings(merged))
        state = merged.get("usage_state", "unverified")
        allowed_states = {
            "owner_confirmed_unused",
            "underused",
            "over_tiered",
            "duplicated",
            "replacement_candidate",
            "verified_used",
        }
        merged["eligible"] = bool(
            not merged.get("protected", False)
            and state in allowed_states
            and merged.get("evidence_sufficient", False)
            and merged.get("unique_liability_confirmed", False)
            and float(merged.get("net_monthly_equivalent", 0)) > 0
        )
        rows.append(merged)
    return {"schema_version": SCHEMA_VERSION, "opportunities": rows}


def optimize(opportunities: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    target = float(baseline["ten_percent_target"])
    candidates = [
        row for row in opportunities.get("opportunities", [])
        if row.get("eligible") and not row.get("protected")
    ]
    candidates.sort(key=lambda row: (
        RISK_ORDER.get(row.get("risk", "high"), 9),
        -float(row.get("net_monthly_equivalent", row.get("monthly_reduction", 0))),
    ))
    selected: list[dict[str, Any]] = []
    total = 0.0
    for row in candidates:
        selected.append(row)
        total += float(row.get("net_monthly_equivalent", row.get("monthly_reduction", 0)))
        if total + 1e-9 >= target:
            break
    total = round(total, 2)
    baseline_monthly = float(baseline["monthly_controllable_spend"])
    return {
        "schema_version": SCHEMA_VERSION,
        "proof_state": "candidate",
        "baseline_hash": baseline.get("baseline_hash"),
        "baseline_monthly": baseline_monthly,
        "target_monthly": target,
        "selected": selected,
        "projected_net_monthly_saving": total,
        "projected_percent": round((total / baseline_monthly) * 100, 2) if baseline_monthly else 0,
        "target_met": total + 1e-9 >= target,
        "shortfall": round(max(0, target - total), 2),
    }


def canonical_hash(payload: dict[str, Any]) -> str:
    cleaned = dict(payload)
    cleaned.pop("batch_hash", None)
    return content_hash(cleaned)


def validate_and_freeze(
    payload: dict[str, Any],
    approval: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "liability_id",
        "provider",
        "account_id",
        "action",
        "current_plan",
        "target_plan",
        "current_monthly_cost",
        "future_monthly_cost",
        "net_monthly_equivalent",
        "currency",
        "renewal",
        "evidence_snapshot_id",
        "consequence",
        "recovery_path",
        "execution_gate",
        "risk",
    }
    if not payload.get("baseline_hash"):
        raise ValueError("baseline_hash is required")
    rows = payload.get("selected", payload.get("recommended_batch", []))
    if not rows:
        raise ValueError("At least one selected action is required")
    errors: list[str] = []
    frozen_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        row = dict(raw)
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")
            continue
        gross_monthly = float(row["current_monthly_cost"]) - float(row["future_monthly_cost"])
        if float(row["net_monthly_equivalent"]) > gross_monthly + 0.01:
            errors.append(f"row {index}: net saving exceeds gross price reduction")
        if float(row["net_monthly_equivalent"]) < 0:
            errors.append(f"row {index}: negative net saving")
        if row.get("annual_commitment"):
            errors.append(f"row {index}: annual commitment requires separate purchase approval")
        if row.get("risk") in {"high", "irreversible"}:
            row["item_level_confirmation_required"] = True
        row["idempotency_key"] = content_hash({
            "baseline_hash": payload["baseline_hash"],
            "liability_id": row["liability_id"],
            "account_id": row["account_id"],
            "action": row["action"],
            "target_plan": row["target_plan"],
        })[:24]
        frozen_rows.append(row)
    if errors:
        raise ValueError("; ".join(errors))

    frozen = dict(payload)
    frozen["selected"] = frozen_rows
    frozen["proof_state"] = "candidate"
    if approval:
        current = (now or utc_now()).astimezone(timezone.utc)
        frozen["proof_state"] = "approved"
        frozen["owner_approval"] = approval
        frozen["approved_at"] = iso_time(current)
        frozen["expires_at"] = iso_time(current + timedelta(hours=24))
    frozen["batch_hash"] = canonical_hash(frozen)
    return frozen


def validate_execution_preflight(
    frozen: dict[str, Any],
    live_items: list[dict[str, Any]],
    now: datetime | None = None,
    item_confirmations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if frozen.get("proof_state") != "approved":
        return {"ready": False, "status": "approval_required", "items": []}
    current = (now or utc_now()).astimezone(timezone.utc)
    expires_at = datetime.fromisoformat(frozen["expires_at"])
    if current > expires_at:
        return {"ready": False, "status": "expired_approval", "items": []}

    live_by_id = {str(item.get("liability_id")): item for item in live_items}
    compare_fields = (
        "provider",
        "account_id",
        "liability_id",
        "current_plan",
        "current_monthly_cost",
        "currency",
        "renewal",
    )
    confirmations = item_confirmations or {}
    results: list[dict[str, Any]] = []
    ready = True
    for approved in frozen.get("selected", []):
        live = live_by_id.get(str(approved["liability_id"]))
        if not live:
            results.append({"liability_id": approved["liability_id"], "ready": False, "changed_fields": ["missing_live_item"]})
            ready = False
            continue
        changed = [
            field
            for field in compare_fields
            if (field in approved or field in live) and approved.get(field) != live.get(field)
        ]
        if approved.get("item_level_confirmation_required"):
            confirmation = confirmations.get(str(approved["liability_id"]), {})
            confirmation_valid = False
            try:
                confirmed_at = datetime.fromisoformat(str(confirmation.get("confirmed_at", "")))
                approved_at = datetime.fromisoformat(frozen["approved_at"])
                confirmation_valid = bool(
                    confirmation.get("confirmation")
                    and confirmation.get("batch_hash") == frozen.get("batch_hash")
                    and confirmed_at.tzinfo is not None
                    and approved_at <= confirmed_at <= current <= expires_at
                )
            except (TypeError, ValueError):
                confirmation_valid = False
            if not confirmation_valid:
                changed.append("item_level_confirmation_required")
        item_ready = not changed and not live.get("already_completed", False)
        if live.get("already_completed", False):
            changed.append("already_completed")
        results.append({"liability_id": approved["liability_id"], "ready": item_ready, "changed_fields": changed})
        ready = ready and item_ready
    return {
        "ready": ready,
        "status": "ready" if ready else "stopped_material_change",
        "batch_hash": frozen.get("batch_hash"),
        "checked_at": iso_time(current),
        "items": results,
    }


def assess_execution_capabilities(capabilities: dict[str, Any]) -> dict[str, Any]:
    required = (
        "authenticated_browser",
        "live_account_readback",
        "before_after_capture",
        "interruptible_security_prompts",
        "durable_receipts",
    )
    missing = [name for name in required if not capabilities.get(name, False)]
    return {
        "mode": "guided_checklist" if missing else "autonomous_browser",
        "autonomous_execution_allowed": not missing,
        "missing_capabilities": missing,
    }


def _assert_secret_safe(payload: Any, path: str = "payload") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                raise ValueError(f"Secret-like field is not allowed in durable case events: {path}.{key}")
            _assert_secret_safe(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_secret_safe(value, f"{path}[{index}]")
    elif isinstance(payload, str):
        if any(pattern.search(payload) for pattern in SECRET_VALUE_PATTERNS):
            raise ValueError(f"Secret-like value is not allowed in durable case events: {path}")


class CaseStore:
    """Append-only hash-chained case state with deterministic replay."""

    def __init__(self, case_dir: Path, events: list[dict[str, Any]], snapshot: dict[str, Any]):
        self.case_dir = case_dir
        self.events_path = case_dir / "events.jsonl"
        self.snapshot_path = case_dir / "case.json"
        self.events = events
        self.snapshot = snapshot

    @classmethod
    def create(
        cls,
        root: str | Path,
        currency: str,
        protected_services: list[str],
        case_id: str | None = None,
        now: datetime | None = None,
    ) -> "CaseStore":
        root_path = Path(root).expanduser().resolve()
        root_path.mkdir(parents=True, exist_ok=True)
        try:
            root_path.chmod(0o700)
        except OSError:
            pass
        resolved_id = case_id or f"save10-{(now or utc_now()).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        case_dir = root_path / resolved_id
        case_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
        store = cls(case_dir, [], {})
        store._append("case_created", {
            "case_id": resolved_id,
            "currency": currency.upper(),
            "protected_services": protected_services,
            "schema_version": SCHEMA_VERSION,
        }, now=now)
        return store

    @classmethod
    def open(cls, case_dir: str | Path) -> "CaseStore":
        directory = Path(case_dir).expanduser().resolve()
        events_path = directory / "events.jsonl"
        events: list[dict[str, Any]] = []
        previous_hash = "GENESIS"
        for expected_sequence, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
            event = json.loads(line)
            if event.get("sequence") != expected_sequence:
                raise ValueError("Case event sequence is invalid")
            if event.get("prev_hash") != previous_hash:
                raise ValueError("Case event hash chain is broken")
            supplied_hash = event.get("event_hash")
            unhashed = dict(event)
            unhashed.pop("event_hash", None)
            if supplied_hash != content_hash(unhashed):
                raise ValueError("Case event content hash mismatch")
            previous_hash = supplied_hash
            events.append(event)
        snapshot = cls._replay(events)
        return cls(directory, events, snapshot)

    @staticmethod
    def _replay(events: list[dict[str, Any]]) -> dict[str, Any]:
        if not events or events[0].get("event_type") != "case_created":
            raise ValueError("Case must begin with case_created")
        created = events[0]["payload"]
        snapshot: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "case_id": created["case_id"],
            "currency": created["currency"],
            "protected_services": created.get("protected_services", []),
            "state": "intake",
            "answers": [],
            "artifacts": [],
            "approvals": [],
            "errors": [],
        }
        for event in events[1:]:
            kind = event["event_type"]
            payload = event["payload"]
            if kind == "state_transition":
                snapshot["state"] = payload["to_state"]
                snapshot["state_payload"] = payload.get("data", {})
            elif kind == "answer":
                snapshot["answers"].append(payload)
            elif kind == "artifact":
                snapshot["artifacts"].append(payload)
            elif kind == "approval":
                snapshot["approvals"].append(payload)
            elif kind == "error":
                snapshot["errors"].append(payload)
        snapshot["event_count"] = len(events)
        snapshot["last_event_hash"] = events[-1]["event_hash"]
        snapshot["updated_at"] = events[-1]["timestamp"]
        return snapshot

    def _append(self, event_type: str, payload: dict[str, Any], now: datetime | None = None) -> None:
        _assert_secret_safe(payload)
        event = {
            "sequence": len(self.events) + 1,
            "timestamp": iso_time(now),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": self.events[-1]["event_hash"] if self.events else "GENESIS",
        }
        event["event_hash"] = content_hash(event)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(event) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            self.events_path.chmod(0o600)
        except OSError:
            pass
        self.events.append(event)
        self.snapshot = self._replay(self.events)
        write_json(self.snapshot_path, self.snapshot)

    def transition(self, to_state: str, data: dict[str, Any], now: datetime | None = None) -> None:
        current = self.snapshot["state"]
        if to_state not in CASE_TRANSITIONS:
            raise ValueError(f"Unknown case state: {to_state}")
        if to_state not in CASE_TRANSITIONS.get(current, set()) and to_state not in EXCEPTION_STATES:
            raise ValueError(f"Invalid case transition: {current} -> {to_state}")
        self._append("state_transition", {"from_state": current, "to_state": to_state, "data": data}, now=now)

    def record(self, event_type: str, payload: dict[str, Any], now: datetime | None = None) -> None:
        if event_type not in {"answer", "artifact", "approval", "error"}:
            raise ValueError("Allowed record types: answer, artifact, approval, error")
        self._append(event_type, payload, now=now)
