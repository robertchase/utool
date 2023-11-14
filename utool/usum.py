#! /usr/bin/env python3
"""Sum by column CLI utility"""
import operator


class UsumException(Exception):
    """special usum handling"""

    def __init__(self, line, msg):
        self.args = (f"{line=}: {msg}",)


def num(value, strict: bool):
    """Parse number as float or int."""
    if not strict:
        value = value.replace("$", "").replace(",", "")
    try:
        value_float = float(value)
        try:
            value_int = int(value)
        except ValueError:
            return value_float
        return value_int if value_int == value_float else value_float
    except ValueError:
        if not strict:
            return 0
        raise ValueError(f"could not convert '{value}' to number") from None


def group_by(data, cols, strict: bool = False):
    """Sum data by specified columns

    data -- iterable of lines of data to be summed
    cols -- list of columns that comprise the key
            (other columns will be summed)
    strict -- if True, expect data to be clean and well-shaped
    """
    groups = {}
    for linenum, line in enumerate(data, start=1):
        toks = line.split()
        if not toks:
            continue
        try:
            names = list(toks[i - 1] for i in cols)
            key = " ".join(names)
            vcols = list(i for i in range(1, len(toks) + 1) if i not in cols)
            values = list(num(toks[i - 1], strict) for i in vcols)
            sums = groups.get(key)
            if sums and len(values) != len(sums):
                raise IndexError(f"number of columns doesn't match {key=}")
            groups[key] = list(map(operator.add, sums, values)) if sums else values
        except (ValueError, IndexError) as err:
            if strict:
                raise UsumException(linenum, str(err)) from None
    return groups


def sum_all(data, strict: bool = False):
    """add every number found"""

    total = 0

    for linenum, line in enumerate(data, start=1):
        if not (toks := line.split()):
            continue
        try:
            total += sum(num(tok, strict) for tok in toks)
        except ValueError as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    return total


def main():
    """Main handler."""
    parser = argparse.ArgumentParser(description="sum group by")
    parser.add_argument("groupby", nargs="*", type=int)
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="error on non-numeric values or mis-matched column counts",
    )

    args = parser.parse_args()
    if args.groupby:
        if len(args.groupby) == 1 and args.groupby[0] == 0:
            args.groupby = []
        groups = group_by(sys.stdin, args.groupby, args.strict)
        for key, val in groups.items():
            sys.stdout.write(f"{key} {' '.join((str(n) for n in val))}\n")
    else:
        total = sum_all(sys.stdin, args.strict)
        sys.stdout.write(str(total))


if __name__ == "__main__":
    import argparse
    import sys

    main()
