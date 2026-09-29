    The 7 tables (Solution Design Document, section 6):
    users          the 4 people who may use the service and their role
    rule_versions  the SETTINGS of pivot_je.py used by a run - a change adds a new version
    runs           one row per click on Run: who, when, which month, the counts, the master file
    run_locations  one row per location in a run: totals, status, file fingerprint, Excel file
    check_results  one row per check per location (C1 ... C5, DATA)
    account_lines  the pivot (PIVOT) and the Summary JE (SUMMARY) lines of every location
    activity_log   who did what and when: sign-ins, runs, downloads

One short connection per call: a SQLite connection belongs to the thread that opened it, and the web
server uses many threads.

Requirement covered: R10
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_name      TEXT PRIMARY KEY,               -- Windows user name, e.g. preparer.one
    display_name   TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('admin', 'preparer', 'reviewer')),
    active         INTEGER NOT NULL DEFAULT 1,
    added_at       TEXT,
    last_login_at  TEXT
);
CREATE TABLE IF NOT EXISTS rule_versions (
    rule_version       INTEGER PRIMARY KEY,        -- 1, 2, 3 ... a change adds a new row
    cash_line_account  TEXT NOT NULL,              -- 11000
    replaced_account   TEXT NOT NULL,              -- 18300
    netted_prefix      TEXT NOT NULL,              -- "1000" (today only 10005)
    cancel_pair        TEXT NOT NULL,              -- "13000,50005"
    known_accounts     TEXT NOT NULL,              -- comma separated
    tolerance          TEXT NOT NULL,              -- "0.01"
    first_used_by      TEXT,
    first_used_at      TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    run_id         TEXT PRIMARY KEY,               -- e.g. 20260928-101500-ab12
    month_folder   TEXT NOT NULL,                  -- e.g. August 2026
    dry_run        INTEGER NOT NULL DEFAULT 0,     -- 1 = checks only, no Excel files kept
    requested_by   TEXT NOT NULL REFERENCES users (user_name),
    status         TEXT NOT NULL CHECK (status IN ('queued', 'running', 'done', 'failed')),
    requested_at   TEXT NOT NULL,
    started_at     TEXT,
    finished_at    TEXT,
    files_found    INTEGER,                        -- Journal Entry files in the month folder
    ok_count       INTEGER,
    review_count   INTEGER,
    error_count    INTEGER,
    missing_count  INTEGER,                        -- folders with exports but no Journal Entry file (C6)
    output_folder  TEXT,
    master_file    TEXT,
    message        TEXT,
    rule_version   INTEGER REFERENCES rule_versions (rule_version)
);
CREATE INDEX IF NOT EXISTS runs_by_month ON runs (month_folder, status);
CREATE TABLE IF NOT EXISTS run_locations (
    run_id             TEXT NOT NULL REFERENCES runs (run_id),
    location_code      TEXT NOT NULL,              -- e.g. 7003
    region             TEXT,
    client             TEXT,
    source_file        TEXT,                       -- the Journal Entry file that was read
    file_size          INTEGER,                    -- size + modified time + SHA-256 = the file fingerprint
    file_modified_at   TEXT,
    file_sha256        TEXT,
    format             TEXT,                       -- 1 = Amount only, 2 = Debit/Credit given
    line_count         INTEGER,
    file_debit         TEXT,                       -- amounts are stored as exact text, e.g. '1197949.08'
    file_credit        TEXT,
    summary_debit      TEXT,
    summary_credit     TEXT,
    leftover_to_11000  TEXT,
    status             TEXT NOT NULL CHECK (status IN ('OK', 'REVIEW', 'ERROR', 'MISSING')),
    workbook_file      TEXT,
    error              TEXT,
    PRIMARY KEY (run_id, location_code)
);
CREATE TABLE IF NOT EXISTS check_results (
    run_id         TEXT NOT NULL,
    location_code  TEXT NOT NULL,
    check_code     TEXT NOT NULL,                  -- C1 ... C5, DATA, READ
    check_name     TEXT,
    result         TEXT NOT NULL CHECK (result IN ('PASS', 'FAIL', 'N/A')),
    detail         TEXT,
    FOREIGN KEY (run_id, location_code) REFERENCES run_locations (run_id, location_code)
);
CREATE INDEX IF NOT EXISTS checks_by_location ON check_results (run_id, location_code);
CREATE TABLE IF NOT EXISTS account_lines (
    run_id         TEXT NOT NULL,
    location_code  TEXT NOT NULL,
    stage          TEXT NOT NULL CHECK (stage IN ('PIVOT', 'SUMMARY')),   -- before / after the adjustments
    line_no        INTEGER NOT NULL,
    account        TEXT NOT NULL,
    line_type      TEXT,                           -- as_is / cash_line (Summary JE lines only)
    description    TEXT,
    debit          TEXT NOT NULL,
    credit         TEXT NOT NULL,
    FOREIGN KEY (run_id, location_code) REFERENCES run_locations (run_id, location_code)
);
CREATE INDEX IF NOT EXISTS lines_by_location ON account_lines (run_id, location_code, stage, line_no);
CREATE TABLE IF NOT EXISTS activity_log (
    log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    at         TEXT NOT NULL,
    user_name  TEXT,
    action     TEXT NOT NULL,                      -- signed in / run started / downloaded ...
    run_id     TEXT,
    details    TEXT
);
"""

TABLES = ["users", "rule_versions", "runs", "run_locations", "check_results", "account_lines", "activity_log"]


def now() -> str:
    """The time as text, e.g. '2026-09-29 10:15:00' - how every date is stored."""
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def connect() -> sqlite3.Connection:
    """
    Open the database file (made the first time).
    isolation_level=None: nothing is held back - we write BEGIN / COMMIT ourselves (see transaction()),
    so we decide what belongs together.
    """
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(config.DB_PATH, timeout=30, isolation_level=None)
    con.execute("PRAGMA foreign_keys = ON")          # a run must belong to a real user, and so on
    con.execute("PRAGMA journal_mode = WAL")         # the pages can read while a run is writing
    con.row_factory = sqlite3.Row                   # rows work like dictionaries: row["status"]
    return con


@contextmanager
def transaction(immediate: bool = False) -> Iterator[sqlite3.Connection]:
    """
    Everything inside the "with" block is saved together - or, on any error, not at all:

        with transaction() as con:
            con.execute("INSERT ...")
            con.execute("INSERT ...")

    immediate=True locks the database for writing at the start (BEGIN IMMEDIATE), so two people clicking
    Run at the same moment are handled one after the other.
    """
    con = connect()
    try:
        con.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        yield con
        con.execute("COMMIT")
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")                  # nothing half-saved
        raise
    finally:
        con.close()


def query(sql: str, params: tuple | list = ()) -> list[sqlite3.Row]:
    """Read rows. The ? in the SQL are filled with params - never paste text into SQL yourself."""
    con = connect()
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


def query_one(sql: str, params: tuple | list = ()) -> sqlite3.Row | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple | list = ()) -> int:
    """Change rows, saved at once. Returns how many rows were changed."""
    con = connect()
    try:
        return con.execute(sql, params).rowcount
    finally:
        con.close()


def create_tables() -> None:
    """Create the 7 tables if they are not there yet - safe to call every time the service starts."""
    con = connect()
    try:
        con.executescript(SCHEMA)
    finally:
        con.close()

