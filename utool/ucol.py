#! /usr/bin/env python3
import re


def split(data, indexes, delimiter=" ", out_delimiter=" ", nullable=False):

    _indexes = []
    for index in indexes:
        if match := re.match(r"(\d+)\+$", index):
            col = int(match.group(1)) - 1
            _indexes.append(f"{col}:")
        else:
            try:
                index = int(index)
            except ValueError:
                raise Exception(f"column number ({index}) must be numeric")
            if index > 0:
                index -= 1
            _indexes.append(index)

    _delimiter = delimiter + "+" if nullable else delimiter
    _delimiter = rf"\{_delimiter}"

    for lineno, line in enumerate(data.splitlines(), start=1):
        cols = re.split(_delimiter, line)
        result = ""
        for index in _indexes:
            if result:
                result += out_delimiter
            try:
                if isinstance(index, str):
                    result += delimiter.join(eval(f"cols[{index}]"))
                else:
                    result += cols[index]
            except IndexError:
                raise Exception(
                    f"column {index} not found on line {lineno}"
                    f':"{line}"')
                raise Exception(f"line '{line}' does not have {index} columns")
        yield result


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="break text into columns")
    parser.add_argument("--delimiter", "-d", default=" ")
    parser.add_argument("--output-delimiter", "-D", default=" ")
    parser.add_argument("--null-columns", "-n", action="store_true")
    parser.add_argument("columns", nargs="+")
    args = parser.parse_args()
    for line in split(
            sys.stdin.read(),
            args.columns,
            args.delimiter,
            args.output_delimiter,
            args.null_columns):
        print(line)
