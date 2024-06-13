"""test ucol"""

import pytest

from utool import ucol


DATA = "1 2 3\n" + "4 5 6\n" + "A B C"

DATA_1 = "1\n" + "4\n" + "A"

DATA_321 = "3 2 1\n" + "6 5 4\n" + "C B A"

DATA_11 = "1 1\n" + "4 4\n" + "A A"

DATA_1_1 = "1 3\n" + "4 6\n" + "A C"

DATA_BAR = "1|2|3\n" + "4|5|6\n" + "A|B|C"

DATA_COMMA = "1,2,3\n" + "4,5,6\n" + "A,B,C"

DATA_EXTRA = "1  2 3\n" + "4 5  6\n" + "A B C"

DATA_EXTRA_123_COMMA = "1,,2\n" + "4,5,\n" + "A,B,C"

DATA_VARIABLE = "1 2 3 4 5 6\n" + "A B C D\n" + "9 8 7 6 5 4 3 2 1 0"

DATA_VARIABLE_4 = "1 4 5 6\n" + "A D\n" + "9 6 5 4 3 2 1 0"

DATA_SPACES = "  1   2   3\n" + "    4     5     6\n" + "A B C"

DATA_SPACES_NULLABLE_1 = "\n" + "\n" + "A"


@pytest.mark.parametrize(
    "data, cols, delim, out_delim, nullable, result",
    (
        (DATA, ["1"], " ", " ", False, DATA_1),
        (DATA, ["1", "2", "3"], " ", " ", False, DATA),
        (DATA, ["3", "2", "1"], " ", " ", False, DATA_321),
        (DATA, ["1", "1"], " ", " ", False, DATA_11),
        (DATA, ["1", "-1"], " ", " ", False, DATA_1_1),
        (DATA_BAR, ["1", "2", "3"], "|", " ", False, DATA),
        (DATA, ["1", "2", "3"], " ", ",", False, DATA_COMMA),
        (DATA_COMMA, ["1", "2", "3"], ",", "|", False, DATA_BAR),
        (DATA_EXTRA, ["1", "2", "3"], " ", ",", False, DATA_EXTRA_123_COMMA),
        (DATA_EXTRA, ["1", "2", "3"], " ", ",", True, DATA_COMMA),
        (DATA_VARIABLE, ["1", "4+"], " ", " ", False, DATA_VARIABLE_4),
        (DATA_SPACES, ["1"], " ", " ", True, DATA_1),
        (DATA_SPACES, ["1"], " ", " ", False, DATA_SPACES_NULLABLE_1.strip()),
    ),
)
# pylint: disable-next=too-many-arguments
def test_basic(data, cols, delim, out_delim, nullable, result):
    """test split function"""
    ans = "\n".join(lin for lin in ucol.split(data, cols, delim, out_delim, nullable))
    assert ans == result


DATA_CSV = '"1"," 2",3\n' + '"4",5,6\n' + '"A","""B",C'

DATA_CSV_1 = "1\n" + "4\n" + "A"

DATA_CSV_2 = " 2\n" + "5\n" + '"B'

DATA_CSV_3 = "3\n" + "6\n" + "C"


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
    ans = "\n".join(lin for lin in ucol.split(data, cols, is_csv=True))
    assert ans == result


DATA_SPARSE = "1 2\n3\n4 5"

DATA_SPARSE_2 = "2\n5"


def test_strict():
    """test strict switch"""

    ans = "\n".join(lin for lin in ucol.split(DATA_SPARSE, ["2"]))
    assert ans == DATA_SPARSE_2

    with pytest.raises(ucol.UcolException):
        list(ucol.split(DATA_SPARSE, ["2"], strict=True))
