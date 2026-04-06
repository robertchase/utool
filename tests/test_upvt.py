"""Tests for upvt."""

import pytest

from utool import upvt


# --- test data ---

DATA = [
    {"Region": "East", "Product": "Widget", "Revenue": "100"},
    {"Region": "East", "Product": "Gadget", "Revenue": "200"},
    {"Region": "West", "Product": "Widget", "Revenue": "150"},
    {"Region": "West", "Product": "Gadget", "Revenue": "300"},
    {"Region": "East", "Product": "Widget", "Revenue": "50"},
]

FIELDNAMES = ["Region", "Product", "Revenue"]


def _copy(rows):
    """Deep copy list of dicts to avoid mutation between tests."""
    return [dict(r) for r in rows]


# --- parse_col_arg tests ---


@pytest.mark.parametrize(
    "arg, expected",
    (
        ("Region", ("Region", None)),
        ("Region+", ("Region", "asc")),
        ("Region-", ("Region", "desc")),
        ("1+", ("1", "asc")),
        ("1-", ("1", "desc")),
        ("1", ("1", None)),
    ),
)
def test_parse_sort_suffix(arg, expected):
    """Test parsing argument with optional sort suffix."""
    assert upvt.parse_sort_suffix(arg) == expected


# --- resolve_name tests ---


@pytest.mark.parametrize(
    "name, expected",
    (
        ("Region", "Region"),
        ("1", "Region"),
        ("2", "Product"),
        ("3", "Revenue"),
    ),
)
def test_resolve_name(name, expected):
    """Test resolving column names and indices."""
    assert upvt.resolve_name(name, FIELDNAMES) == expected


@pytest.mark.parametrize("index", ("0", "4", "-1"))
def test_resolve_name_out_of_range(index):
    """Test that out-of-range indices raise ValueError."""
    with pytest.raises(ValueError, match="out of range"):
        upvt.resolve_name(index, FIELDNAMES)


# --- _sum_values tests ---


def test_sum_values_basic():
    """Test summing a list of values."""
    assert upvt._sum_values(["100", "50"]) == "150"


def test_sum_values_decimals():
    """Test summing preserves decimal precision."""
    assert upvt._sum_values(["1.50", "2.25"]) == "3.75"


def test_sum_values_blanks():
    """Test that blank values are skipped."""
    assert upvt._sum_values(["10", "", "20"]) == "30"


def test_sum_values_non_numeric():
    """Test that non-numeric values are skipped."""
    assert upvt._sum_values(["10", "abc", "20"]) == "30"


def test_sum_values_empty():
    """Test summing an empty list."""
    assert upvt._sum_values([]) == "0"


# --- pivot tests ---


def test_pivot_basic():
    """Test basic pivot table creation."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue")
    assert fnames == ["Region", "Widget", "Gadget"]
    assert len(result) == 2
    # East: Widget=100+50=150, Gadget=200
    east = result[0]
    assert east["Region"] == "East"
    assert east["Widget"] == "150"
    assert east["Gadget"] == "200"
    # West: Widget=150, Gadget=300
    west = result[1]
    assert west["Region"] == "West"
    assert west["Widget"] == "150"
    assert west["Gadget"] == "300"


def test_pivot_preserves_encounter_order():
    """Test that row and column order matches first encounter."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue")
    # East appears before West; Widget appears before Gadget
    assert fnames == ["Region", "Widget", "Gadget"]
    assert result[0]["Region"] == "East"
    assert result[1]["Region"] == "West"


def test_pivot_rows_asc():
    """Test pivot with rows sorted ascending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", row_sort="asc")
    assert result[0]["Region"] == "East"
    assert result[1]["Region"] == "West"
    # Columns stay in encounter order
    assert fnames == ["Region", "Widget", "Gadget"]


def test_pivot_rows_desc():
    """Test pivot with rows sorted descending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", row_sort="desc")
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_cols_asc():
    """Test pivot with columns sorted ascending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", col_sort="asc")
    assert fnames == ["Region", "Gadget", "Widget"]
    # Rows stay in encounter order
    assert result[0]["Region"] == "East"
    assert result[1]["Region"] == "West"


def test_pivot_cols_desc():
    """Test pivot with columns sorted descending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", col_sort="desc")
    assert fnames == ["Region", "Widget", "Gadget"]


def test_pivot_both_sorted():
    """Test pivot with both rows and columns sorted."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", row_sort="desc", col_sort="asc"
    )
    assert fnames == ["Region", "Gadget", "Widget"]
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_missing_cells():
    """Test that missing row/col combinations produce empty strings."""
    rows = [
        {"R": "a", "C": "x", "V": "1"},
        {"R": "b", "C": "y", "V": "2"},
    ]
    fnames, result = upvt.pivot(rows, "R", "C", "V")
    assert fnames == ["R", "x", "y"]
    assert result[0]["x"] == "1"
    assert result[0]["y"] == ""
    assert result[1]["x"] == ""
    assert result[1]["y"] == "2"


def test_pivot_empty():
    """Test pivot with no rows."""
    fnames, result = upvt.pivot([], "R", "C", "V")
    assert fnames == ["R"]
    assert result == []


def test_pivot_single_row():
    """Test pivot with a single row."""
    rows = [{"R": "a", "C": "x", "V": "5"}]
    fnames, result = upvt.pivot(rows, "R", "C", "V")
    assert fnames == ["R", "x"]
    assert result == [{"R": "a", "x": "5"}]


def test_pivot_decimal_precision():
    """Test that decimal precision is preserved in aggregation."""
    rows = [
        {"R": "a", "C": "x", "V": "1.50"},
        {"R": "a", "C": "x", "V": "2.75"},
    ]
    fnames, result = upvt.pivot(rows, "R", "C", "V")
    assert result[0]["x"] == "4.25"


# --- htotal column tests ---


def test_pivot_htotal():
    """Test pivot with horizontal total column."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", htotal=True)
    assert fnames == ["Region", "Widget", "Gadget", "Total"]
    # East: 150 + 200 = 350
    assert result[0]["Total"] == "350"
    # West: 150 + 300 = 450
    assert result[1]["Total"] == "450"


def test_pivot_htotal_sort_desc():
    """Test that htotal_sort=desc sorts rows by total descending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, htotal_sort="desc"
    )
    # West (450) before East (350)
    assert result[0]["Region"] == "West"
    assert result[0]["Total"] == "450"
    assert result[1]["Region"] == "East"
    assert result[1]["Total"] == "350"


def test_pivot_htotal_sort_asc():
    """Test that htotal_sort=asc sorts rows by total ascending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, htotal_sort="asc"
    )
    # East (350) before West (450)
    assert result[0]["Region"] == "East"
    assert result[1]["Region"] == "West"


def test_pivot_htotal_sort_overrides_row_sort():
    """Test that htotal_sort overrides row_sort."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue",
        row_sort="asc", htotal=True, htotal_sort="desc",
    )
    # htotal_sort wins: West (450) before East (350)
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_htotal_missing_cells():
    """Test htotal with sparse pivot (missing cells not summed)."""
    rows = [
        {"R": "a", "C": "x", "V": "10"},
        {"R": "b", "C": "y", "V": "20"},
    ]
    fnames, result = upvt.pivot(rows, "R", "C", "V", htotal=True)
    assert result[0]["Total"] == "10"
    assert result[1]["Total"] == "20"


# --- vtotal row tests ---


def test_pivot_vtotal():
    """Test pivot with vertical total row."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", vtotal=True)
    assert fnames == ["Region", "Widget", "Gadget"]
    assert len(result) == 3  # 2 data rows + 1 total row
    total_row = result[-1]
    assert total_row["Region"] == "Total"
    # Widget: 150 (East) + 150 (West) = 300
    assert total_row["Widget"] == "300"
    # Gadget: 200 (East) + 300 (West) = 500
    assert total_row["Gadget"] == "500"


def test_pivot_vtotal_and_htotal():
    """Test pivot with both vtotal and htotal; bottom-right is grand total."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, vtotal=True
    )
    assert fnames == ["Region", "Widget", "Gadget", "Total"]
    total_row = result[-1]
    assert total_row["Region"] == "Total"
    assert total_row["Widget"] == "300"
    assert total_row["Gadget"] == "500"
    # Grand total: 350 + 450 = 800
    assert total_row["Total"] == "800"


def test_pivot_vtotal_stays_last_after_sort():
    """Test that vtotal row is appended after sorting."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue",
        htotal=True, htotal_sort="desc", vtotal=True,
    )
    assert result[-1]["Region"] == "Total"
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_vtotal_summary_only():
    """Test vtotal row with summary_only shows only label and htotal."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue",
        htotal=True, vtotal=True, summary_only=True,
    )
    assert fnames == ["Region", "Total"]
    total_row = result[-1]
    assert total_row == {"Region": "Total", "Total": "800"}


def test_pivot_vtotal_with_avg_leaves_avg_blank():
    """Test vtotal row has blank Avg cell."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", avg=True, vtotal=True
    )
    assert result[-1]["Avg"] == ""


# --- avg column tests ---


def test_pivot_avg():
    """Test pivot with avg column."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(rows, "Region", "Product", "Revenue", avg=True)
    assert fnames == ["Region", "Widget", "Gadget", "Avg"]
    # East: (150 + 200) / 2 = 175.00
    assert result[0]["Avg"] == "175.00"
    # West: (150 + 300) / 2 = 225.00
    assert result[1]["Avg"] == "225.00"


def test_pivot_avg_missing_cells():
    """Test avg denominator includes missing cells (treated as 0)."""
    rows = [
        {"R": "a", "C": "x", "V": "10"},
        {"R": "b", "C": "y", "V": "20"},
    ]
    fnames, result = upvt.pivot(rows, "R", "C", "V", avg=True)
    # 2 columns total; row "a": 10/2=5.00, row "b": 20/2=10.00
    assert result[0]["Avg"] == "5.00"
    assert result[1]["Avg"] == "10.00"


def test_pivot_avg_sort_desc():
    """Test avg_sort=desc sorts rows by avg descending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", avg=True, avg_sort="desc"
    )
    # West (225.00) before East (175.00)
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_avg_sort_asc():
    """Test avg_sort=asc sorts rows by avg ascending."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", avg=True, avg_sort="asc"
    )
    assert result[0]["Region"] == "East"
    assert result[1]["Region"] == "West"


def test_pivot_avg_sort_overrides_total_sort():
    """Test avg_sort overrides total_sort."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue",
        htotal=True, htotal_sort="asc",
        avg=True, avg_sort="desc",
    )
    # avg_sort wins: West (225) before East (175)
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


def test_pivot_total_and_avg_column_order():
    """Test Total appears before Avg when both are present."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, avg=True
    )
    assert fnames[-2] == "Total"
    assert fnames[-1] == "Avg"


def test_avg_values_basic():
    """Test _avg_values with all cells present."""
    assert upvt._avg_values(["100", "200"], 2) == "150.00"


def test_avg_values_missing():
    """Test _avg_values with missing cells (denominator includes them)."""
    assert upvt._avg_values(["100"], 2) == "50.00"


def test_avg_values_zero_count():
    """Test _avg_values with zero columns."""
    assert upvt._avg_values([], 0) == "0.00"


# --- summary_only tests ---


def test_pivot_summary_only_total():
    """Test summary_only with --total omits pivot columns."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, summary_only=True
    )
    assert fnames == ["Region", "Total"]
    assert "Widget" not in fnames
    assert result[0] == {"Region": "East", "Total": "350"}
    assert result[1] == {"Region": "West", "Total": "450"}


def test_pivot_summary_only_avg():
    """Test summary_only with --avg omits pivot columns."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", avg=True, summary_only=True
    )
    assert fnames == ["Region", "Avg"]
    assert result[0]["Avg"] == "175.00"


def test_pivot_summary_only_total_and_avg():
    """Test summary_only with both --total and --avg."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue", htotal=True, avg=True, summary_only=True
    )
    assert fnames == ["Region", "Total", "Avg"]


def test_pivot_summary_only_sorting_still_works():
    """Test that sorting still applies with summary_only."""
    rows = _copy(DATA)
    fnames, result = upvt.pivot(
        rows, "Region", "Product", "Revenue",
        htotal=True, htotal_sort="desc", summary_only=True,
    )
    assert result[0]["Region"] == "West"
    assert result[1]["Region"] == "East"


# --- format_table tests ---


def test_format_table():
    """Test table formatting."""
    rows = [
        {"A": "hello", "B": "1"},
        {"A": "world", "B": "2"},
    ]
    output = upvt.format_table(rows, ["A", "B"])
    lines = output.strip().split("\n")
    assert len(lines) == 4  # header + separator + 2 data rows
    assert "A" in lines[0]
    assert "---" in lines[1]
    assert "hello" in lines[2]


def test_format_table_right_justify():
    """Test that right_justify right-aligns all columns except the first."""
    rows = [
        {"A": "East", "B": "100", "C": "1000"},
        {"A": "West", "B": "20",  "C": "200"},
    ]
    output = upvt.format_table(rows, ["A", "B", "C"], right_justify=True)
    lines = output.strip().split("\n")
    # Data rows: first col left-justified, others right-justified
    assert lines[2].startswith("East")
    assert lines[2].endswith("1000")
    assert lines[3].startswith("West")
    assert lines[3].endswith(" 200")


def test_format_table_vtotal_separator():
    """Test that vtotal=True inserts a separator before the last row."""
    rows = [
        {"A": "East", "B": "100"},
        {"A": "West", "B": "200"},
        {"A": "Total", "B": "300"},
    ]
    output = upvt.format_table(rows, ["A", "B"], vtotal=True)
    lines = output.strip().split("\n")
    # header + header-sep + 2 data rows + vtotal-sep + total row = 6
    assert len(lines) == 6
    sep_line = lines[4]
    # First column blank, second column dashed
    assert sep_line.startswith(" ")
    assert "---" in sep_line
    assert lines[5].startswith("Total")


def test_format_table_vtotal_separator_no_dashes_under_avg():
    """Test that the Avg column has no dashes in the vtotal separator."""
    rows = [
        {"A": "East", "B": "100", "Avg": "50.00"},
        {"A": "West", "B": "200", "Avg": "100.00"},
        {"A": "Total", "B": "300", "Avg": ""},
    ]
    output = upvt.format_table(rows, ["A", "B", "Avg"], vtotal=True, avg=True)
    lines = output.strip().split("\n")
    sep_line = lines[4]
    # Avg column should have no dashes; B column should
    assert "---" in sep_line
    assert sep_line.endswith(" " * len("Avg"))
