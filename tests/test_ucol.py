"""test ucol"""

import pytest

from utool import ucol


DATA = "1 2 3\n" + "4 5 6\n" + "A B C"

DATA_1 = [["1"], ["4"], ["A"]]

DATA_123 = [["1", "2", "3"], ["4", "5", "6"], ["A", "B", "C"]]

DATA_321 = [["3", "2", "1"], ["6", "5", "4"], ["C", "B", "A"]]

DATA_11 = [["1", "1"], ["4", "4"], ["A", "A"]]

DATA_1_1 = [["1", "3"], ["4", "6"], ["A", "C"]]

DATA_BAR = "1|2|3\n" + "4|5|6\n" + "A|B|C"

DATA_VARIABLE = "1 2 3 4 5 6\n" + "A B C D\n" + "9 8 7 6 5 4 3 2 1 0"

DATA_VARIABLE_4 = [
    ["1", "4", "5", "6"],
    ["A", "D"],
    ["9", "6", "5", "4", "3", "2", "1", "0"],
]

DATA_SPACES = "  1   2   3\n" + "    4     5     6\n" + "A B C"

DATA_SPACES_NULLABLE_1 = [[""], [""], ["A"]]


@pytest.mark.parametrize(
    "data, cols, delim, nullable, result",
    (
        (DATA, ["1"], " ", False, DATA_1),
        (DATA, ["1", "2", "3"], " ", False, DATA_123),
        (DATA, ["3", "2", "1"], " ", False, DATA_321),
        (DATA, ["1", "1"], " ", False, DATA_11),
        (DATA, ["1", "-1"], " ", False, DATA_1_1),
        (DATA_BAR, ["1", "2", "3"], "|", False, DATA_123),
        (DATA_VARIABLE, ["1", "4+"], " ", False, DATA_VARIABLE_4),
        (DATA_SPACES, ["1"], " ", True, DATA_1),
        (DATA_SPACES, ["1"], " ", False, DATA_SPACES_NULLABLE_1),
    ),
)
def test_basic(data, cols, delim, nullable, result):
    """test split function"""
    ans = list(ucol.split(data, cols, delim, nullable))
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
    ans = list(lin for lin in ucol.split(data, cols, is_csv=True))
    assert ans == result


DATA_SPARSE = "1 2\n3\n4 5"

DATA_SPARSE_2 = [["2"], ["5"]]


def test_strict():
    """test strict switch"""

    ans = list(lin for lin in ucol.split(DATA_SPARSE, ["2"]))
    assert ans == DATA_SPARSE_2

    with pytest.raises(ucol.UcolException):
        list(ucol.split(DATA_SPARSE, ["2"], strict=True))


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
