# Design: `uqfx` — QFX/OFX to CSV

## Purpose

Read a QFX (Quicken Financial Exchange) or OFX (Open Financial Exchange)
file and emit its transactions as CSV. Composable with the rest of the
`utool` suite (`ucol`, `usum`, `ubrk`, `upvt`, `usup`).

## Non-goals

- Account reconciliation, balance tracking, running totals
- Writing QFX (export only — we're strictly an importer)
- Multi-statement / multi-account merge semantics (error on > 1)

## Modes

The default mode emits the bank/credit-card schema (`FIELDS`). An
`--investments` flag switches to a wider investment schema
(`INV_FIELDS`) covering `BUYSTOCK`, `BUYMF`, `BUYDEBT`, `BUYOPT`,
`BUYOTHER`, `SELLSTOCK`, `SELLMF`, `SELLDEBT`, `SELLOPT`, `SELLOTHER`,
`INCOME`, `REINVEST`, `TRANSFER`, and `INVBANKTRAN` (cash transactions
in an investment account).

Investment schema columns:
`date, type, subtype, security, units, unit_price, commission, fees, total, memo, fitid`

- `type` — wrapper tag name (`BUYSTOCK`, `INCOME`, `INVBANKTRAN`, …)
- `subtype` — `BUYTYPE` / `SELLTYPE` / `INCOMETYPE` (or `TRNTYPE` for `INVBANKTRAN`)
- `security` — `SECID/UNIQUEID` (CUSIP or ticker)
- `INVBANKTRAN` rows have empty security/units/unit_price/commission/fees

A bank-statement file in `--investments` mode returns no rows (rather
than raising). An investment-statement file in default mode raises with
a message pointing at `--investments`.

## Input formats

QFX is a bank-proprietary extension of OFX. Two wire formats:

- **OFX 1.x** — SGML-like. A plain-text header of `KEY:VALUE` lines, a
  blank line, then markup that *looks* like XML but has unclosed tags
  (leaf tags like `<TRNAMT>-12.34` are common — no `</TRNAMT>`). A
  standard XML parser will reject this.
- **OFX 2.x** — well-formed XML with an `<?xml ...?>` declaration and
  an `<?OFX ... ?>` processing instruction.

The tool must accept both.

### Detection

Sniff the first ~200 bytes:
- starts with `<?xml` → OFX 2.x, use `xml.etree.ElementTree`
- starts with `OFXHEADER:` or similar → OFX 1.x, use regex extraction

## Parsing approach

### OFX 2.x

`xml.etree.ElementTree.fromstring()` on the body. Walk to all `<STMTTRN>`
(and `<CCSTMTTRN>`, same shape) elements regardless of their wrapping
statement container.

### OFX 1.x

Don't try to parse the full document. Instead:

1. Skip the header (everything up to the first blank line, then
   everything up to the first `<OFX>` tag).
2. Find each `<STMTTRN>…</STMTTRN>` block with a multiline regex.
3. Within each block, extract fields with per-field regexes of the
   form `<TAG>value` where `value` ends at the next `<` or end-of-line.

This is uglier than a real parser but matches what real QFX files
actually emit. Tags are always uppercase in OFX 1.x. Values are
whitespace-stripped.

## Transaction fields

The tool extracts this fixed set from each `<STMTTRN>`:

| output column | OFX tag       | notes                                         |
|---------------|---------------|-----------------------------------------------|
| `date`        | `DTPOSTED`    | normalized to `YYYY-MM-DD`                    |
| `amount`      | `TRNAMT`      | Decimal string, negative for debits           |
| `type`        | `TRNTYPE`     | `DEBIT`, `CREDIT`, `CHECK`, `XFER`, etc.      |
| `payee`       | `NAME`        | falls back to empty                           |
| `memo`        | `MEMO`        | empty if absent                               |
| `check`       | `CHECKNUM`    | empty unless `TRNTYPE=CHECK`                  |
| `fitid`       | `FITID`       | bank's unique id for the transaction          |

Other fields seen in the wild that we ignore for v1: `PAYEEID`,
`REFNUM`, `CATEGORY`, `SIC`, `CORRECTFITID`.

### Date normalization

OFX dates are `YYYYMMDD[HHMMSS[.XXX][offset]]`. We take the first 8
characters and format as `YYYY-MM-DD`. We do not preserve time or
timezone — most financial workflows are date-granular and the time
component is noise.

### Amount

Preserve the raw string (Decimal-compatible). Don't reformat. Lets the
user hand it to `usum`, `ubrk`, or `upvt` which use Decimal arithmetic.

## Output

Default: CSV to stdout with header row `date,amount,type,payee,memo,check,fitid`.

Flags follow the existing convention:
- `-f FILE` / `--file` — input QFX/OFX file (default stdin)
- `-o FILE` / `--output` — output file (default stdout)
- `-t` / `--to-table` — formatted table output
- `--to-tsv` — tab-separated output

### Column selection (optional v1.1)

Not v1: pass-through positional args to select/reorder fields
(matching `ucol`'s shape). For v1, always emit the full field set and
let users pipe to `ucol` if they want to trim or reorder.

## File layout

```
utool/uqfx.py           — all logic + CLI
tests/test_uqfx.py      — unit tests
design/uqfx.md          — this file
```

Fits the flat `utool/*.py` pattern of the other tools (no `logic/`
subdirectory — this project predates that convention).

## Public API (for testability)

```python
def parse_header(data: str) -> tuple[str, str]:
    """Split OFX text into (header, body)."""

def detect_version(data: str) -> str:
    """Return '1.x' or '2.x'."""

def extract_transactions(data: str) -> list[dict]:
    """Return normalized transaction dicts with the fixed field set."""

def normalize_date(ofx_date: str) -> str:
    """YYYYMMDD[HHMMSS...] → YYYY-MM-DD."""

FIELDS = ["date", "amount", "type", "payee", "memo", "check", "fitid"]
```

`main()` wires argparse → `extract_transactions()` → `csv.DictWriter`
or `format_table()`.

## Error handling

- Empty input → error to stderr, exit 1
- No `<STMTTRN>` blocks found → empty output, exit 0 (not an error; a
  statement with zero transactions is valid)
- Malformed transaction (missing `DTPOSTED` or `TRNAMT`) → skip the
  transaction, write a warning to stderr (unless `--strict`, which
  exits 1 on the first bad row — matches `ucol`/`usum` convention)
- `<INVSTMTRS>` (investment statement) → error to stderr, exit 1, tell
  user this is not yet supported

## Test plan

Unit tests (micro-tests, no file I/O):

1. `normalize_date` — happy path + time-component variants + invalid
2. `detect_version` — `<?xml` → 2.x; `OFXHEADER:100` → 1.x
3. `parse_header` — splits v1 header cleanly; passes through v2
4. `extract_transactions` on minimal OFX 1.x fixture strings:
   - one transaction
   - multiple transactions
   - credit card (`<CCSTMTTRN>`) vs bank (`<STMTTRN>`)
   - missing optional fields (empty `NAME`, no `MEMO`)
   - missing required fields (missing `DTPOSTED`) — skip with warning
5. `extract_transactions` on OFX 2.x fixture strings (same cases)
6. End-to-end via `main()` with captured stdout:
   - default CSV output
   - `--to-table`
   - `--to-tsv`
   - stdin input

Fixtures live as triple-quoted strings in the test file (tiny, hand-
crafted examples — not real bank files, both for licensing and to
avoid committing PII).

## Open questions

1. **Locale / decimal separator** — OFX spec mandates `.` for
   decimals. In practice some European banks emit `,`. Punt for v1;
   if it comes up, normalize to `.` with a `--decimal` flag.
2. **Encoding** — QFX is usually `windows-1252`; OFX 2.x declares
   `UTF-8`. Read with `encoding="cp1252"` when the header says so,
   otherwise UTF-8. (Check the `ENCODING:` header line in v1.)
3. **Newline handling in `MEMO`** — some banks emit literal newlines
   inside memo values. Our regex stops at `<`, so we'll include the
   newline. CSV output handles this via quoting. Worth a test.

## Out of scope (future work, separate designs)

- Writing OFX (export)
- Account metadata extraction (bank ID, account number) — could live
  in a separate `--info` mode
- Deduping against a running ledger via `FITID`
- Mixed bank + investment statements in a single output (today the
  schema choice is a hard switch via `--investments`)
