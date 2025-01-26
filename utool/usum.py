"""Sum by column CLI utility"""

import argparse
import sys
import re


class UsumException(Exception):
    """special usum handling"""

    def __init__(self, line, msg):
        self.args = (f"{line=}: {msg}",)


def num(value, strict: bool) -> tuple[int | float, int]:
    """Parse number as float or int

    returns (numeric value, precision)
    """
    if not strict:
        if re.match(r"-?(\$\d*|\$?\d{1,3}(,\d{3})+)(\.\d+)?$", value):
            value = value.replace("$", "").replace(",", "")
    precision = 0
    try:
        value_float = float(value)
        parts = value.split(".")
        if len(parts) == 2:
            precision = len(parts[1].strip())
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


def group_by(data, cols, delim=" ", strict: bool = False):
    """Sum data by specified columns

    data -- iterable of lines of data to be summed
    cols -- list of columns numbers that comprise the key (starting at 1)
            (other columns will be summed)
    delim -- column separator
    strict -- if True, expect data to be clean and well-shaped
    """
    groups = {}
    precision = None
    for linenum, line in enumerate(data, start=1):
        toks = line.split(delim)
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
            precision = [
                max(pre, val[1]) for pre, val in zip(precision, values, strict=False)
            ]

            if sums is None:
                sums = [0] * len(values)
            groups[key] = [
                sum_ + val[0] for sum_, val in zip(sums, values, strict=False)
            ]

        except (ValueError, IndexError) as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    for key, sums in groups.items():
        fmt = [
            f"{{:.{prec}f}}".format(col)
            for col, prec in zip(sums, precision, strict=False)
        ]
        groups[key] = fmt

    return groups


def sum_all(data, delim=" ", strict: bool = False):
    """add every number found"""

    total = 0
    precision = 0

    for linenum, line in enumerate(data, start=1):
        if not (toks := line.split(delim)):
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
        "--delimiter",
        "-d",
        default=" ",
        help="input/output column delimiter, default=' '",
    )
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
        groups = group_by(sys.stdin, args.groupby, args.delimiter, args.strict)
        if args.groupby:
            for key, val in groups.items():
                line = args.delimiter.join(n for n in val)
                sys.stdout.write(f"{key}{args.delimiter}{line}\n")
        else:
            _, val = next(iter(groups.items()))
            sys.stdout.write(args.delimiter.join(n for n in val))
    else:
        total = sum_all(sys.stdin, args.delimiter, args.strict)
        sys.stdout.write(total)


if __name__ == "__main__":
    main()
