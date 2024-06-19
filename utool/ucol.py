#! /usr/bin/env python3
"""Split text into columns."""
import csv
import re


class UcolException(Exception):
    """ucol specific exception."""


class ColRange:  # pylint: disable=too-few-public-methods
    """represent a range of columns starting at 'start'"""

    def __init__(self, start: int):
        self.start = start


def parse_indexes(indexes):
    """normalize specified indexes"""
    _indexes = []
    for index in indexes:
        if match := re.match(r"(\d+)\+$", index):
            col = ColRange(int(match.group(1)) - 1)
            _indexes.append(col)
        else:
            try:
                index = int(index)
            except ValueError as exc:
                raise UcolException(f"column number ({index}) must be numeric") from exc
            if index > 0:
                index -= 1
            _indexes.append(index)
    return _indexes


def split(  # pylint: disable=too-many-arguments
    data,
    indexes,
    delimiter=" ",
    nullable=False,
    strict=False,
    is_csv=False,
):
    """Split text into columns.

    data - open file
    indexes - list of column numbers to extract from each line in data
              these can be:
                  integer (first column is "1", second is "2", etc)
                  negative integer (count from right)
                  <integer>+ (all columns including and after "integer")
              columns can repeat and be in any order
    delimiter - separator between input columns
                multiple sequential delimiters will result in multiple
                empty columns unless nullable=True
    nullable - control parsing of multiple delimiters (see delimiter)
    strict - if True, stop on rows that have too few columns, else skip
    is_csv - if True, parse each line with csv reader
    """
    indexes = parse_indexes(indexes)

    if not is_csv:
        _delimiter = "\\" + (delimiter + "+" if nullable else delimiter)

    for lineno, line in enumerate(data.splitlines(), start=1):
        if nullable:
            line = line.strip(delimiter)
        if is_csv:
            cols = list(csv.reader([line]))[0]
        else:
            cols = re.split(_delimiter, line)
        result = []
        for index in indexes:
            try:
                if isinstance(index, ColRange):
                    result.extend(cols[index.start :])
                else:
                    result.append(cols[index])
            except IndexError:
                if not strict:
                    result = None
                    break
                raise UcolException(
                    f"line={lineno}:'{line}' does not have enough columns"
                ) from None
        if result:
            yield result


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="select columns from text")
    parser.add_argument(
        "--delimiter", "-d", default=" ", help="input column delimiter, default=' '"
    )
    parser.add_argument(
        "--output-delimiter",
        "-D",
        default=" ",
        help='output column delimiter, default=" "',
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="handle commas, quotes, and escapes like a csv file",
    )
    parser.add_argument(
        "--null-columns",
        "-n",
        action="store_true",
        help="consecutive delimiters indicate multiple columns",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="raise error on rows that have too few columns (else skip)",
    )
    parser.add_argument(
        "columns", nargs="+", help="list of column numbers, e.g. 1 2 -1 5+"
    )
    args = parser.parse_args()
    for response in split(
        sys.stdin.read(),
        args.columns,
        args.delimiter,
        not args.null_columns,
        args.strict,
        args.csv,
    ):
        print(args.output_delimiter.join(response))
