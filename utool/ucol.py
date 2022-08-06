#! /usr/bin/env python3
import re


def split(data, indexes, delimiter=" ", out_delimiter=" ", nullable=False):
    if nullable:
        delimiter = delimiter + "+"
    delimiter = rf"\{delimiter}"
    for lineno, line in enumerate(data.splitlines(), start=1):
        cols = re.split(delimiter, line)
        result = ""
        for index in indexes:
            if result:
                result += out_delimiter
            try:
                result += cols[index if index < 0 else index - 1]
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
    columns = [int(col) for col in args.columns]
    for line in split(
            sys.stdin.read(),
            columns,
            args.delimiter,
            args.output_delimiter,
            args.null_columns):
        print(line)
