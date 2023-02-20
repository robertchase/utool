#! /usr/bin/env python3
"""format text into paragraphs"""
import re


def get_indent(indent, lines):
    """derive indent from first non-empty line"""
    if indent is None:
        for line in lines:
            if len(line.strip()):
                indent = len(re.match(r"(\s*)", line).group(1))
                break
    return indent


def get_paragraphs(lines):
    """break lines into paragraphs

    each paragraph is separated by an empty line
    return a list of paragraphs where a paragraph is a list of words
    """
    paras = []
    para = []
    for line in lines:
        if len(line.strip()):
            for word in line.split():
                para.append(word)
        else:
            if para:
                paras.append(para)
                para = []
    if para:
        paras.append(para)
    return paras


def paragraph(data, columns=80, indent=None):
    """yield lines from data that are no more than columns chars long"""

    lines = data.split("\n")
    indent = get_indent(indent, lines)
    paragraphs = get_paragraphs(lines)

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
