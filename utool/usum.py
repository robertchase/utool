#! /usr/bin/env python3
"""Sum by column CLI utility"""


class UsumException(Exception):
    """special usum handling"""

    def __init__(self, line, msg):
        self.args = (f"{line=}: {msg}",)


def num(value, strict: bool):
    """Parse number as float or int

    returns (numeric value, precision)
    """
    if not strict:
        value = value.replace("$", "").replace(",", "")
    precision = 0
    try:
        value_float = float(value)
        prec = value.split(".")
        if len(prec) == 2:
            precision = len(prec[1])
        try:
            value_int = int(value)
        except ValueError:
            return value_float, precision
        if value_int == value_float:
            return value_int, 0
        return value_float, precision
    except ValueError:
        if not strict:
            return 0, 0
        raise ValueError(f"could not convert '{value}' to number") from None


def group_by(data, cols, strict: bool = False):
    """Sum data by specified columns

    data -- iterable of lines of data to be summed
    cols -- list of columns numbers that comprise the key (starting at 1)
            (other columns will be summed)
    strict -- if True, expect data to be clean and well-shaped
    """
    groups = {}
    precision = None
    for linenum, line in enumerate(data, start=1):
        toks = line.split()
        if not toks:
            continue
        try:
            key = " ".join(list(toks[i - 1] for i in cols))
            vcols = list(i for i in range(1, len(toks) + 1) if i not in cols)
            values = list(num(toks[i - 1], strict) for i in vcols)
            sums = groups.get(key)
            if sums and len(values) != len(sums):
                raise IndexError(f"number of columns doesn't match {key=}")

            if precision is None:
                precision = [0] * len(values)
            precision = [max(pre, val[1]) for pre, val in zip(precision, values)]

            if sums is None:
                sums = [0] * len(values)
            groups[key] = [sum_ + val[0] for sum_, val in zip(sums, values)]

        except (ValueError, IndexError) as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    for key, sums in groups.items():
        fmt = [f"{{:.{prec}f}}".format(col) for col, prec in zip(sums, precision)]
        groups[key] = fmt

    return groups


def sum_all(data, strict: bool = False):
    """add every number found"""

    total = 0
    precision = 0

    for linenum, line in enumerate(data, start=1):
        if not (toks := line.split()):
            continue
        try:
            for tok in toks:
                value, prec = num(tok, strict)
                total += value
                precision = max(precision, prec)
        except ValueError as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    return f"{{:.{precision}f}}".format(total)


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
            sys.stdout.write(f"{key} {' '.join((n for n in val))}\n")
    else:
        total = sum_all(sys.stdin, args.strict)
        sys.stdout.write(total)


if __name__ == "__main__":
    import argparse
    import sys

    main()
