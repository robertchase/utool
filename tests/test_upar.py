import pytest

from utool.upar import format


@pytest.mark.parametrize("data, cols, indent, result", (
    ("ABC DEF", 80, 0, "ABC DEF"),
    ("ABC DEF", 7, 0, "ABC DEF"),
    ("ABC DEF", 6, 0, "ABC\nDEF"),
    ("ABC DEF", 7, 1, " ABC\n DEF"),
    ("ABC DEF", 2, 1, " ABC\n DEF"),
    ("ABC\nDEF", 80, 0, "ABC DEF"),
    ("ABC\nDEF", 80, 2, "  ABC DEF"),
))
def test_format(data, cols, indent, result):
    ans = "\n".join([line for line in format(data, cols, indent)])
    assert ans == result
