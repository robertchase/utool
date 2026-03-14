"""Insert break rows and totals into CSV data."""

import argparse
import csv
import io
import sys
from decimal import Decimal, InvalidOperation


def parse_break_spec(spec: str) -> tuple[list[str], list[str]]:
    """Parse a break spec like 'col1,col2:total1,total2' into ([break_cols], [subtotal_cols]).

    spec -- string in the format 'break_col[,break_col...][:subtotal_col[,subtotal_col...]]'
    returns ([break_column_names], [subtotal_column_names])
    """
    if ":" in spec:
        break_str, total_str = spec.split(":", 1)
        break_cols = [c.strip() for c in break_str.split(",")]
        subtotal_cols = [c.strip() for c in total_str.split(",")]
    else:
        break_cols = [c.strip() for c in spec.split(",")]
        subtotal_cols = []

    if not break_cols or break_cols == [""]:
        raise ValueError(
            f"invalid break spec '{spec}', at least one break column required"
        )

    return break_cols, subtotal_cols


def resolve_name(name: str, fieldnames: list[str]) -> str:
    """Resolve a single column reference to a header name.

    name -- column name or 1-indexed integer
    fieldnames -- list of CSV column names
    returns resolved column name
    """
    try:
        index = int(name)
    except ValueError:
        return name
    if index < 1 or index > len(fieldnames):
        raise ValueError(
            f"column index {index} out of range (1-{len(fieldnames)})"
        )
    return fieldnames[index - 1]


def resolve_break_spec(
    spec: tuple[list[str], list[str]], fieldnames: list[str]
) -> tuple[list[str], list[str]]:
    """Resolve numeric column references in a break spec.

    spec -- ([break_cols], [subtotal_cols]) from parse_break_spec
    fieldnames -- list of CSV column names
    returns ([resolved_break_cols], [resolved_subtotal_cols])
    """
    break_cols, subtotal_cols = spec
    return (
        [resolve_name(c, fieldnames) for c in break_cols],
        [resolve_name(c, fieldnames) for c in subtotal_cols],
    )


def _sum_col(rows: list[dict], col: str) -> str:
    """Sum a column across rows, returning a string.

    rows -- list of dicts
    col -- column name to sum
    returns string representation of the sum
    """
    total = Decimal(0)
    max_places = 0
    for row in rows:
        val = row[col].strip()
        if not val:
            continue
        try:
            d = Decimal(val)
        except InvalidOperation:
            continue
        total += d
        _, _, exponent = d.as_tuple()
        if isinstance(exponent, int) and exponent < 0:
            max_places = max(max_places, -exponent)

    if max_places > 0:
        fmt = f".{max_places}f"
        return format(total, fmt)
    return str(total)


def insert_breaks(
    rows: list[dict],
    break_cols: list[str],
    subtotal_cols: list[str],
    fieldnames: list[str],
) -> list[dict]:
    """Insert break rows when break columns change value.

    rows -- list of dicts (as from csv.DictReader)
    break_cols -- columns that define group boundaries
    subtotal_cols -- columns to sum in break rows (may be empty)
    fieldnames -- all column names
    returns new list of dicts with break rows inserted
    """
    if not rows:
        return []

    result: list[dict] = []
    group_rows: list[dict] = []
    prev_key: tuple[str, ...] | None = None

    for row in rows:
        current_key = tuple(row[c] for c in break_cols)
        if prev_key is not None and current_key != prev_key:
            result.extend(group_rows)
            result.append(_make_break_row(group_rows, subtotal_cols, fieldnames))
            group_rows = []
        group_rows.append(row)
        prev_key = current_key

    result.extend(group_rows)
    if len(rows) > 0:
        result.append(_make_break_row(group_rows, subtotal_cols, fieldnames))

    return result


def _make_break_row(
    group_rows: list[dict],
    subtotal_cols: list[str],
    fieldnames: list[str],
) -> dict:
    """Create a break row for a group.

    group_rows -- rows in the current group
    subtotal_cols -- columns to sum
    fieldnames -- all column names
    returns a dict with subtotal values (or all blanks if no subtotal_cols)
    """
    break_row = {f: "" for f in fieldnames}
    for col in subtotal_cols:
        break_row[col] = _sum_col(group_rows, col)
    return break_row


def append_total(
    rows: list[dict],
    total_cols: list[str],
    fieldnames: list[str],
) -> list[dict]:
    """Append a grand total row to the end of rows.

    rows -- list of dicts (may include break rows)
    total_cols -- columns to sum for grand total
    fieldnames -- all column names
    returns rows with grand total row appended
    """
    # Sum only data rows (non-break rows = rows that have at least one non-empty
    # value in a non-total column). Simpler: sum ALL rows including break rows
    # would double-count. Instead, collect original data rows before breaks were
    # inserted. We solve this by summing from the original rows passed to main().
    # This function receives original (pre-break) rows.
    total_row = {f: "" for f in fieldnames}
    for col in total_cols:
        total_row[col] = _sum_col(rows, col)
    return total_row


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
        line = "  ".join(
            str(row[f]).ljust(widths[i]) for i, f in enumerate(fieldnames)
        )
        lines.append(line)

    return "\n".join(lines) + "\n"


def main() -> None:
    """Main handler."""
    parser = argparse.ArgumentParser(
        description="insert break rows and totals into CSV data"
    )
    parser.add_argument(
        "breaks",
        nargs="?",
        default=None,
        help="break spec: 'break_col[,break_col...][:subtotal_col[,subtotal_col...]]'. "
        "columns can be names or 1-indexed numbers",
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
        "-s",
        "--sort",
        action="store_true",
        help="sort rows by break columns before processing",
    )
    parser.add_argument(
        "--total",
        default=None,
        help="comma-separated columns to include in a grand total row",
    )
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="read input as TSV instead of CSV",
    )
    parser.add_argument(
        "-t",
        "--to-table",
        action="store_true",
        help="display output as a formatted table",
    )
    parser.add_argument(
        "--to-tsv",
        action="store_true",
        help="write output as TSV instead of CSV",
    )

    args = parser.parse_args()

    if args.breaks is None and args.total is None:
        sys.stderr.write("error: must specify a break spec or --total (or both)\n")
        sys.exit(1)

    in_dialect = "excel-tab" if args.tsv else "excel"
    reader = csv.DictReader(args.file, dialect=in_dialect)
    fieldnames = reader.fieldnames
    if not fieldnames:
        sys.stderr.write("error: input has no headers\n")
        sys.exit(1)

    fnames = list(fieldnames)

    # Parse and resolve break spec
    break_cols: list[str] = []
    subtotal_cols: list[str] = []
    if args.breaks is not None:
        parsed_spec = parse_break_spec(args.breaks)
        break_cols, subtotal_cols = resolve_break_spec(parsed_spec, fnames)
        for name in [*break_cols, *subtotal_cols]:
            if name not in fieldnames:
                sys.stderr.write(f"error: column '{name}' not found in input\n")
                sys.exit(1)

    # Parse and resolve total columns
    total_cols: list[str] = []
    if args.total is not None:
        total_cols = [
            resolve_name(c.strip(), fnames) for c in args.total.split(",")
        ]
        for name in total_cols:
            if name not in fieldnames:
                sys.stderr.write(f"error: column '{name}' not found in input\n")
                sys.exit(1)

    rows = list(reader)

    if args.sort and break_cols:
        rows.sort(key=lambda r: tuple(r[c] for c in break_cols))

    # Keep original rows for grand total (before break rows are inserted)
    original_rows = rows

    if break_cols:
        rows = insert_breaks(rows, break_cols, subtotal_cols, fnames)

    if total_cols:
        total_row = append_total(original_rows, total_cols, fnames)
        rows.append(total_row)

    if args.to_table:
        sys.stdout.write(format_table(rows, fnames))
    else:
        out_dialect = "excel-tab" if args.to_tsv else "excel"
        out = args.output or sys.stdout
        buf = io.StringIO() if out is sys.stdout else out
        writer = csv.DictWriter(buf, fieldnames=fnames, dialect=out_dialect)
        writer.writeheader()
        writer.writerows(rows)
        if out is sys.stdout:
            sys.stdout.write(buf.getvalue())
        if args.output:
            args.output.close()


if __name__ == "__main__":
    main()
