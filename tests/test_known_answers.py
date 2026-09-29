"""
tests/test_known_answers.py - the calculation still gives the demo numbers
==========================================================================
Run it from the project folder after every change:   python -m tests.test_known_answers
(With pytest installed, "python -m pytest" runs every test file.)
"""
from pathlib import Path

from app.engine import core

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_7003_demo_numbers():
    result = core.build_result(FIXTURES / "7003-Export_JournalEntry.csv")
    assert str(result.pivot_debit) == "1197949.08"          # pivot Grand Total, as in the Working file
    assert str(result.summary_debit) == "733846.98"         # Summary JE total, as in the Working file


def test_44105_demo_numbers():
    result = core.build_result(FIXTURES / "44105-Export_JournalEntry.csv")
    assert str(result.summary_debit) == "216073.21"


if __name__ == "__main__":
    test_7003_demo_numbers()
    test_44105_demo_numbers()
    print("All known answers match")
