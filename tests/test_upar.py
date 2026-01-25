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


@pytest.mark.parametrize(
    "data, cols, indent, hanging, result",
    (
        ("ABC DEF GHI", 8, 0, 2, "ABC DEF\n  GHI"),
        ("ABC DEF GHI JKL", 8, 0, 4, "ABC DEF\n    GHI\n    JKL"),
        ("ABC DEF", 80, 0, 2, "ABC DEF"),  # no wrap needed
        ("ABC DEF GHI", 10, 2, 2, "  ABC DEF\n    GHI"),  # indent + hanging
    ),
)
def test_hanging(data, cols, indent, hanging, result):
    """test hanging indent"""
    ans = "\n".join(line for line in paragraph(data, cols, indent, hanging=hanging))
    assert ans == result


@pytest.mark.parametrize(
    "data, cols, prefix, result",
    (
        ("ABC DEF", 80, "# ", "# ABC DEF"),
        ("ABC DEF GHI", 10, "# ", "# ABC DEF\n# GHI"),
        ("ABC DEF", 10, "> ", "> ABC DEF"),
        ("ABC\n\nDEF", 80, "// ", "// ABC\n\n// DEF"),  # preserves paragraph breaks
    ),
)
def test_prefix(data, cols, prefix, result):
    """test prefix"""
    ans = "\n".join(line for line in paragraph(data, cols, prefix=prefix))
    assert ans == result


@pytest.mark.parametrize(
    "data, cols, prefix, hanging, result",
    (
        ("ABC DEF GHI", 10, "# ", 2, "# ABC DEF\n#   GHI"),
        ("ABC DEF GHI JKL", 12, "> ", 4, "> ABC DEF\n>     GHI\n>     JKL"),
    ),
)
def test_prefix_hanging(data, cols, prefix, hanging, result):
    """test prefix combined with hanging indent"""
    ans = "\n".join(
        line for line in paragraph(data, cols, prefix=prefix, hanging=hanging)
    )
    assert ans == result
