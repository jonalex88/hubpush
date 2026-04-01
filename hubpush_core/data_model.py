from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

SYNC_COLUMNS = [
    "HubSpot Status",
    "HubSpot Contact ID",
    "HubSpot Company ID",
    "HubSpot Deal ID",
    "Last Push Timestamp",
    "Last Push Commit ID",
    "Last Push Message",
    "Cloud Row ID",
    "Row Checksum",
    "Cloud Updated At",
]

STATUS_NOT_READY = "Not Ready"
STATUS_WAITING_FOR_DOCUMENTS = "Waiting For Documents"
STATUS_READY_TO_PUSH = "Ready To Push"
STATUS_PUSHED = "Pushed"
STATUS_PUSH_FAILED = "Push Failed"
STATUS_UNDONE = "Undone"

ALLOWED_STATUSES = {
    STATUS_NOT_READY,
    STATUS_WAITING_FOR_DOCUMENTS,
    STATUS_READY_TO_PUSH,
    STATUS_PUSHED,
    STATUS_PUSH_FAILED,
    STATUS_UNDONE,
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def build_cloud_row_id(row: dict[str, Any]) -> str:
    # Deterministic ID used across Excel and cloud to avoid drift.
    parts = [
        normalize_text(row.get("source subfolder", "")).lower(),
        normalize_text(row.get("company reg name", "")).lower(),
        normalize_text(row.get("company registration number", "")).lower(),
        normalize_text(row.get("primary franchisee email address", "")).lower(),
        normalize_text(row.get("FIS Number", "")).lower(),
        normalize_text(row.get("Restaurant Name", "")).lower(),
        normalize_text(row.get("Email Address", "")).lower(),
        normalize_text(row.get("Contact Email", "")).lower(),
    ]
    seed = "|".join(parts)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()


def default_hubspot_status(row: dict[str, Any]) -> str:
    mandate = normalize_text(row.get("debit order mandate validation result", "")).upper()
    bank = normalize_text(row.get("bank account proof validation", "")).upper()
    if mandate == "PASS" and bank == "PASS":
        return STATUS_READY_TO_PUSH
    if mandate == "FAIL" or bank == "FAIL":
        return STATUS_WAITING_FOR_DOCUMENTS
    return STATUS_NOT_READY


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_row_payload(row: dict[str, Any]) -> dict[str, Any]:
    ignored = {
        "Row Checksum",
        "Cloud Updated At",
    }
    payload = {k: row.get(k, "") for k in sorted(row) if k not in ignored}
    return payload


def compute_row_checksum(row: dict[str, Any]) -> str:
    payload = canonical_row_payload(row)
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
