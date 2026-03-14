"""Suppress repeated values in CSV columns"""

import argparse
import csv
import io
import sys


def parse_spec(spec: str) -> tuple[str, list[str]]:
    """Parse a suppress spec like 'column:key1,key2' into (column, [keys]).

    spec -- string in the format 'column:key1,key2'
    returns (column_name, [key_column_names])
    """
    if ":" not in spec:
        raise ValueError(
            f"invalid suppress spec '{spec}', expected format: column:key1,key2"
        )
    col, keys_str = spec.split(":", 1)
    keys = [k.strip() for k in keys_str.split(",")]
    return col.strip(), keys


def suppress(rows: list[dict], specs: list[tuple[str, list[str]]]) -> list[dict]:
    """Suppress repeated column values within groups in sorted data.

    rows -- list of dicts (as from csv.DictReader)
    specs -- list of (column, [key_columns]) tuples; for each spec,
             the column value is blanked on every row except the first
             in each group defined by the key columns
    returns modified list of dicts
    """
    prev_keys: dict[str, tuple[str, ...]] = {}

    for row in rows:
        for col, keys in specs:
            current = tuple(row[k] for k in keys)
            if current == prev_keys.get(col):
                row[col] = ""
            else:
                prev_keys[col] = current

    return rows


def format_table(rows: list[dict], fieldnames: list[str]) -> str:
    """Format rows as a simple aligned table.

    rows -- list of dicts
    fieldnames -- column names in order
    returns formatted table string
    """
    widths = [len(f) for f in fieldnames]
    for row in rows:
        for i, f in enumerate(fieldnames):
            widths[i] = max(widths[i], len(str(row[f])))

    header = "  ".join(f.ljust(widths[i]) for i, f in enumerate(fieldnames))
    separator = "  ".join("-" * widths[i] for i in range(len(fieldnames)))
    lines = [header, separator]
    for row in rows:
        line = "  ".join(str(row[f]).ljust(widths[i]) for i, f in enumerate(fieldnames))
        lines.append(line)

    return "\n".join(lines) + "\n"


def main() -> None:
    """Main handler."""
    parser = argparse.ArgumentParser(
        description="suppress repeated values in CSV columns"
    )
    parser.add_argument(
        "suppress",
        nargs="+",
        help="suppress spec: 'column:key1,key2' — blanks column on duplicate group rows",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input file (default=stdin)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default=None,
        help="output file (default=stdout)",
    )
    parser.add_argument(
        "-t",
        "--table",
        action="store_true",
        help="display output as a formatted table instead of CSV",
    )

    args = parser.parse_args()

    specs = [parse_spec(s) for s in args.suppress]

    reader = csv.DictReader(args.file)
    fieldnames = reader.fieldnames
    if not fieldnames:
        sys.stderr.write("error: CSV has no headers\n")
        sys.exit(1)

    for col, keys in specs:
        for name in [col, *keys]:
            if name not in fieldnames:
                sys.stderr.write(f"error: column '{name}' not found in CSV\n")
                sys.exit(1)

    rows = suppress(list(reader), specs)

    if args.table:
        sys.stdout.write(format_table(rows, list(fieldnames)))
    else:
        out = args.output or sys.stdout
        buf = io.StringIO() if out is sys.stdout else out
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        if out is sys.stdout:
            sys.stdout.write(buf.getvalue())
        if args.output:
            args.output.close()


if __name__ == "__main__":
    main()
