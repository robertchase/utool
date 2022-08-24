#! /usr/bin/env python3
"""Average for set of numbers CLI utility"""
import statistics


def to_num(value):
    """parse number as float or int"""
    value_float = float(value)
    try:
        value_int = int(value)
    except ValueError:
        return value_float
    return value_int if value_int == value_float else value_float


def to_list(data):
    """return a list of numbers from iterable lines of data"""
    numbers = []
    for linenum, line in enumerate(data, start=1):
        if toks := line.split():
            try:
                if len(toks) != 1:
                    raise Exception("Too many values on line")
                numbers.append(to_num(toks[0]))
            except Exception as err:
                raise Exception('line=%s: %s' % (linenum, str(err)))
    return numbers


if __name__ == '__main__':
    import sys

    numbers = to_list(sys.stdin)
    sys.stdout.write(
        f"{statistics.mean(numbers)}"
        f" {statistics.quantiles(numbers)}"
        f" t={sum(numbers)} n={len(numbers)}"
    )
