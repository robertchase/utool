"""Split text into columns."""

import argparse
import csv
import json
import re
import string
import sys
import typing


class UcolException(Exception):
    """ucol specific exception."""


def remove_comma(val: str) -> str:
    """remove commas and/or leading dollar signs ($) from numeric strings"""
    if re.match(r"(-?\$\d*|\$?\d{1,3}(,\d{3})+)(\.\d+)?$", val):
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


def linesplitter(
    is_csv: bool,
    delimiter: str,
    nullable: bool,
    strip: bool,
) -> typing.Callable[[str], list[str]]:
    """Return a function to split lines."""

    def regex_delimiter(delimiter):
        if delimiter == "^":
            delimiter = r"\^"
        return f"[{delimiter}]"

    if is_csv:

        def _split(line):
            """Use csv module."""
            return next(iter(csv.reader([line])))

    elif nullable and delimiter is None:

        def _split(line):
            """Split on whitespace character."""
            if strip:
                line = line.strip()
            return re.split(r"\s", line)

    elif nullable:
        _delimiter = regex_delimiter(delimiter)

        def _split(line):
            """Split on delimiter character."""
            if strip:
                line = line.strip(delimiter)
            return re.split(_delimiter, line)

    elif delimiter is None:

        def _split(line):
            """Split on whitespace characters."""
            if strip:
                line = line.strip()
            return re.split(r"\s+", line)

    else:
        _delimiter = regex_delimiter(delimiter) + "+"

        def _split(line):
            """Split on delimiter characters."""
            if strip:
                line = line.strip(delimiter)
            return re.split(_delimiter, line)

    return _split


class ColumnSelector:
    """Callable that returns a column by index."""

    def __init__(self, index):
        if index[0] == "_":
            index = f"-{index[1:]}"
        self.index = int(index)
        if self.index > 0:
            self.index -= 1

    def __call__(self, columns: list[str]) -> list[str]:
        return [columns[self.index]]


class ColumnSelectorRange(ColumnSelector):
    """Callable that returns the set of columns beginning with an index."""

    def __call__(self, columns: list[str]) -> list[str]:
        return columns[self.index :]


class ColumnSelectorSlice(ColumnSelector):
    """Callable that returns a substring of a column at index."""

    def __init__(self, index, start, end):
        super().__init__(index)
        if start:
            self.start = int(start)
            if self.start > 0:
                self.start -= 1
        else:
            self.start = None
        if end:
            self.end = int(end)
            if self.end < 0:
                self.end += 1
        else:
            self.end = None

    def __call__(self, columns: list[str]) -> list[str]:
        column = columns[self.index]
        if self.start is None:
            return [column[: self.end]]
        if self.end is None:
            return [column[self.start :]]
        return [column[self.start : self.end]]


def split(  # pylint: disable=too-many-positional-arguments,too-many-arguments
    data: typing.TextIO,
    indexes: list[ColumnSelector],
    delimiter: str | None = None,
    nullable: bool = False,
    strip: bool = True,
    strict: bool = False,
    is_csv: bool = False,
) -> typing.Iterator[list[str]]:
    """Split text into columns.

    data - open file
    indexes - list of ColumnSelectors
    delimiter - separator between input columns
                multiple sequential delimiters will result in multiple
                    empty columns unless nullable=True
                if None, split on whitespace
    nullable - control parsing of multiple delimiters (see delimiter)
    strip - strip leading and trailing delimiters from line
    strict - if True, stop on rows that have too few columns, else skip
    is_csv - if True, parse each line with csv reader
    """
    splitter = linesplitter(is_csv, delimiter, nullable, strip)

    for lineno, line in enumerate(data.splitlines(), start=1):
        cols = splitter(line)
        result = []
        for index in indexes:
            try:
                result.extend(index(cols))
            except IndexError:
                if not strict:
                    result = None
                    break
                raise UcolException(
                    f"line={lineno}:'{line}' does not have enough columns"
                ) from None
        if result:
            yield result


def column_specifier(column: str):
    """Return a ColumnSelector for 'column'.

    The ColumnSelector is a callable that, depending on the value of 'column'
    does one of:

    * if column is a number, the selector will return the numbereth column
      (starting with one)
    * if column is a negative number (starts with a minus (-) or an underscore (_)),
      the selector will select a column starting from the right
    * if column is a number followed by a "+", the selector will select the
      column and all following columns
    * if the column is a number followed by [n,m], the selector will select the
      substring from n to m of the numbereth column (n and m start with 1 when counting
      from the left, or -1 when counting from the right)

      if specifying a negative column number and a [n,m] selector, then an underscore
      (_) must be used instead of a minus sign (-) as a prefix to the column number.
    """

    if re.match(r"[-_]?\d+$", column):
        return ColumnSelector(column)
    if match := re.match(r"(\d+)\+$", column):
        return ColumnSelectorRange(match.group(1))
    if match := re.match(r"(_?\d+)\[(-?\d*)(?:,(-?\d+))?\]$", column):
        index, start, end = match.groups()
        return ColumnSelectorSlice(index, start, end)
    raise argparse.ArgumentTypeError(f"Invalid column specification: {column}")


def main():
    """Main handler."""
    parser = argparse.ArgumentParser(description="select columns from text")
    parser.add_argument(
        "--delimiter",
        "-d",
        default=None,
        help="input column delimiter, default=whitespace",
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
        "--no-strip",
        action="store_true",
        help="don't strip leading and trailing delimiters from line",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="raise error on rows that have too few columns (else skip)",
    )
    parser.add_argument(
        "columns",
        type=column_specifier,
        default=["1+"],
        nargs="*",
        help="list of column numbers, e.g. 1 2 -1 5+ 1[1,5] _2[,7] (default=1+)",
    )
    args = parser.parse_args()
    if args.to_sc:
        args.un_comma = True
    if args.to_json:
        print("[", end="")
    for row_number, response in enumerate(
        split(
            sys.stdin.read(),
            args.columns,
            args.delimiter,
            args.null_columns,
            not args.no_strip,
            args.strict,
            args.csv,
        )
    ):
        if args.un_comma:
            response = [remove_comma(item) for item in response]
        if args.to_json:
            if row_number == 0:
                json_keys = response
            else:
                if row_number > 1:
                    print(",", end="")
                print(json.dumps(dict(zip(json_keys, response, strict=False))), end="")
        elif args.to_sc:
            for sc_line in row_to_sc(response, row_number):
                print(sc_line)
        else:
            print(args.output_delimiter.join(response))
    if args.to_json:
        print("]")


if __name__ == "__main__":
    main()
