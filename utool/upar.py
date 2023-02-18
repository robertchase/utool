#! /usr/bin/env python3
"""format text into paragraphs"""
import re


# pylint: disable=too-many-branches
def paragraph(data, columns=80, indent=None):
    """yield lines from data that are no more than columns chars long"""

    line = ""
    top = True
    new_paragraph = False

    # pylint: disable=too-many-nested-blocks
    for data_line in data.split("\n"):
        if len(data_line.rstrip()) == 0:
            if not top:
                if line:
                    if new_paragraph:
                        yield ""
                        new_paragraph = False
                    yield f"{' ' * indent}{line}"
                    line = ""
                new_paragraph = True
        else:
            if top:
                if indent is None:
                    indent = len(re.match(r"(\s*)", data_line).group(1))
                top = False
                maxlen = columns - indent
            for word in data_line.split():
                if not line:
                    if len(word) >= maxlen:
                        if new_paragraph:
                            yield ""
                            new_paragraph = False
                        yield f"{' ' * indent}{word}"
                    else:
                        line = word

                elif len(newl := f"{line} {word}") > maxlen:
                    if new_paragraph:
                        yield ""
                        new_paragraph = False
                    yield f"{' ' * indent}{line}"
                    line = word

                else:
                    line = newl

    if line:
        if new_paragraph:
            yield ""
            new_paragraph = False
        yield f"{' ' * indent}{line}"


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="break text into paragraphs")
    parser.add_argument("--columns", "-c", type=int, default=80)
    parser.add_argument("--indent", "-i", type=int, default=None)
    args = parser.parse_args()
    for text in paragraph(sys.stdin.read(), args.columns, args.indent):
        print(text)
