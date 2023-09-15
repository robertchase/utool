"""test upar"""
import pytest

from utool.upar import paragraph


@pytest.mark.parametrize(
    "data, cols, indent, result",
    (
        ("ABC DEF", 80, 0, "ABC DEF"),
        ("ABC DEF", 7, 0, "ABC DEF"),
        ("ABC DEF", 6, 0, "ABC\nDEF"),
        ("ABC DEF", 7, 1, " ABC\n DEF"),
        ("ABC DEF", 2, 1, " ABC\n DEF"),
        ("ABC\nDEF", 80, 0, "ABC DEF"),
        ("ABC\nDEF", 80, 2, "  ABC DEF"),
        ("   ABC\nDEF", 2, None, "   ABC\n   DEF"),
        ("ABC\n\nDEF", 80, 0, "ABC\n\nDEF"),
        ("\n\nABC\n\nDEF\n\n", 80, 0, "ABC\n\nDEF"),
    ),
)
def test_format(data, cols, indent, result):
    """test paragraph function"""
    ans = "\n".join(line for line in paragraph(data, cols, indent))
    assert ans == result
