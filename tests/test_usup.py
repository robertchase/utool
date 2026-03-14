"""tests for usup"""

import pytest

from utool import usup


DATA_SIMPLE = [
    {"Activity": "email", "Date": "2026-03-02", "Category": "Admin", "hours": "0.25", "total": "4.75"},
    {"Activity": "standup", "Date": "2026-03-02", "Category": "Meetings", "hours": "0.75", "total": "4.75"},
    {"Activity": "coding", "Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
    {"Activity": "review", "Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
    {"Activity": "email", "Date": "2026-03-03", "Category": "Admin", "hours": "0.5", "total": "5.5"},
    {"Activity": "coding", "Date": "2026-03-03", "Category": "Dev", "hours": "5.0", "total": "5.5"},
]


def _copy(rows):
    """Deep copy list of dicts to avoid mutation between tests."""
    return [dict(r) for r in rows]


@pytest.mark.parametrize(
    "specs, column, expected",
    (
        (
            [("total", ["Date"])],
            "total",
            ["4.75", "", "", "", "5.5", ""],
        ),
        (
            [("hours", ["Date", "Category"])],
            "hours",
            ["0.25", "0.75", "3.75", "", "0.5", "5.0"],
        ),
        (
            [("Category", ["Date", "Category"])],
            "Category",
            ["Admin", "Meetings", "Dev", "", "Admin", "Dev"],
        ),
    ),
)
def test_suppress(specs, column, expected):
    """test suppress function with various specs"""
    rows = _copy(DATA_SIMPLE)
    result = usup.suppress(rows, specs)
    assert [r[column] for r in result] == expected


def test_suppress_multiple_specs():
    """test suppress with multiple specs applied together"""
    rows = _copy(DATA_SIMPLE)
    specs = [
        ("total", ["Date"]),
        ("hours", ["Date", "Category"]),
        ("Category", ["Date", "Category"]),
    ]
    result = usup.suppress(rows, specs)
    assert [r["total"] for r in result] == ["4.75", "", "", "", "5.5", ""]
    assert [r["hours"] for r in result] == ["0.25", "0.75", "3.75", "", "0.5", "5.0"]
    assert [r["Category"] for r in result] == ["Admin", "Meetings", "Dev", "", "Admin", "Dev"]


@pytest.mark.parametrize(
    "spec, expected",
    (
        ("total:Date", ("total", ["Date"])),
        ("hours:Date,Category", ("hours", ["Date", "Category"])),
        (" hours : Date , Category ", ("hours", ["Date", "Category"])),
    ),
)
def test_parse_spec(spec, expected):
    """test spec parsing"""
    assert usup.parse_spec(spec) == expected


def test_parse_spec_invalid():
    """test that invalid spec raises ValueError"""
    with pytest.raises(ValueError):
        usup.parse_spec("no_colon")


def test_format_table():
    """test table formatting"""
    rows = [
        {"A": "hello", "B": "1"},
        {"A": "", "B": "2"},
    ]
    output = usup.format_table(rows, ["A", "B"])
    lines = output.strip().split("\n")
    assert len(lines) == 4  # header + separator + 2 data rows
    assert "A" in lines[0]
    assert "---" in lines[1]
    assert "hello" in lines[2]


def test_suppress_empty():
    """test suppress with no rows"""
    assert usup.suppress([], [("col", ["key"])]) == []


# --- resolve_spec / column index tests ---

FIELDNAMES = ["Activity", "Date", "Category", "hours", "total"]


@pytest.mark.parametrize(
    "spec, expected",
    (
        (("total", ["Date"]), ("total", ["Date"])),
        (("5", ["2"]), ("total", ["Date"])),
        (("4", ["2", "3"]), ("hours", ["Date", "Category"])),
        (("Category", ["2"]), ("Category", ["Date"])),
        (("3", ["Date", "Category"]), ("Category", ["Date", "Category"])),
    ),
)
def test_resolve_spec(spec, expected):
    """test resolving numeric column indices to names"""
    assert usup.resolve_spec(spec, FIELDNAMES) == expected


@pytest.mark.parametrize("index", ("0", "6", "-1"))
def test_resolve_spec_out_of_range(index):
    """test that out-of-range indices raise ValueError"""
    with pytest.raises(ValueError, match="out of range"):
        usup.resolve_spec((index, ["1"]), FIELDNAMES)


def test_resolve_spec_key_out_of_range():
    """test that out-of-range key index raises ValueError"""
    with pytest.raises(ValueError, match="out of range"):
        usup.resolve_spec(("1", ["99"]), FIELDNAMES)


# --- sort_keys tests ---


def test_sort_keys_single_spec():
    """test sort_keys with a single spec"""
    specs = [("total", ["Date"])]
    assert usup.sort_keys(specs) == ["Date"]


def test_sort_keys_multiple_specs_deduplicates():
    """test sort_keys deduplicates and preserves first-seen order"""
    specs = [
        ("total", ["Date"]),
        ("hours", ["Date", "Category"]),
        ("Category", ["Date", "Category"]),
    ]
    assert usup.sort_keys(specs) == ["Date", "Category"]


def test_sort_keys_ordering():
    """test sort_keys preserves order across specs with different keys"""
    specs = [
        ("a", ["X", "Y"]),
        ("b", ["Z", "X"]),
    ]
    assert usup.sort_keys(specs) == ["X", "Y", "Z"]


# --- sort + suppress integration tests ---


DATA_UNSORTED = [
    {"Date": "2026-03-03", "Category": "Dev", "hours": "5.0", "total": "5.5"},
    {"Date": "2026-03-02", "Category": "Admin", "hours": "0.25", "total": "4.75"},
    {"Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
    {"Date": "2026-03-03", "Category": "Admin", "hours": "0.5", "total": "5.5"},
    {"Date": "2026-03-02", "Category": "Dev", "hours": "3.75", "total": "4.75"},
]


def test_sort_then_suppress():
    """test that sorting by key columns produces correct suppression"""
    rows = _copy(DATA_UNSORTED)
    specs = [("total", ["Date"])]
    keys = usup.sort_keys(specs)
    rows.sort(key=lambda r: tuple(r[k] for k in keys))
    result = usup.suppress(rows, specs)
    assert [r["total"] for r in result] == ["4.75", "", "", "5.5", ""]
    assert [r["Date"] for r in result] == [
        "2026-03-02", "2026-03-02", "2026-03-02", "2026-03-03", "2026-03-03",
    ]


def test_sort_then_suppress_compound_keys():
    """test sort + suppress with compound keys"""
    rows = _copy(DATA_UNSORTED)
    specs = [("hours", ["Date", "Category"])]
    keys = usup.sort_keys(specs)
    rows.sort(key=lambda r: tuple(r[k] for k in keys))
    result = usup.suppress(rows, specs)
    assert [r["hours"] for r in result] == ["0.25", "3.75", "", "0.5", "5.0"]
