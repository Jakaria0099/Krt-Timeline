"""
data_layer.py — handles all persistence

Tries Google Sheets first (when configured via st.secrets).
Falls back to local timeline_data.json if not configured or sheet I/O fails.

Storage model:
  Sheet has TWO worksheets:
    branches:   id | person | task_title | color
    events:     id | branch_id | date | form | priority | title |
                description | sharepoint_url | sharepoint_label | time_taken
  Writes are full-replace (last-write-wins). Acceptable for small teams; users
  should "Pull" before they "Push" if multiple people are editing.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional, Tuple

import streamlit as st

DATA_FILE = "timeline_data.json"
BRANCHES_WS = "branches"
EVENTS_WS = "events"

BRANCH_HEADERS = ["id", "person", "task_title", "color"]
EVENT_HEADERS = [
    "id", "branch_id", "date", "form", "priority", "title",
    "description", "sharepoint_url", "sharepoint_label", "time_taken",
]

# ── Configuration check ──────────────────────────────────────────────────────
def has_gsheet_config() -> bool:
    """True if Google Sheets credentials are present in st.secrets."""
    try:
        if "gcp_service_account" not in st.secrets:
            return False
        if "gsheet" not in st.secrets:
            return False
        if "spreadsheet_url" not in st.secrets["gsheet"]:
            return False
        return True
    except Exception:
        return False


# ── gspread client (cached as resource) ──────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_client_and_sheet():
    """Authenticate and return (client, spreadsheet) — cached for the session."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet_url = st.secrets["gsheet"]["spreadsheet_url"]
    spreadsheet = client.open_by_url(spreadsheet_url)
    return client, spreadsheet


def _ensure_worksheets(spreadsheet) -> None:
    """Create branches/events worksheets with headers if missing."""
    existing = {ws.title for ws in spreadsheet.worksheets()}
    if BRANCHES_WS not in existing:
        ws = spreadsheet.add_worksheet(title=BRANCHES_WS, rows=200, cols=len(BRANCH_HEADERS))
        ws.append_row(BRANCH_HEADERS)
    if EVENTS_WS not in existing:
        ws = spreadsheet.add_worksheet(title=EVENTS_WS, rows=2000, cols=len(EVENT_HEADERS))
        ws.append_row(EVENT_HEADERS)


# ── Read from sheet (cached, with TTL) ──────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _read_from_sheet() -> dict:
    """Read both worksheets, assemble {branches: [...]} structure."""
    _, spreadsheet = _get_client_and_sheet()
    _ensure_worksheets(spreadsheet)

    branches_ws = spreadsheet.worksheet(BRANCHES_WS)
    events_ws = spreadsheet.worksheet(EVENTS_WS)

    branches_records = branches_ws.get_all_records(expected_headers=BRANCH_HEADERS)
    events_records = events_ws.get_all_records(expected_headers=EVENT_HEADERS)

    # Group events by branch_id
    events_by_branch: dict[str, list] = {}
    for ev in events_records:
        bid = str(ev.get("branch_id", "")).strip()
        eid = str(ev.get("id", "")).strip()
        if not bid or not eid:
            continue
        events_by_branch.setdefault(bid, []).append({
            "id": eid,
            "date": str(ev.get("date", "")).strip(),
            "form": str(ev.get("form", "")).strip(),
            "priority": str(ev.get("priority", "")).strip(),
            "title": str(ev.get("title", "")).strip(),
            "description": str(ev.get("description", "")).strip(),
            "sharepoint_url": str(ev.get("sharepoint_url", "")).strip(),
            "sharepoint_label": str(ev.get("sharepoint_label", "")).strip(),
            "time_taken": str(ev.get("time_taken", "")).strip(),
        })

    branches: list = []
    for b in branches_records:
        bid = str(b.get("id", "")).strip()
        if not bid:
            continue
        branches.append({
            "id": bid,
            "person": str(b.get("person", "")).strip(),
            "task_title": str(b.get("task_title", "")).strip(),
            "color": str(b.get("color", "#5b8dee")).strip() or "#5b8dee",
            "events": sorted(events_by_branch.get(bid, []), key=lambda e: e["date"]),
        })

    return {"branches": branches}


# ── Write to sheet (full replace) ────────────────────────────────────────────
def _write_to_sheet(data: dict) -> None:
    """Replace all rows in branches and events worksheets."""
    _, spreadsheet = _get_client_and_sheet()
    _ensure_worksheets(spreadsheet)

    branches_ws = spreadsheet.worksheet(BRANCHES_WS)
    events_ws = spreadsheet.worksheet(EVENTS_WS)

    branches_rows: list = [BRANCH_HEADERS[:]]
    events_rows: list = [EVENT_HEADERS[:]]

    for b in data.get("branches", []):
        branches_rows.append([
            str(b.get("id", "")),
            str(b.get("person", "")),
            str(b.get("task_title", "")),
            str(b.get("color", "")),
        ])
        for ev in b.get("events", []):
            events_rows.append([
                str(ev.get("id", "")),
                str(b.get("id", "")),
                str(ev.get("date", "")),
                str(ev.get("form", "")),
                str(ev.get("priority", "")),
                str(ev.get("title", "")),
                str(ev.get("description", "")),
                str(ev.get("sharepoint_url", "")),
                str(ev.get("sharepoint_label", "")),
                str(ev.get("time_taken", "")),
            ])

    # Clear and rewrite. value_input_option='RAW' avoids gspread interpreting
    # strings as formulas (e.g. dates starting with '=').
    branches_ws.clear()
    if branches_rows:
        branches_ws.update(values=branches_rows, range_name="A1", value_input_option="RAW")
    events_ws.clear()
    if events_rows:
        events_ws.update(values=events_rows, range_name="A1", value_input_option="RAW")


# ── Local file fallback ──────────────────────────────────────────────────────
def _read_from_file() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"branches": []}


def _write_to_file(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Public API ───────────────────────────────────────────────────────────────
def load_data() -> Tuple[dict, str, Optional[str]]:
    """
    Returns (data, source, error_msg).
      source: "sheet" | "file"
      error_msg: human-readable error (if anything failed gracefully)
    """
    if has_gsheet_config():
        try:
            return _read_from_sheet(), "sheet", None
        except Exception as e:
            return _read_from_file(), "file", f"Could not read from Google Sheet: {e}"
    return _read_from_file(), "file", None


def save_data(data: dict) -> Tuple[str, Optional[str]]:
    """
    Returns (destination, error_msg).
      destination: "sheet" | "file"
    Always writes to local file as a backup. Tries sheet if configured.
    """
    # Always update local file as backup
    try:
        _write_to_file(data)
    except Exception:
        pass

    if has_gsheet_config():
        try:
            _write_to_sheet(data)
            # Invalidate read cache so next load reflects the new state
            _read_from_sheet.clear()
            return "sheet", None
        except Exception as e:
            return "file", f"Could not write to Google Sheet (saved locally): {e}"

    return "file", None


def force_refresh() -> None:
    """Clear all caches so next load_data hits the sheet."""
    try:
        _read_from_sheet.clear()
    except Exception:
        pass
