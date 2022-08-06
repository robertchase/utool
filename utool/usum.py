#! /usr/bin/env python
"""Sum by column CLI utility"""
import operator


def num(value):
    """Parse number as float or int."""
    value_float = float(value)
    try:
        value_int = int(value)
    except ValueError:
        return value_float
    return value_int if value_int == value_float else value_float


def group_by(data, cols):
    """Sum data by specified columns

        data -- iterable of lines of data to be summed
        cols -- list of columns that comprise the key
                (other columns will be summed)
    """
    groups = {}
    for linenum, line in enumerate(data, start=1):
        toks = line.split()
        if not toks:
            continue
        try:
            names = list(toks[i-1] for i in cols)
            key = ' '.join(names)
            vcols = list(i for i in range(1, len(toks)+1) if i not in cols)
            values = list(num(toks[i-1]) for i in vcols)
            sums = groups.get(key)
            if sums and len(values) != len(sums):
                raise Exception(
                    "number of columns doesnt match key='%s'" % key
                )
        except Exception as err:
            raise Exception('line=%s: %s' % (linenum, str(err)))
        groups[key] = list(map(operator.add, sums, values)) if sums else values
    return groups


def main():
    """Main handler."""
    parser = argparse.ArgumentParser(description='sum group by')
    parser.add_argument('groupby', nargs='+', type=int)
    args = parser.parse_args()

    groups = group_by(sys.stdin, args.groupby)

    for key, val in groups.items():
        sys.stdout.write('%s %s\n' % (key, ' '.join((str(n) for n in val))))


if __name__ == '__main__':
    import argparse
    import sys

    main()
