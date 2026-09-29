"""
tests/test_core.py - the core logic in detail
=============================================
Run it from the project folder:   python -m tests.test_core
(With pytest installed, "python -m pytest" runs every test file.)

Each test builds a small Journal Entry file (or uses the two samples in tests/fixtures) and checks the
pivot table, the Summary JE, the checks and the status that core.build_result() hands back.
"""
import contextlib
import io
import tempfile
from decimal import Decimal
from pathlib import Path

from app.engine import core, pivot_je

FIXTURES = Path(__file__).resolve().parent / "fixtures"
D = Decimal

def make_file(folder: Path, name: str, rows: list[str]) -> Path:
    """Write a small Format 1 Journal Entry file: Location, Account, Amount."""
    path = folder / name
    path.write_text("Location,Account,Amount\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path

def lines_of(result) -> list[tuple]:
    return [(s.account, s.kind, s.debit, s.credit) for s in result.summary]

def test_7003_format_1():
    r = core.build_result(FIXTURES / "7003-Export_JournalEntry.csv")
    assert (r.location, r.format, r.line_count, r.status) == ("7003", "1", 58, "OK")
    assert len(r.pivot) == 11 and r.pivot[0].account == "10005"          # accounts in number order
    assert r.pivot_debit == r.pivot_credit == D("1197949.08")
    assert r.netted == ["10005"] and r.leftover == D("0.00")
    assert r.cash_line.debit == D("346058.49") and r.cash_line.credit == D("0.00")
    assert r.summary_debit == r.summary_credit == D("733846.98")
    assert [s.account for s in r.summary] == ["11000", "11000", "21110", "40000", "40005", "40010", "40015", "65115"]
    assert "13000" not in [s.account for s in r.summary]                 # 13000 and 50005 cancel out
    assert {c.code: c.result for c in r.checks} == {"C1": "PASS", "C2": "N/A", "C3": "PASS", "C4": "PASS", "C5": "PASS"}

def test_44105_format_2():
    r = core.build_result(FIXTURES / "44105-Export_JournalEntry.csv")
    assert (r.location, r.format, r.status) == ("44105", "2", "OK")
    assert r.pivot_debit == r.pivot_credit == D("347893.47")
    assert r.cash_line.debit == D("106773.63") and r.cash_line.credit == D("3000.00")
    assert r.summary_debit == r.summary_credit == D("216073.21")
    assert next(c for c in r.checks if c.code == "C2").result == "N/A"   # Debit/Credit given in the file

def test_same_answer_as_process_file():
    """core.build_result() and the tested pivot_je.process_file() agree on location, lines, totals and status."""
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("7003-Export_JournalEntry.csv", "44105-Export_JournalEntry.csv"):
            with contextlib.redirect_stdout(io.StringIO()):               # process_file prints its tables
                info = pivot_je.process_file(FIXTURES / name, Path(tmp), set())
            r = core.build_result(FIXTURES / name)
            assert (r.location, r.format, r.line_count, r.status) == (info["location"], info["format"], info["lines"], info["status"])
            assert (r.pivot_debit, r.summary_debit) == (info["pivot"], info["summary"])

def test_leftover_on_the_debit_side():
    """13000 Cr 1,000 and 50005 Dr 1,050: the extra 50 goes to the cash line Debit (100 + 50 = 150)."""
    with tempfile.TemporaryDirectory() as tmp:
        r = core.build_result(make_file(Path(tmp), "9001-Export_JournalEntry.csv",
                                        ["9001,18300,100.00", "9001,13000,-1000.00", "9001,50005,1050.00",
                                         "9001,40000,-150.00"]))
    assert r.leftover == D("50.00")
    assert lines_of(r) == [("11000", "cash_line", D("150.00"), D("0.00")), ("40000", "as_is", D("0.00"), D("150.00"))]
    assert r.summary_debit == r.summary_credit == D("150.00") and r.status == "OK"

def test_leftover_on_the_credit_side_and_a_new_account():
    """13000 Cr 23,137.43 and 50005 Dr 23,000.00: 137.43 goes to the cash line Credit; 99999 is flagged NEW."""
    with tempfile.TemporaryDirectory() as tmp:
        r = core.build_result(make_file(Path(tmp), "9002-Export_JournalEntry.csv",
                                        ["9002,13000,-23137.43", "9002,50005,23000.00", "9002,99999,137.43",
                                         "9002,18300,1000.00", "9002,40000,-1000.00"]))
    assert r.leftover == D("-137.43")
    assert r.cash_line.debit == D("1000.00") and r.cash_line.credit == D("137.43")
    assert r.summary_debit == r.summary_credit == D("1137.43")
    checks = {c.code: c for c in r.checks}
    assert checks["C5"].result == "FAIL" and "99999" in checks["C5"].detail
    assert checks["C3"].result == "PASS" and "moved into the 11000 line" in checks["C3"].detail
    assert r.status == "REVIEW"

def test_accounts_starting_with_1000_are_netted():
    """10005 and 10009 both start with 1000: their Debit comes off the cash line Credit."""
    with tempfile.TemporaryDirectory() as tmp:
        r = core.build_result(make_file(Path(tmp), "9003-Export_JournalEntry.csv",
                                        ["9003,18300,-500.00", "9003,10005,300.00", "9003,10009,200.00"]))
    assert r.netted == ["10005", "10009"]
    assert lines_of(r) == [("11000", "cash_line", D("0.00"), D("0.00"))]     # 500 - 300 - 200 = 0
    assert "10005 + 10009 netted" in r.cash_line.what
    assert next(c for c in r.checks if c.code == "C5").detail == "10009"      # 10009 is not a known account

def test_an_amount_that_is_not_a_number():
    with tempfile.TemporaryDirectory() as tmp:
        r = core.build_result(make_file(Path(tmp), "9004-Export_JournalEntry.csv",
                                        ["9004,40000,-100.00", "9004,18300,100.00", "9004,40000,abc"]))
    assert r.problems == ["Row 4: Amount is not a number ('abc') - line left out"]
    assert [c for c in r.checks if c.code == "DATA"][0].result == "FAIL"
    assert r.pivot_debit == r.pivot_credit == D("100.00") and r.status == "REVIEW"


def test_a_file_that_does_not_balance():
    with tempfile.TemporaryDirectory() as tmp:
        r = core.build_result(make_file(Path(tmp), "9005-Export_JournalEntry.csv",
                                        ["9005,40000,-100.00", "9005,18300,90.00"]))
    assert next(c for c in r.checks if c.code == "C1").result == "FAIL" and r.status == "REVIEW"

def test_a_file_without_an_account_column_raises():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "9006-Export_JournalEntry.csv"
        bad.write_text("Foo,Bar\n1,2\n", encoding="utf-8")
        try:
            core.build_result(bad)
        except ValueError as exc:
            assert "no Account column" in str(exc)
        else:
            raise AssertionError("a file without an Account column must raise ValueError")

def test_location_from_the_file_name_when_there_is_no_location_column():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "7777-Export_JournalEntry.csv"
        path.write_text("Account,Amount\n40000,-10.00\n18300,10.00\n", encoding="utf-8")
        assert core.build_result(path).location == "7777"

if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"  OK  {name}")
    print(f"\nAll {len(tests)} core tests passed")
