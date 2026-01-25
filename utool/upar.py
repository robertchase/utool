"""format text into paragraphs"""

import argparse
import re
import sys


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


def paragraph(data, columns=80, indent=None, hanging=0, prefix=""):
    """yield lines from data that are no more than columns chars long

    data -- text to format
    columns -- maximum line length
    indent -- number of spaces to indent each line (default: derive from first line)
    hanging -- additional indent for continuation lines (default: 0)
    prefix -- string to prepend to each line (default: "")
    """

    lines = data.split("\n")
    indent = get_indent(indent, lines)
    paragraphs = get_paragraphs(lines)

    indent_str = " " * (indent or 0)
    hanging_str = " " * hanging
    maxlen = columns - (indent or 0) - len(prefix)
    maxlen_continuation = maxlen - hanging

    line = ""
    for paragraph_no, para in enumerate(paragraphs):
        if paragraph_no > 0:
            yield ""
        first_line = True
        for word in para:
            effective_maxlen = maxlen if first_line else maxlen_continuation
            if not line:
                if len(word) > effective_maxlen:
                    if first_line:
                        yield f"{prefix}{indent_str}{word}"
                    else:
                        yield f"{prefix}{indent_str}{hanging_str}{word}"
                    first_line = False
                else:
                    line = word
            elif len(newline := f"{line} {word}") > effective_maxlen:
                if first_line:
                    yield f"{prefix}{indent_str}{line}"
                    first_line = False
                else:
                    yield f"{prefix}{indent_str}{hanging_str}{line}"
                line = word
            else:
                line = newline
        if line:
            if first_line:
                yield f"{prefix}{indent_str}{line}"
            else:
                yield f"{prefix}{indent_str}{hanging_str}{line}"
            line = ""


def main():
    """Main handler."""
    parser = argparse.ArgumentParser(description="break text into paragraphs")
    parser.add_argument("--length", "-l", type=int, default=80)
    parser.add_argument("--indent", "-i", type=int, default=None)
    parser.add_argument(
        "--hanging",
        "-H",
        type=int,
        default=0,
        help="additional indent for continuation lines (default: 0)",
    )
    parser.add_argument(
        "--prefix",
        "-p",
        type=str,
        default="",
        help="string to prepend to each line (default: none)",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input file (default: stdin)",
    )
    args = parser.parse_args()
    for text in paragraph(
        args.file.read(), args.length, args.indent, args.hanging, args.prefix
    ):
        print(text)


if __name__ == "__main__":
    main()
