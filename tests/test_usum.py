"""tests for usum"""

import pytest

from utool import usum


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


DATA_ZERO = (
    "1 2 3",
    "4.5",
)


DATA_DELIMITER = (
    "1|2|3",
    "4|5|6",
)


DATA_COUNT = (
    "A 1",
    "B 2",
    "B 10",
    "A 3",
    "B 4",
    "C 10",
)


@pytest.mark.parametrize(
    "data, cols, result",
    (
        (DATA, [1], {"A": ["4"], "B": ["6"]}),
        (DATA_2_KEY, [1, 2], {"A A": ["4"], "A B": ["6"]}),
        (DATA_2_KEY_ORDER, [1, 3], {"A A": ["4"], "A B": ["6"]}),
        (DATA_2_VAL, [1], {"A": ["4", "40"], "B": ["6", "60"]}),
        (DATA_FLOAT, [1], {"A": ["4.4"], "B": ["6.6"]}),
    ),
)
def test_group_by(data, cols, result):
    """test group-by function"""
    assert usum.group_by(data, cols) == result


@pytest.mark.parametrize(
    "data, cols, result",
    (
        (DATA, [1], {"A": ["2", "4"], "B": ["2", "6"]}),
        (DATA_2_KEY, [1, 2], {"A A": ["2", "4"], "A B": ["2", "6"]}),
        (DATA_2_KEY_ORDER, [1, 3], {"A A": ["2", "4"], "A B": ["2", "6"]}),
        (DATA_2_VAL, [1], {"A": ["2", "4", "40"], "B": ["2", "6", "60"]}),
        (DATA_FLOAT, [1], {"A": ["2", "4.4"], "B": ["2", "6.6"]}),
        (DATA_COUNT, [1], {"A": ["2", "4"], "B": ["3", "16"], "C": ["1", "10"]}),
    ),
)
def test_group_by_with_count(data, cols, result):
    """test group-by function"""
    assert usum.group_by(data, cols, count=True) == result


@pytest.mark.parametrize(
    "data, result",
    ((DATA_ZERO, "10.5"),),
)
def test_sum_all(data, result):
    """test sum-all function"""
    assert usum.sum_all(data) == result


@pytest.mark.parametrize(
    "data, result",
    ((DATA_DELIMITER, {"": ["5", "7", "9"]}),),
)
def test_delimiter(data, result):
    """test non-space delimiter function"""
    assert usum.group_by(data, [], delim="|") == result


@pytest.mark.parametrize(
    "value, strict, result",
    (
        ("123", False, (123, 0)),
        ("123", True, (123, 0)),
        ("123.45", False, (123.45, 2)),
        ("123.45", True, (123.45, 2)),
        ("abc", False, (0, 0)),
        ("abc", True, None),
        ("$1,234.56", False, (1234.56, 2)),
        ("$1,234.56", True, None),
        ("$1,2345.6", False, (0, 0)),
        ("$1,2345.6", True, None),
        ("$123,456", False, (123456, 0)),
        ("$123,456.78", False, (123456.78, 2)),
        ("-$123,456.78", False, (-123456.78, 2)),
    ),
)
def test_num(value, strict, result):
    """Test parsing numbers."""
    if result:
        assert usum.num(value, strict) == result
    else:
        with pytest.raises(ValueError):
            usum.num(value, strict)
