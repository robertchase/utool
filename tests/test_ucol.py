import pytest

from utool.ucol import split


DATA = (
    "1 2 3\n"
    "4 5 6\n"
    "A B C"
)

DATA_321 = (
    "3 2 1\n"
    "6 5 4\n"
    "C B A"
)

DATA_11 = (
    "1 1\n"
    "4 4\n"
    "A A"
)

DATA_1_1 = (
    "1 3\n"
    "4 6\n"
    "A C"
)

DATA_BAR = (
    "1|2|3\n"
    "4|5|6\n"
    "A|B|C"
)

DATA_COMMA = (
    "1,2,3\n"
    "4,5,6\n"
    "A,B,C"
)

DATA_EXTRA = (
    "1  2 3\n"
    "4 5  6\n"
    "A B C"
)

DATA_EXTRA_123_COMMA = (
    "1,,2\n"
    "4,5,\n"
    "A,B,C"
)


@pytest.mark.parametrize("data, cols, delim, out_delim, nullable, result", (
    (DATA, [1, 2, 3], " ", " ", False, DATA),
    (DATA, [3, 2, 1], " ", " ", False, DATA_321),
    (DATA, [1, 1], " ", " ", False, DATA_11),
    (DATA, [1, -1], " ", " ", False, DATA_1_1),
    (DATA_BAR, [1, 2, 3], "|", " ", False, DATA),
    (DATA, [1, 2, 3], " ", ",", False, DATA_COMMA),
    (DATA_COMMA, [1, 2, 3], ",", "|", False, DATA_BAR),
    (DATA_EXTRA, [1, 2, 3], " ", ",", False, DATA_EXTRA_123_COMMA),
    (DATA_EXTRA, [1, 2, 3], " ", ",", True, DATA_COMMA),
))
def test_basic(data, cols, delim, out_delim, nullable, result):
    ans = "\n".join(
        [lin for lin in split(data, cols, delim, out_delim, nullable)])
    assert ans == result
