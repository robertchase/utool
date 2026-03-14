"""tests for ubrk"""

import pytest

from utool import ubrk


# --- test data ---

DATA = [
    {"Date": "2026-03-02", "Category": "Admin", "hours": "0.25", "total": "4.75"},
    {"Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
    {"Date": "2026-03-02", "Category": "Dev", "hours": "0.75", "total": "4.75"},
    {"Date": "2026-03-03", "Category": "Admin", "hours": "0.5", "total": "5.5"},
    {"Date": "2026-03-03", "Category": "Dev", "hours": "5.0", "total": "5.5"},
]

FIELDNAMES = ["Date", "Category", "hours", "total"]


def _copy(rows):
    """Deep copy list of dicts to avoid mutation between tests."""
    return [dict(r) for r in rows]


# --- parse_break_spec tests ---


@pytest.mark.parametrize(
    "spec, expected",
    (
        ("Date", (["Date"], [])),
        ("Date:hours", (["Date"], ["hours"])),
        ("Date,Category:hours,total", (["Date", "Category"], ["hours", "total"])),
        (" Date , Category : hours , total ", (["Date", "Category"], ["hours", "total"])),
    ),
)
def test_parse_break_spec(spec, expected):
    """test parsing break specs"""
    assert ubrk.parse_break_spec(spec) == expected


def test_parse_break_spec_empty():
    """test that empty break column raises ValueError"""
    with pytest.raises(ValueError, match="at least one break column"):
        ubrk.parse_break_spec(":hours")


# --- resolve_name tests ---


@pytest.mark.parametrize(
    "name, expected",
    (
        ("Date", "Date"),
        ("1", "Date"),
        ("3", "hours"),
    ),
)
def test_resolve_name(name, expected):
    """test resolving column names and indices"""
    assert ubrk.resolve_name(name, FIELDNAMES) == expected


@pytest.mark.parametrize("index", ("0", "5", "-1"))
def test_resolve_name_out_of_range(index):
    """test that out-of-range indices raise ValueError"""
    with pytest.raises(ValueError, match="out of range"):
        ubrk.resolve_name(index, FIELDNAMES)


# --- resolve_break_spec tests ---


def test_resolve_break_spec_numeric():
    """test resolving numeric indices in break spec"""
    spec = (["1"], ["3", "4"])
    assert ubrk.resolve_break_spec(spec, FIELDNAMES) == (
        ["Date"],
        ["hours", "total"],
    )


# --- insert_breaks tests ---


def test_insert_breaks_no_subtotals():
    """test break rows with no subtotals are all blank"""
    rows = _copy(DATA)
    result = ubrk.insert_breaks(rows, ["Date"], [], FIELDNAMES)
    # 5 data rows + 2 break rows (one per group)
    assert len(result) == 7
    # break row after first group (index 3)
    assert result[3] == {"Date": "", "Category": "", "hours": "", "total": ""}
    # break row after second group (index 6)
    assert result[6] == {"Date": "", "Category": "", "hours": "", "total": ""}


def test_insert_breaks_with_subtotals():
    """test break rows with subtotal columns"""
    rows = _copy(DATA)
    result = ubrk.insert_breaks(rows, ["Date"], ["hours"], FIELDNAMES)
    assert len(result) == 7
    # break row after first group sums hours: 0.25 + 3.75 + 0.75 = 4.75
    assert result[3]["hours"] == "4.75"
    assert result[3]["Date"] == ""
    assert result[3]["Category"] == ""
    assert result[3]["total"] == ""
    # break row after second group sums hours: 0.5 + 5.0 = 5.5
    assert result[6]["hours"] == "5.5"


def test_insert_breaks_multiple_subtotal_cols():
    """test break rows with multiple subtotal columns"""
    rows = _copy(DATA)
    result = ubrk.insert_breaks(rows, ["Date"], ["hours", "total"], FIELDNAMES)
    # first group: hours=4.75, total=4.75+4.75+4.75=14.25
    assert result[3]["hours"] == "4.75"
    assert result[3]["total"] == "14.25"
    # second group: hours=5.5, total=5.5+5.5=11.0
    assert result[6]["hours"] == "5.5"
    assert result[6]["total"] == "11.0"


def test_insert_breaks_multiple_break_cols():
    """test breaks on compound columns"""
    rows = _copy(DATA)
    result = ubrk.insert_breaks(rows, ["Date", "Category"], ["hours"], FIELDNAMES)
    # Groups: (03-02,Admin), (03-02,Dev), (03-03,Admin), (03-03,Dev)
    # 5 data rows + 4 break rows = 9
    assert len(result) == 9
    # (03-02,Admin): hours=0.25
    assert result[1]["hours"] == "0.25"
    assert result[1]["Date"] == ""
    # (03-02,Dev): hours=3.75+0.75=4.50
    assert result[4]["hours"] == "4.50"
    # (03-03,Admin): hours=0.5
    assert result[6]["hours"] == "0.5"
    # (03-03,Dev): hours=5.0
    assert result[8]["hours"] == "5.0"


def test_insert_breaks_empty():
    """test insert_breaks with no rows"""
    assert ubrk.insert_breaks([], ["Date"], ["hours"], FIELDNAMES) == []


def test_insert_breaks_single_group():
    """test insert_breaks with all rows in one group"""
    rows = _copy(DATA[:3])  # all Date=2026-03-02
    result = ubrk.insert_breaks(rows, ["Date"], ["hours"], FIELDNAMES)
    assert len(result) == 4  # 3 data + 1 break
    assert result[3]["hours"] == "4.75"


# --- append_total tests ---


def test_append_total():
    """test grand total row"""
    rows = _copy(DATA)
    total_row = ubrk.append_total(rows, ["hours"], FIELDNAMES)
    # 0.25 + 3.75 + 0.75 + 0.5 + 5.0 = 10.25
    assert total_row["hours"] == "10.25"
    assert total_row["Date"] == ""
    assert total_row["Category"] == ""
    assert total_row["total"] == ""


def test_append_total_multiple_cols():
    """test grand total with multiple columns"""
    rows = _copy(DATA)
    total_row = ubrk.append_total(rows, ["hours", "total"], FIELDNAMES)
    assert total_row["hours"] == "10.25"
    # total: 4.75+4.75+4.75+5.5+5.5 = 25.25
    assert total_row["total"] == "25.25"


# --- _sum_col tests ---


def test_sum_col_with_blanks():
    """test that blank values are skipped during summing"""
    rows = [{"x": "1.5"}, {"x": ""}, {"x": "2.5"}]
    assert ubrk._sum_col(rows, "x") == "4.0"


def test_sum_col_integers():
    """test summing integer values"""
    rows = [{"x": "10"}, {"x": "20"}, {"x": "30"}]
    assert ubrk._sum_col(rows, "x") == "60"


def test_sum_col_non_numeric():
    """test that non-numeric values are skipped"""
    rows = [{"x": "1.5"}, {"x": "abc"}, {"x": "2.5"}]
    assert ubrk._sum_col(rows, "x") == "4.0"


# --- sort + break integration ---


DATA_UNSORTED = [
    {"Date": "2026-03-03", "Category": "Dev", "hours": "5.0", "total": "5.5"},
    {"Date": "2026-03-02", "Category": "Admin", "hours": "0.25", "total": "4.75"},
    {"Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
    {"Date": "2026-03-03", "Category": "Admin", "hours": "0.5", "total": "5.5"},
]


def test_sort_then_break():
    """test that sorting before breaking produces correct groups"""
    rows = _copy(DATA_UNSORTED)
    break_cols = ["Date"]
    rows.sort(key=lambda r: tuple(r[c] for c in break_cols))
    result = ubrk.insert_breaks(rows, break_cols, ["hours"], FIELDNAMES)
    # 4 data rows + 2 break rows = 6
    assert len(result) == 6
    # first group (03-02): 0.25 + 3.75 = 4.00
    assert result[2]["hours"] == "4.00"
    # second group (03-03): 0.5 + 5.0 = 5.5
    assert result[5]["hours"] == "5.5"


# --- format_table tests ---


def test_format_table():
    """test table formatting"""
    rows = [
        {"A": "hello", "B": "1"},
        {"A": "", "B": "2"},
    ]
    output = ubrk.format_table(rows, ["A", "B"])
    lines = output.strip().split("\n")
    assert len(lines) == 4  # header + separator + 2 data rows
    assert "A" in lines[0]
    assert "---" in lines[1]
    assert "hello" in lines[2]
