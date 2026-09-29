"""
app/engine/core.py - the core logic: the pivot table and the Summary JE of one Journal Entry file
==================================================================================================
All the calculation is done by the tested functions in pivot_je.py (in this folder, NOT changed):

    STEP 1  read_file          read the CSV / Excel file, every value as text
    STEP 2  fill_debit_credit  Debit / Credit from the Amount (Format 1), or as given (Format 2)
    STEP 3  build_pivot        the pivot table: Rows = Account, Sum of Debit, Sum of Credit
    STEP 4  build_summary      the adjustments -> the Summary JE
    STEP 5  run_checks         checks C1 ... C5 and the data checks -> status OK or REVIEW

This module runs those steps for one file and hands back ONE result object with plain, typed data:
no printing, no Excel file, no database. The other modules (database, Excel files, runner, API, pages)
only work with this result.

How to use it:
    from app.engine import core
    result = core.build_result(Path("tests/fixtures/7003-Export_JournalEntry.csv"))
    result.pivot_debit       -> Decimal("1197949.08")      the pivot's Grand Total (Debit)
    result.summary_debit     -> Decimal("733846.98")       the Summary JE total (Debit)
    result.status            -> "OK"

A file that cannot be read (for example: no Account column) raises an exception. The caller - the
runner - catches it and marks that location ERROR, so one bad file never stops a run.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.engine import pivot_je

ZERO = pivot_je.ZERO


# =============================================================================
# The result - plain data the rest of the service can use
# =============================================================================
@dataclass(frozen=True)
class PivotLine:
    """One row of the pivot table (the Excel PivotTable step)."""
    account: str
    debit: Decimal
    credit: Decimal

    @property
    def net(self) -> Decimal:
        return self.debit - self.credit


@dataclass(frozen=True)
class SummaryLine:
    """One line of the Summary JE (after the adjustments)."""
    account: str
    kind: str                 # "cash_line" = the second 11000 line (18300 + netted accounts + 13000/50005
                              # difference), "as_is" = every other line
    what: str                 # the explanation, e.g. "18300 posted as 11000, 10005 netted"
    debit: Decimal
    credit: Decimal

    @property
    def net(self) -> Decimal:
        return self.debit - self.credit


@dataclass(frozen=True)
class Check:
    """One check of the file."""
    code: str                 # C1 ... C5, or DATA for a line that could not be used
    name: str                 # e.g. "Pivot balances (Grand Total Debit = Credit)"
    result: str               # PASS / FAIL / N/A
    detail: str               # e.g. "difference 0.00"


@dataclass(frozen=True)
class CoreResult:
    """Everything the core logic works out for one Journal Entry file."""
    source: Path              # the file that was read
    location: str             # e.g. 7003 - from the Location column, otherwise from the file name
    format: str               # "1" = Amount only, "2" = Debit/Credit given in the file
    line_count: int           # lines in the file
    pivot: list[PivotLine]
    summary: list[SummaryLine]
    leftover: Decimal         # the 13000/50005 difference: > 0 extra Debit, < 0 extra Credit
    netted: list[str]         # the accounts netted into the cash line (today 10005)
    checks: list[Check]
    problems: list[str]       # lines left out, e.g. "Row 3: Amount is not a number ('abc') - line left out"
    status: str               # OK = every check passed and nothing to look at, otherwise REVIEW
    # the objects pivot_je.write_excel() needs to write the location workbook later (Excel module)
    excel_parts: dict[str, Any] = field(repr=False, compare=False, default_factory=dict)

    @property
    def pivot_debit(self) -> Decimal:
        """The pivot's Grand Total, Debit side."""
        return sum((p.debit for p in self.pivot), ZERO)

    @property
    def pivot_credit(self) -> Decimal:
        return sum((p.credit for p in self.pivot), ZERO)

    @property
    def summary_debit(self) -> Decimal:
        """The Summary JE total, Debit side."""
        return sum((s.debit for s in self.summary), ZERO)

    @property
    def summary_credit(self) -> Decimal:
        return sum((s.credit for s in self.summary), ZERO)

    @property
    def cash_line(self) -> SummaryLine | None:
        """The second 11000 line, where 18300, the netted accounts and the 13000/50005 difference end up."""
        return next((s for s in self.summary if s.kind == "cash_line"), None)


# =============================================================================
# The core logic
# =============================================================================
def build_result(path: Path) -> CoreResult:
    """Read one Journal Entry file and work out its pivot table, Summary JE, checks and status."""
    path = Path(path)
    raw = pivot_je.read_file(path)                                            # STEP 1
    data, lines, fmt, problems = pivot_je.fill_debit_credit(raw)              # STEP 2
    pivot = pivot_je.build_pivot(lines)                                       # STEP 3
    summary, leftover, netted = pivot_je.build_summary(pivot)                 # STEP 4
    check_lines, status = pivot_je.run_checks(pivot, summary, leftover, problems)   # STEP 5

    return CoreResult(
        source=path,
        location=location_of(raw, path),
        format=fmt,
        line_count=len(raw),
        pivot=[PivotLine(a, pivot.at[a, "Debit"], pivot.at[a, "Credit"]) for a in pivot.index],
        summary=[SummaryLine(s["account"], s["kind"], s["what"], s["debit"], s["credit"]) for s in summary],
        leftover=leftover,
        netted=list(netted),
        checks=checks_from(check_lines, fmt, raw),
        problems=list(problems),
        status=status,
        excel_parts={"data": data, "pivot": pivot, "summary": summary, "netted": netted},
    )


def location_of(raw, path: Path) -> str:
    """
    The location code - the same rule as pivot_je.process_file():
    the most common value of the Location / LOCATION_ID column, otherwise the number at the start
    of the file name (7003-Export_JournalEntry.csv -> 7003).
    """
    column = pivot_je.find_column(raw, "Location", "LOCATION_ID")
    values = [v.strip() for v in raw[column]] if column else []
    values = [v for v in values if v]
    if values:
        return max(set(values), key=values.count)
    match = re.match(r"(\d+)", path.stem)
    return match.group(1) if match else path.stem


CHECK_CODES = [("Pivot balances", "C1"), ("Summary JE balances", "C4"), ("cancel out", "C3"),
               ("No new accounts", "C5"), ("line credit not negative", "DATA")]


def checks_from(check_lines: list[str], fmt: str, raw) -> list[Check]:
    """
    pivot_je.run_checks() gives printable lines, for example
        '  OK     Pivot balances (Grand Total Debit = Credit): difference 0.00'
        '  CHECK  Row 3: Amount is not a number ('abc') - line left out'
    Each line becomes one Check. C2 (do Debit/Credit columns already in the file agree with the Amount?)
    is added here, because pivot_je only prints a line for it when they do not agree.
    """
    checks, mismatch = [], None
    for line in check_lines:
        text = line.strip()
        ok = text.startswith("OK")
        text = text[2:].strip() if ok else text[5:].strip()          # remove the "OK" / "CHECK" word
        code = next((c for key, c in CHECK_CODES if key in text), None)
        if code is None:
            if "differ from the Amount" in text:                   # belongs to C2 below
                mismatch = text
            else:                                                  # a line that could not be used
                checks.append(Check("DATA", "Line left out", "FAIL", text))
            continue
        name, _, detail = text.partition(": ")
        checks.append(Check(code, name, "PASS" if ok else "FAIL", detail))

    if fmt == "2":
        c2 = ("N/A", "Debit/Credit given in the file")
    elif mismatch:
        c2 = ("FAIL", mismatch)
    elif pivot_je.find_column(raw, "Debit") is not None and pivot_je.find_column(raw, "Credit") is not None:
        c2 = ("PASS", "all lines match the Amount")
    else:
        c2 = ("N/A", "Debit/Credit filled from Amount")
    checks.append(Check("C2", "Debit / Credit match the file", *c2))
    return sorted(checks, key=lambda c: (c.code == "DATA", c.code))  # C1 ... C5, then DATA
