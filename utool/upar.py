#! /usr/bin/env python3
"""format text into paragraphs"""
import re


# pylint: disable=too-many-branches
def paragraph(data, columns=80, indent=None):
    """yield lines from data that are no more than columns chars long"""

    paragraphs = []
    para = []
    for data_line in data.split("\n"):
        if len(data_line.rstrip()) == 0:
            if para:
                paragraphs.append(para)
                para = []
            continue

        if indent is None:
            indent = len(re.match(r"(\s*)", data_line).group(1))

        for word in data_line.split():
            para.append(word)

    if para:
        paragraphs.append(para)

    maxlen = columns - (indent or 0)
    line = ""
    for paragraph_no, para in enumerate(paragraphs):
        if paragraph_no > 0:
            yield ""
        for word in para:
            if not line and len(word) > maxlen:
                yield f"{' ' * indent}{word}"
            elif not line:
                line = word
            elif len(newline := f"{line} {word}") > maxlen:
                yield f"{' ' * indent}{line}"
                line = word
            else:
                line = newline
        if line:
            yield f"{' ' * indent}{line}"
            line = ""


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="break text into paragraphs")
    parser.add_argument("--columns", "-c", type=int, default=80)
    parser.add_argument("--indent", "-i", type=int, default=None)
    args = parser.parse_args()
    for text in paragraph(sys.stdin.read(), args.columns, args.indent):
        print(text)
