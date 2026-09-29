"""
app/database/repository.py - every SQL statement of the service, one function each
==================================================================================
The other modules never write SQL themselves: they call these functions.
Always with ? placeholders - never paste text into SQL.

    Start-up   create_tables (from connection.py), sync_users, mark_interrupted_runs
    Users      get_user, active_users, record_sign_in
    Runs       rule_version_for, open_run (the one-run-per-month rule), set_output_folder,
               finish_run, fail_run
    Results    save_location (a location, its checks and its account lines in ONE transaction)
    Reading    get_run, recent_runs, last_run_per_month, run_locations, location, checks,
               failed_checks, account_lines, row_counts
    Audit      log, activity

Requirements covered: R9 (one run per month), R10 (every result kept), R11 (activity log)
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any, Iterable

from app.database.connection import create_tables, execute, now, query, query_one, transaction  # noqa: F401

ROLES = ("reviewer", "preparer", "admin")
ROLE_LEVEL = {"reviewer": 1, "preparer": 2, "admin": 3}   # a higher role can do everything a lower one can
RULE_FIELDS = ["cash_line_account", "replaced_account", "netted_prefix", "cancel_pair", "known_accounts",
               "tolerance"]
USER_JOIN = "LEFT JOIN users u ON u.user_name = r.requested_by"


def _field(item: Any, name: str) -> Any:
    """Read a value from a dict (item["debit"]) or from an object such as core's PivotLine (item.debit)."""
    return item[name] if isinstance(item, dict) else getattr(item, name)


def _text(value: Any) -> str | None:
    """Amounts are stored as exact text: Decimal('1197949.08') -> '1197949.08' (no rounding like float)."""
    return None if value is None else str(value)


# =============================================================================
# Start-up
# =============================================================================
def sync_users(users: Iterable[tuple[str, str, str]]) -> None:
    """Make the users table match config.USERS: add new people, update names and roles, switch off the rest."""
    users = list(users)
    if not users:
        raise ValueError("config.USERS is empty - add at least one user")
    for user_name, _, role in users:
        if role not in ROLES:
            raise ValueError(f"User {user_name}: role must be one of {', '.join(ROLES)} - not {role!r}")
    with transaction() as con:
        for user_name, display_name, role in users:
            con.execute("INSERT INTO users (user_name, display_name, role, active, added_at) VALUES (?, ?, ?, 1, ?) "
                        "ON CONFLICT (user_name) DO UPDATE SET display_name = excluded.display_name, "
                        "role = excluded.role, active = 1", (user_name.lower(), display_name, role, now()))
        keep = [u[0].lower() for u in users]
        con.execute(f"UPDATE users SET active = 0 WHERE user_name NOT IN ({','.join('?' * len(keep))})", keep)


def mark_interrupted_runs() -> int:
    """A run that was still 'running' when the service stopped can never finish: mark it failed. Returns how many."""
    return execute("UPDATE runs SET status = 'failed', finished_at = ?, "
                   "message = 'Stopped because the service was restarted - please run again.' "
                   "WHERE status IN ('queued', 'running')", (now(),))


# =============================================================================
# Users
# =============================================================================
def get_user(user_name: str | None) -> sqlite3.Row | None:
    """An active user, or None (unknown or switched off)."""
    if not user_name:
        return None
    return query_one("SELECT * FROM users WHERE user_name = ? AND active = 1", (user_name.strip().lower(),))


def active_users() -> list[sqlite3.Row]:
    return query("SELECT * FROM users WHERE active = 1 ORDER BY display_name")


def record_sign_in(user_name: str) -> None:
    with transaction() as con:
        con.execute("UPDATE users SET last_login_at = ? WHERE user_name = ?", (now(), user_name))
        con.execute("INSERT INTO activity_log (at, user_name, action) VALUES (?, ?, 'signed in')",
                    (now(), user_name))


# =============================================================================
# A run
# =============================================================================
def rule_version_for(rules: dict[str, str], user_name: str) -> int:
    """
    The SETTINGS of pivot_je.py as a row of rule_versions.
    The same rules give the same version number; changed rules add a new version.
    rules = {"cash_line_account": "11000", "replaced_account": "18300", "netted_prefix": "1000",
             "cancel_pair": "13000,50005", "known_accounts": "10005,11000,...", "tolerance": "0.01"}
    """
    missing = [f for f in RULE_FIELDS if f not in rules]
    if missing:
        raise ValueError(f"rules is missing: {', '.join(missing)}")
    values = [str(rules[f]) for f in RULE_FIELDS]
    with transaction(immediate=True) as con:
        same = con.execute("SELECT rule_version FROM rule_versions WHERE "
                           + " AND ".join(f"{f} = ?" for f in RULE_FIELDS), values).fetchone()
        if same:
            return same["rule_version"]
        version = con.execute("SELECT COALESCE(MAX(rule_version), 0) + 1 FROM rule_versions").fetchone()[0]
        con.execute(f"INSERT INTO rule_versions (rule_version, {', '.join(RULE_FIELDS)}, first_used_by, "
                    f"first_used_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (version, *values, user_name, now()))
        return version


def open_run(month_folder: str, user_name: str, dry_run: bool, rule_version: int | None,
             files_found: int) -> tuple[str | None, sqlite3.Row | None]:
    """
    The "one run per month folder at a time" rule, done safely:
    BEGIN IMMEDIATE locks the database for writing, so two clicks at the same moment are handled one
    after the other - the second one finds the first run and is refused.
    Returns (new run id, None) - or (None, the run that is already going).
    """
    with transaction(immediate=True) as con:
        busy = con.execute(f"SELECT r.*, u.display_name FROM runs r {USER_JOIN} "
                           "WHERE r.month_folder = ? AND r.status IN ('queued', 'running')",
                           (month_folder,)).fetchone()
        if busy:
            return None, busy
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
        con.execute("INSERT INTO runs (run_id, month_folder, dry_run, requested_by, status, requested_at, "
                    "started_at, files_found, rule_version) VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?)",
                    (run_id, month_folder, int(dry_run), user_name, now(), now(), files_found, rule_version))
        con.execute("INSERT INTO activity_log (at, user_name, action, run_id, details) VALUES (?, ?, ?, ?, ?)",
                    (now(), user_name, "run started", run_id, month_folder + (" (dry run)" if dry_run else "")))
        return run_id, None


def set_output_folder(run_id: str, folder: str | None) -> None:
    execute("UPDATE runs SET output_folder = ? WHERE run_id = ?", (folder, run_id))


def finish_run(run_id: str, counts: dict[str, int], message: str = "", master_file: str | None = None) -> None:
    """counts = {"OK": 70, "REVIEW": 4, "ERROR": 1, "MISSING": 0}"""
    execute("UPDATE runs SET status = 'done', finished_at = ?, ok_count = ?, review_count = ?, error_count = ?, "
            "missing_count = ?, master_file = ?, message = ? WHERE run_id = ?",
            (now(), counts.get("OK", 0), counts.get("REVIEW", 0), counts.get("ERROR", 0), counts.get("MISSING", 0),
             master_file, message, run_id))


def fail_run(run_id: str, message: str) -> None:
    execute("UPDATE runs SET status = 'failed', finished_at = ?, message = ? WHERE run_id = ?",
            (now(), message, run_id))


# =============================================================================
# The results of one location
# =============================================================================
def save_location(run_id: str, loc: dict[str, Any]) -> None:
    """
    One location: run_locations + check_results + account_lines in ONE transaction - all of it or nothing.

    loc is a dict with:
        location, status                          required (status OK / REVIEW / ERROR / MISSING)
        region, client, source_file, file_size, file_modified_at, file_sha256, format, line_count,
        file_debit, file_credit, summary_debit, summary_credit, leftover, workbook_file, error
                                                  optional (None when not known, e.g. for an ERROR)
        checks    list of {code, name, result, detail}           - or core's Check objects
        pivot     list of {account, debit, credit}               - or core's PivotLine objects
        summary   list of {account, kind, what, debit, credit}   - or core's SummaryLine objects
    """
    code = loc["location"]
    get = loc.get
    with transaction() as con:
        con.execute("INSERT INTO run_locations (run_id, location_code, region, client, source_file, file_size, "
                    "file_modified_at, file_sha256, format, line_count, file_debit, file_credit, summary_debit, "
                    "summary_credit, leftover_to_11000, status, workbook_file, error) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, code, get("region"), get("client"), get("source_file"), get("file_size"),
                     get("file_modified_at"), get("file_sha256"), get("format"), get("line_count"),
                     _text(get("file_debit")), _text(get("file_credit")), _text(get("summary_debit")),
                     _text(get("summary_credit")), _text(get("leftover")), loc["status"], get("workbook_file"),
                     get("error")))
        con.executemany("INSERT INTO check_results (run_id, location_code, check_code, check_name, result, detail) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        [(run_id, code, _field(c, "code"), _field(c, "name"), _field(c, "result"), _field(c, "detail"))
                         for c in get("checks") or []])
        con.executemany("INSERT INTO account_lines (run_id, location_code, stage, line_no, account, line_type, "
                        "description, debit, credit) VALUES (?, ?, 'PIVOT', ?, ?, NULL, NULL, ?, ?)",
                        [(run_id, code, i, _field(p, "account"), _text(_field(p, "debit")), _text(_field(p, "credit")))
                         for i, p in enumerate(get("pivot") or [], start=1)])
        con.executemany("INSERT INTO account_lines (run_id, location_code, stage, line_no, account, line_type, "
                        "description, debit, credit) VALUES (?, ?, 'SUMMARY', ?, ?, ?, ?, ?, ?)",
                        [(run_id, code, i, _field(s, "account"), _field(s, "kind"), _field(s, "what"),
                          _text(_field(s, "debit")), _text(_field(s, "credit")))
                         for i, s in enumerate(get("summary") or [], start=1)])


# =============================================================================
# Reading back (for the pages, the API and the master file)
# =============================================================================
def get_run(run_id: str) -> sqlite3.Row | None:
    return query_one(f"SELECT r.*, u.display_name FROM runs r {USER_JOIN} WHERE r.run_id = ?", (run_id,))


def recent_runs(limit: int = 50) -> list[sqlite3.Row]:
    return query(f"SELECT r.*, u.display_name FROM runs r {USER_JOIN} "
                 "ORDER BY r.requested_at DESC, r.rowid DESC LIMIT ?", (limit,))


def last_run_per_month() -> dict[str, sqlite3.Row]:
    """month folder -> its newest run (for the dashboard)."""
    last: dict[str, sqlite3.Row] = {}
    for row in recent_runs(500):
        last.setdefault(row["month_folder"], row)            # the list is newest first
    return last


def run_locations(run_id: str) -> list[sqlite3.Row]:
    return query("SELECT * FROM run_locations WHERE run_id = ? ORDER BY region, client, location_code", (run_id,))


def location(run_id: str, code: str) -> sqlite3.Row | None:
    return query_one("SELECT * FROM run_locations WHERE run_id = ? AND location_code = ?", (run_id, code))


def checks(run_id: str, code: str) -> list[sqlite3.Row]:
    return query("SELECT * FROM check_results WHERE run_id = ? AND location_code = ? ORDER BY rowid", (run_id, code))


def failed_checks(run_id: str) -> dict[str, list[str]]:
    """location code -> the details of its failed checks (for the Issues column)."""
    out: dict[str, list[str]] = {}
    for row in query("SELECT location_code, check_name, detail FROM check_results "
                     "WHERE run_id = ? AND result = 'FAIL' ORDER BY rowid", (run_id,)):
        out.setdefault(row["location_code"], []).append(f"{row['check_name']}: {row['detail']}")
    return out


def account_lines(run_id: str, code: str | None = None, stage: str | None = None) -> list[sqlite3.Row]:
    """The pivot (stage PIVOT) and / or the Summary JE (stage SUMMARY) lines, in their original order."""
    sql, params = "SELECT * FROM account_lines WHERE run_id = ?", [run_id]
    if code is not None:
        sql, params = sql + " AND location_code = ?", params + [code]
    if stage is not None:
        sql, params = sql + " AND stage = ?", params + [stage]
    return query(sql + " ORDER BY location_code, stage, line_no", params)


def row_counts(run_id: str) -> dict[str, int]:
    """How many rows a run has in each result table (for checks and tests)."""
    return {t: query_one(f"SELECT COUNT(*) AS n FROM {t} WHERE run_id = ?", (run_id,))["n"]
            for t in ("run_locations", "check_results", "account_lines")}


# =============================================================================
# The activity log
# =============================================================================
def log(user_name: str | None, action: str, run_id: str | None = None, details: str = "") -> None:
    execute("INSERT INTO activity_log (at, user_name, action, run_id, details) VALUES (?, ?, ?, ?, ?)",
            (now(), user_name, action, run_id, details))


def activity(limit: int = 200) -> list[sqlite3.Row]:
    return query("SELECT a.*, u.display_name FROM activity_log a LEFT JOIN users u ON u.user_name = a.user_name "
                 "ORDER BY a.log_id DESC LIMIT ?", (limit,))

