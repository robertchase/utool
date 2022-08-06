import pytest

from utool.usum import group_by


DATA = (
    "A 1",
    "B 2",
    "A 3",
    "B 4",
)

DATA_2_KEY = (
    "A A 1",
    "A B 2",
    "A A 3",
    "A B 4",
)

DATA_2_KEY_ORDER = (
    "A 1 A",
    "A 2 B",
    "A 3 A",
    "A 4 B",
)

DATA_2_VAL = (
    "A 1 10",
    "B 2 20",
    "A 3 30",
    "B 4 40",
)

DATA_FLOAT = (
    "A 1.1",
    "B 2.2",
    "A 3.3",
    "B 4.4",
)


@pytest.mark.parametrize("data, cols, result", (
    (DATA, [1], {"A": [4], "B": [6]}),
    (DATA_2_KEY, [1, 2], {"A A": [4], "A B": [6]}),
    (DATA_2_KEY_ORDER, [1, 3], {"A A": [4], "A B": [6]}),
    (DATA_2_VAL, [1], {"A": [4, 40], "B": [6, 60]}),
    (DATA_FLOAT, [1], {"A": [1.1 + 3.3], "B": [2.2 + 4.4]}),
))
def test_group_by(data, cols, result):
    assert group_by(data, cols) == result
