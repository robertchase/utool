"""Sum by column CLI utility"""

import argparse
import collections
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


def group_by(
    data, cols, delim=" ", strict: bool = False, count: bool = False, op: str = "sum"
):
    """Aggregate data by specified columns

    data -- iterable of lines of data to be aggregated
    cols -- list of columns numbers that comprise the key (starting at 1)
            (other columns will be aggregated)
    delim -- column separator
    strict -- if True, expect data to be clean and well-shaped
    count -- if True, prepend list of results with count for each output line
    op -- aggregation operation: "sum", "avg", "min", or "max"
    """
    groups = {}
    counts = collections.Counter()
    precision = None
    for linenum, line in enumerate(data, start=1):
        toks = line.split(delim)
        if not toks:
            continue
        try:
            key = " ".join(list(toks[i - 1] for i in cols))
            vcols = list(i for i in range(1, len(toks) + 1) if i not in cols)
            values = list(num(toks[i - 1], strict) for i in vcols)
            agg = groups.get(key)
            if agg and len(values) != len(agg):
                raise IndexError(f"number of columns doesn't match {key=}")

            if precision is None:
                precision = [0] * len(values)
            precision = [
                max(pre, val[1]) for pre, val in zip(precision, values, strict=False)
            ]

            counts[key] += 1
            if agg is None:
                if op in ("sum", "avg"):
                    agg = [0] * len(values)
                else:  # min, max
                    agg = [val[0] for val in values]
                    groups[key] = agg
                    continue

            if op in ("sum", "avg"):
                groups[key] = [
                    agg_ + val[0] for agg_, val in zip(agg, values, strict=False)
                ]
            elif op == "min":
                groups[key] = [
                    min(agg_, val[0]) for agg_, val in zip(agg, values, strict=False)
                ]
            elif op == "max":
                groups[key] = [
                    max(agg_, val[0]) for agg_, val in zip(agg, values, strict=False)
                ]

        except (ValueError, IndexError) as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    for key, agg in groups.items():
        if op == "avg":
            agg = [val / counts[key] for val in agg]
        fmt = [
            f"{{:.{prec}f}}".format(col)
            for col, prec in zip(agg, precision, strict=False)
        ]
        groups[key] = [str(counts[key]), *fmt] if count else fmt

    return groups


def agg_all(data, delim=" ", strict: bool = False, op: str = "sum"):
    """aggregate every number found"""

    result = None
    count = 0
    precision = 0

    for linenum, line in enumerate(data, start=1):
        if not (toks := line.split(delim)):
            continue
        try:
            for tok in toks:
                value, prec = num(tok, strict)
                precision = max(precision, prec)
                count += 1
                if result is None:
                    result = value
                elif op == "sum" or op == "avg":
                    result += value
                elif op == "min":
                    result = min(result, value)
                elif op == "max":
                    result = max(result, value)
        except ValueError as err:
            if strict:
                raise UsumException(linenum, str(err)) from None

    if result is None:
        result = 0
    elif op == "avg" and count > 0:
        result = result / count

    return f"{{:.{precision}f}}".format(result)


def main():
    """Main handler."""
    parser = argparse.ArgumentParser(description="aggregate columns with group by")
    parser.add_argument("groupby", nargs="*", type=int)
    parser.add_argument(
        "--delimiter",
        "-d",
        default=" ",
        help="input/output column delimiter, default=' '",
    )
    parser.add_argument(
        "--count",
        "-c",
        action="store_true",
        help="add count of items included in result for each output line",
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="error on non-numeric values or mis-matched column counts",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input file (default=stdin)",
    )
    op_group = parser.add_mutually_exclusive_group()
    op_group.add_argument(
        "--avg",
        action="store_const",
        const="avg",
        dest="op",
        help="compute average instead of sum",
    )
    op_group.add_argument(
        "--min",
        action="store_const",
        const="min",
        dest="op",
        help="compute minimum instead of sum",
    )
    op_group.add_argument(
        "--max",
        action="store_const",
        const="max",
        dest="op",
        help="compute maximum instead of sum",
    )

    args = parser.parse_args()
    op = args.op or "sum"
    if args.groupby:
        if len(args.groupby) == 1 and args.groupby[0] == 0:
            args.groupby = []
        groups = group_by(
            args.file, args.groupby, args.delimiter, args.strict, args.count, op
        )
        if args.groupby:
            for key, val in groups.items():
                line = args.delimiter.join(n for n in val)
                sys.stdout.write(f"{key}{args.delimiter}{line}\n")
        else:
            _, val = next(iter(groups.items()))
            sys.stdout.write(args.delimiter.join(n for n in val) + "\n")
    else:
        result = agg_all(args.file, args.delimiter, args.strict, op)
        sys.stdout.write(result + "\n")


if __name__ == "__main__":
    main()
