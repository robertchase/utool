"""Create pivot tables from CSV data."""

import argparse
import csv
import io
import sys
from collections import OrderedDict
from decimal import Decimal, InvalidOperation


def parse_sort_suffix(arg: str) -> tuple[str, str | None]:
    """Parse an argument, stripping optional +/- sort suffix.

    arg -- string optionally suffixed with + or -
    returns (base, sort_direction) where sort_direction is
            'asc', 'desc', or None
    """
    if arg.endswith("+"):
        return arg[:-1], "asc"
    if arg.endswith("-"):
        return arg[:-1], "desc"
    return arg, None


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


def _sum_values(values: list[str]) -> str:
    """Sum a list of string values using Decimal, returning a string.

    values -- list of string representations of numbers
    returns string representation of the sum
    """
    total = Decimal(0)
    max_places = 0
    for val in values:
        val = val.strip()
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


TOTAL_HEADER = "Total"
AVG_HEADER = "Avg"


def _avg_values(values: list[str], count: int) -> str:
    """Compute the mean of values over count buckets, treating missing as zero.

    values -- summed cell values for cells that exist
    count -- total number of columns (denominator; missing cells count as 0)
    returns string representation of the mean, always 2 decimal places
    """
    if count == 0:
        return "0.00"
    total = Decimal(0)
    for val in values:
        val = val.strip()
        if not val:
            continue
        try:
            total += Decimal(val)
        except InvalidOperation:
            continue
    return format(total / Decimal(count), ".2f")


def pivot(
    rows: list[dict],
    row_col: str,
    col_col: str,
    val_col: str,
    row_sort: str | None = None,
    col_sort: str | None = None,
    htotal: bool = False,
    htotal_sort: str | None = None,
    vtotal: bool = False,
    avg: bool = False,
    avg_sort: str | None = None,
    summary_only: bool = False,
) -> tuple[list[str], list[dict]]:
    """Build a pivot table from rows.

    rows -- list of dicts (as from csv.DictReader)
    row_col -- column whose values become row labels
    col_col -- column whose unique values become pivot column headers
    val_col -- column whose values fill cells (summed per group)
    row_sort -- 'asc', 'desc', or None to preserve encounter order
    col_sort -- 'asc', 'desc', or None to preserve encounter order
    htotal -- include a Total column summing each row (horizontal)
    htotal_sort -- 'asc', 'desc', or None; if set, sort rows by htotal
                   (overrides row_sort)
    vtotal -- append a Total row summing each column (vertical)
    avg -- include an Avg column with the row mean (missing cells = 0)
    avg_sort -- 'asc', 'desc', or None; if set, sort rows by avg
                (overrides htotal_sort and row_sort)
    summary_only -- omit pivot columns; output only row label + Total/Avg
    returns (fieldnames, pivot_rows) where fieldnames starts with row_col
    """
    # Collect unique row and column values in encounter order
    row_keys: OrderedDict[str, None] = OrderedDict()
    col_keys: OrderedDict[str, None] = OrderedDict()
    cells: dict[tuple[str, str], list[str]] = {}

    for row in rows:
        r = row[row_col]
        c = row[col_col]
        v = row[val_col]
        row_keys[r] = None
        col_keys[c] = None
        cells.setdefault((r, c), []).append(v)

    row_labels = list(row_keys)
    col_labels = list(col_keys)

    if col_sort is not None:
        col_labels.sort(reverse=(col_sort == "desc"))

    fieldnames = [row_col] + col_labels

    pivot_rows: list[dict] = []
    for r in row_labels:
        pivot_row: dict[str, str] = {row_col: r}
        cell_values: list[str] = []
        for c in col_labels:
            vals = cells.get((r, c), [])
            summed = _sum_values(vals) if vals else ""
            pivot_row[c] = summed
            if summed:
                cell_values.append(summed)
        if htotal:
            pivot_row[TOTAL_HEADER] = _sum_values(cell_values)
        if avg:
            pivot_row[AVG_HEADER] = _avg_values(cell_values, len(col_labels))
        pivot_rows.append(pivot_row)

    if htotal:
        fieldnames.append(TOTAL_HEADER)
    if avg:
        fieldnames.append(AVG_HEADER)

    if summary_only:
        summary_cols = [c for c in (TOTAL_HEADER, AVG_HEADER) if c in fieldnames]
        fieldnames = [row_col] + summary_cols
        pivot_rows = [{k: r[k] for k in fieldnames} for r in pivot_rows]

    # Sort rows: avg_sort > htotal_sort > row_sort
    if avg_sort is not None and avg:
        pivot_rows.sort(
            key=lambda r: Decimal(r[AVG_HEADER] or "0"),
            reverse=(avg_sort == "desc"),
        )
    elif htotal_sort is not None and htotal:
        pivot_rows.sort(
            key=lambda r: Decimal(r[TOTAL_HEADER] or "0"),
            reverse=(htotal_sort == "desc"),
        )
    elif row_sort is not None:
        row_labels.sort(reverse=(row_sort == "desc"))
        label_order = {label: i for i, label in enumerate(row_labels)}
        pivot_rows.sort(key=lambda r: label_order[r[row_col]])

    # Append vertical total row after sorting so it stays at the bottom
    if vtotal:
        vtotal_row: dict[str, str] = {row_col: TOTAL_HEADER}
        for c in col_labels:
            if not summary_only:
                vtotal_row[c] = _sum_values([r[c] for r in pivot_rows if r.get(c)])
        if htotal:
            vtotal_row[TOTAL_HEADER] = _sum_values(
                [r[TOTAL_HEADER] for r in pivot_rows if r.get(TOTAL_HEADER)]
            )
        if avg:
            vtotal_row[AVG_HEADER] = ""
        pivot_rows.append(vtotal_row)

    return fieldnames, pivot_rows


def format_table(
    rows: list[dict],
    fieldnames: list[str],
    vtotal: bool = False,
    avg: bool = False,
) -> str:
    """Format rows as a simple aligned table.

    rows -- list of dicts
    fieldnames -- column names in order
    vtotal -- if True, insert a dashed separator before the last row
              (first column blank, remaining columns dashed)
    avg -- if True, leave the Avg column blank in the vtotal separator
    returns formatted table string
    """
    widths = [len(f) for f in fieldnames]
    for row in rows:
        for i, f in enumerate(fieldnames):
            widths[i] = max(widths[i], len(str(row.get(f, ""))))

    header = "  ".join(f.ljust(widths[i]) for i, f in enumerate(fieldnames))
    separator = "  ".join("-" * widths[i] for i in range(len(fieldnames)))
    lines = [header, separator]

    data_rows = rows[:-1] if vtotal and rows else rows
    for row in data_rows:
        line = "  ".join(
            str(row.get(f, "")).ljust(widths[i]) for i, f in enumerate(fieldnames)
        )
        lines.append(line)

    if vtotal and rows:
        vtotal_sep = "  ".join(
            " " * widths[i]
            if i == 0 or (avg and fieldnames[i] == AVG_HEADER)
            else "-" * widths[i]
            for i, _ in enumerate(fieldnames)
        )
        lines.append(vtotal_sep)
        total_row = rows[-1]
        lines.append("  ".join(
            str(total_row.get(f, "")).ljust(widths[i])
            for i, f in enumerate(fieldnames)
        ))

    return "\n".join(lines) + "\n"


def main() -> None:
    """Main handler."""
    parser = argparse.ArgumentParser(
        description="create pivot tables from CSV data"
    )
    parser.add_argument(
        "row_col",
        help="column for row labels (name or 1-indexed number); "
        "suffix with + or - to sort ascending or descending",
    )
    parser.add_argument(
        "col_col",
        help="column for pivot column headers (name or 1-indexed number); "
        "suffix with + or - to sort ascending or descending",
    )
    parser.add_argument(
        "val_col",
        help="column whose values fill cells (summed per group)",
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
        "--total",
        nargs="?",
        const="",
        default=None,
        help="add both a Total column (per row) and a Total row (per column); "
        "use --total+ or --total- to sort rows by row total asc/desc",
    )
    parser.add_argument(
        "--htotal",
        nargs="?",
        const="",
        default=None,
        help="add a Total column summing each row; "
        "use --htotal+ or --htotal- to sort rows by total asc/desc",
    )
    parser.add_argument(
        "--vtotal",
        action="store_true",
        help="append a Total row summing each column",
    )
    parser.add_argument(
        "--avg",
        nargs="?",
        const="",
        default=None,
        help="add an Avg column with the row mean (missing cells count as 0); "
        "use --avg+ or --avg- to sort rows by avg asc/desc",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="omit pivot columns; output only row label plus --total/--avg columns",
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

    # Preprocess argv so --total+/-, --htotal+/-, --avg+/- are recognised by argparse
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg in ("--total+", "--total-"):
            argv[i:i + 1] = ["--total", arg[-1]]
        elif arg in ("--htotal+", "--htotal-"):
            argv[i:i + 1] = ["--htotal", arg[-1]]
        elif arg in ("--avg+", "--avg-"):
            argv[i:i + 1] = ["--avg", arg[-1]]

    args = parser.parse_args(argv)

    in_dialect = "excel-tab" if args.tsv else "excel"
    reader = csv.DictReader(args.file, dialect=in_dialect)
    fieldnames = reader.fieldnames
    if not fieldnames:
        sys.stderr.write("error: input has no headers\n")
        sys.exit(1)

    fnames = list(fieldnames)

    row_raw, row_sort = parse_sort_suffix(args.row_col)
    col_raw, col_sort = parse_sort_suffix(args.col_col)

    row_col = resolve_name(row_raw, fnames)
    col_col = resolve_name(col_raw, fnames)
    val_col = resolve_name(args.val_col, fnames)

    for name in (row_col, col_col, val_col):
        if name not in fieldnames:
            sys.stderr.write(f"error: column '{name}' not found in input\n")
            sys.exit(1)

    rows = list(reader)

    # Parse --total / --htotal with optional +/- suffix
    # --total implies both htotal and vtotal
    def _parse_total_arg(val: str | None) -> tuple[bool, str | None]:
        if val is None:
            return False, None
        return True, ("asc" if val == "+" else "desc" if val == "-" else None)

    use_htotal_from_total, htotal_sort_from_total = _parse_total_arg(args.total)
    use_htotal_from_flag, htotal_sort_from_flag = _parse_total_arg(args.htotal)
    use_htotal = use_htotal_from_total or use_htotal_from_flag
    htotal_sort = htotal_sort_from_total or htotal_sort_from_flag
    use_vtotal = args.vtotal or use_htotal_from_total

    # Parse --avg with optional +/- suffix
    use_avg = args.avg is not None
    avg_sort: str | None = None
    if use_avg and args.avg == "+":
        avg_sort = "asc"
    elif use_avg and args.avg == "-":
        avg_sort = "desc"

    pivot_fnames, pivot_rows = pivot(
        rows, row_col, col_col, val_col, row_sort, col_sort,
        htotal=use_htotal, htotal_sort=htotal_sort,
        vtotal=use_vtotal,
        avg=use_avg, avg_sort=avg_sort,
        summary_only=args.summary_only,
    )

    if args.to_table:
        sys.stdout.write(format_table(pivot_rows, pivot_fnames, vtotal=use_vtotal, avg=use_avg))
    else:
        out_dialect = "excel-tab" if args.to_tsv else "excel"
        out = args.output or sys.stdout
        buf = io.StringIO() if out is sys.stdout else out
        writer = csv.DictWriter(buf, fieldnames=pivot_fnames, dialect=out_dialect)
        writer.writeheader()
        writer.writerows(pivot_rows)
        if out is sys.stdout:
            sys.stdout.write(buf.getvalue())
        if args.output:
            args.output.close()


if __name__ == "__main__":
    main()
