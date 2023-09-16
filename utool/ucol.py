#! /usr/bin/env python3
"""split text into columns"""
import re


class UcolException(Exception):
    """ucol specific exception"""


def split(data, indexes, delimiter=" ", out_delimiter=" ", nullable=False):
    """split text into columns

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
    out_delimiter - separator between output columns
    nullable - control parsing of multiple delimiters (see delimiter)
    """

    _indexes = []
    for index in indexes:
        if match := re.match(r"(\d+)\+$", index):
            col = int(match.group(1)) - 1
            _indexes.append(f"{col}:")
        else:
            try:
                index = int(index)
            except ValueError as exc:
                raise UcolException(f"column number ({index}) must be numeric") from exc
            if index > 0:
                index -= 1
            _indexes.append(index)

    _delimiter = "\\" + (delimiter + "+" if nullable else delimiter)

    for lineno, line in enumerate(data.splitlines(), start=1):
        if nullable:
            line = line.strip(delimiter)
        cols = re.split(_delimiter, line)
        result = ""
        for index in _indexes:
            if result:
                result += out_delimiter
            try:
                if isinstance(index, str):
                    # pylint: disable-next=eval-used
                    result += delimiter.join(eval(f"cols[{index}]"))
                else:
                    result += cols[index]
            except IndexError as exc:
                raise UcolException(
                    f"line {lineno}:'{line}'" f" does not have {index} columns"
                ) from exc
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
        "--null-columns",
        "-n",
        action="store_true",
        help="allow consecutive empty columns",
    )
    parser.add_argument(
        "columns", nargs="+", help="list of column numbers, e.g. 1 2 -1 5+"
    )
    args = parser.parse_args()
    for response in split(
        sys.stdin.read(),
        args.columns,
        args.delimiter,
        args.output_delimiter,
        not args.null_columns,
    ):
        print(response)
