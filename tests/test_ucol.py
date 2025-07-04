"""test ucol"""

import pytest

from utool import ucol


DATA = "1 2 3\n" + "4 5 6\n" + "A B C"

DATA_1 = [["1"], ["4"], ["A"]]

DATA_123 = [["1", "2", "3"], ["4", "5", "6"], ["A", "B", "C"]]

DATA_321 = [["3", "2", "1"], ["6", "5", "4"], ["C", "B", "A"]]

DATA_11 = [["1", "1"], ["4", "4"], ["A", "A"]]

DATA_1_1 = [["1", "3"], ["4", "6"], ["A", "C"]]

DATA_BAR = "1||2|3\n" + "4||5|6\n" + "A||B|C"

DATA_123_NULL = [["1", "", "2"], ["4", "", "5"], ["A", "", "B"]]

DATA_CARET = "^^1^2^3\n" + "4^5^6\n" + "A^B^C"

DATA_CARET_NOSTRIP = [["", "1", "2"], ["4", "5", "6"], ["A", "B", "C"]]

DATA_VARIABLE = "1 2 3 4 5 6\n" + "A B C D\n" + "9 8 7 6 5 4 3 2 1 0"

DATA_VARIABLE_4 = [
    ["1", "4", "5", "6"],
    ["A", "D"],
    ["9", "6", "5", "4", "3", "2", "1", "0"],
]

DATA_SPACES = "  1   2   3\n" + "    4     5     6\n" + "A B C"

DATA_SPACES_NULLABLE_1 = [[""], [""], ["A"]]


@pytest.mark.parametrize(
    "data, cols, delim, nullable, strip, result",
    (
        (DATA, ["1"], None, False, False, DATA_1),
        (DATA, ["1", "2", "3"], None, False, False, DATA_123),
        (DATA, ["3", "2", "1"], None, False, False, DATA_321),
        (DATA, ["1", "1"], None, False, False, DATA_11),
        (DATA, ["1", "-1"], " ", False, False, DATA_1_1),
        (DATA_VARIABLE, ["1", "4+"], None, False, False, DATA_VARIABLE_4),
        (DATA_BAR, ["1", "2", "3"], "|", False, False, DATA_123),
        (DATA_BAR, ["1", "2", "3"], "|", True, False, DATA_123_NULL),
        (DATA_CARET, ["1", "2", "3"], "^", False, False, DATA_CARET_NOSTRIP),
        (DATA_CARET, ["1", "2", "3"], "^", False, True, DATA_123),
        (DATA_SPACES, ["1"], None, True, True, DATA_1),
        (DATA_SPACES, ["1"], None, True, False, DATA_SPACES_NULLABLE_1),
        (DATA_SPACES, ["1"], None, False, True, DATA_1),
        (DATA_SPACES, ["1"], None, False, False, DATA_SPACES_NULLABLE_1),
    ),
)
# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def test_basic(data, cols, delim, nullable, strip, result):
    """test split function"""
    cols = [ucol.column_specifier(col) for col in cols]
    ans = list(ucol.split(data, cols, delim, nullable, strip))
    assert ans == result


DATA_DATE = "2025-01-02 A\n2026-03-04 B"


@pytest.mark.parametrize(
    "data, cols, result",
    (
        (DATA_DATE, ["1[1,7]", "2"], [["2025-01", "A"], ["2026-03", "B"]]),
        (DATA_DATE, ["1[,7]", "2"], [["2025-01", "A"], ["2026-03", "B"]]),
        (DATA_DATE, ["1[6]"], [["01-02"], ["03-04"]]),
        (DATA_DATE, ["1[6,100]"], [["01-02"], ["03-04"]]),
        (DATA_DATE, ["1[6,7]"], [["01"], ["03"]]),
    ),
)
def test_substring(data, cols, result):
    """Test substring operation."""
    cols = [ucol.column_specifier(col) for col in cols]
    ans = list(ucol.split(data, cols))
    assert ans == result


DATA_CSV = '"1"," 2",3\n' + '"4",5,6\n' + '"A","""B",C'

DATA_CSV_1 = [["1"], ["4"], ["A"]]

DATA_CSV_2 = [[" 2"], ["5"], ['"B']]

DATA_CSV_3 = [["3"], ["6"], ["C"]]


@pytest.mark.parametrize(
    "data, cols, result",
    (
        (DATA_CSV, ["1"], DATA_CSV_1),
        (DATA_CSV, ["2"], DATA_CSV_2),
        (DATA_CSV, ["3"], DATA_CSV_3),
    ),
)
def test_csv(data, cols, result):
    """test csv option"""
    cols = [ucol.column_specifier(col) for col in cols]
    ans = list(lin for lin in ucol.split(data, cols, is_csv=True))
    assert ans == result


DATA_SPARSE = "1 2\n3\n4 5"

DATA_SPARSE_2 = [["2"], ["5"]]


def test_strict():
    """test strict switch"""

    cols = [ucol.column_specifier("2")]

    ans = list(lin for lin in ucol.split(DATA_SPARSE, cols))
    assert ans == DATA_SPARSE_2

    with pytest.raises(ucol.UcolException):
        list(ucol.split(DATA_SPARSE, cols, strict=True))


@pytest.mark.parametrize(
    "value, result",
    (
        ("", ""),
        ("abc", "abc"),
        ("123", "123"),
        ("12,345", "12345"),
        ("12,34", "12,34"),
        ("12,345.678", "12345.678"),
        ("$12,345.678", "12345.678"),
        ("$12,345,000.678", "12345000.678"),
        ("$12", "12"),
        ("$12.34", "12.34"),
        ("$a", "$a"),
    ),
)
def test_remove_comma(value, result):
    """test numeric cleanup (remove '$' and ',')"""
    assert ucol.remove_comma(value) == result


@pytest.mark.parametrize(
    "value, result",
    (
        (1, "A"),
        (10, "J"),
        (26, "Z"),
        (27, "AA"),
        (987654321, "CECGIBQ"),
    ),
)
def test_as_alpha(value, result):
    """test base 26 conversion"""
    assert ucol.as_alpha(value) == result
