#! /usr/bin/env python3
"""Split text into columns."""
import csv
import json
import re
import typing
import string


class UcolException(Exception):
    """ucol specific exception."""


class ColRange:  # pylint: disable=too-few-public-methods
    """represent a range of columns starting at 'start'"""

    def __init__(self, start: int):
        self.start = start


def remove_comma(val: str) -> str:
    """remove commas and/or leading dollar signs ($) from numeric strings"""
    if re.match(r"(\$\d*|\$?\d{1,3}(,\d{3})+)(\.\d+)?$", val):
        return val.replace("$", "").replace(",", "")
    return val


def as_alpha(value: int) -> str:
    """turn decimal number into alpha (base 26)"""
    base = len(string.ascii_uppercase)
    parts = ""
    while base < value:
        parts = string.ascii_uppercase[value % base - 1] + parts
        value = value // base
    return string.ascii_uppercase[value - 1] + parts


def row_to_sc(row: list[str], row_num: int) -> typing.Iterator[str]:
    """generate lines for a spreadsheet calculator using values in row"""
    for col_number, cell in enumerate(row, start=1):
        cell_number = f"{as_alpha(col_number)}{row_num}"
        try:
            float(cell)
            yield f"let {cell_number} = {cell}"
        except ValueError:
            yield f'leftstring {cell_number} = "{cell}"'


def parse_indexes(indexes: list[str]) -> list[int | ColRange]:
    """normalize column indexes"""
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
    data: typing.TextIO,
    indexes: list[str],
    delimiter: str = " ",
    nullable: bool = False,
    strict: bool = False,
    is_csv: bool = False,
) -> typing.Iterator[list[str]]:
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
        help="parse data as csv",
    )
    parser.add_argument(
        "--un-comma",
        action="store_true",
        help="remove commas and/or leading dollar sign ($) from numbers",
    )
    parser.add_argument(
        "--to-json",
        action="store_true",
        help="output as json (list of dict) using first row as keys",
    )
    parser.add_argument(
        "--to-sc",
        action="store_true",
        help="output as sc (spreadsheet calculator) file (enables un-comma)",
    )
    parser.add_argument(
        "--null-columns",
        "-n",
        action="store_true",
        help="consecutive delimiters indicate multiple columns (default=False)",
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
    if args.to_sc:
        args.un_comma = True
    if args.to_json:
        json_result = []
    for row_number, response in enumerate(
        split(
            sys.stdin.read(),
            args.columns,
            args.delimiter,
            not args.null_columns,
            args.strict,
            args.csv,
        )
    ):
        if args.un_comma:
            response = [remove_comma(item) for item in response]
        if args.to_json:
            if json_result:
                json_result.append(dict(zip(json_result[0], response)))
            else:
                json_result.append(response)
        elif args.to_sc:
            for sc_line in row_to_sc(response, row_number):
                print(sc_line)
        else:
            print(args.output_delimiter.join(response))
    if args.to_json:
        print(json.dumps(json_result[1:]))
