"""Parse QFX/OFX bank-statement files and emit transactions as CSV."""

import argparse
import csv
import io
import re
import sys
import xml.etree.ElementTree as ET


FIELDS = ["date", "amount", "type", "payee", "memo", "check", "fitid", "acctid"]

INV_FIELDS = [
    "date", "type", "subtype", "security", "units", "unit_price",
    "commission", "fees", "total", "memo", "fitid", "acctid",
]

# OFX field mapping: output column -> OFX tag
_TAG_MAP = {
    "date": "DTPOSTED",
    "amount": "TRNAMT",
    "type": "TRNTYPE",
    "payee": "NAME",
    "memo": "MEMO",
    "check": "CHECKNUM",
    "fitid": "FITID",
}

# Investment transaction wrapper tags (kinds of <INVTRANLIST> children)
INV_TXN_TAGS = (
    "BUYSTOCK", "BUYMF", "BUYDEBT", "BUYOPT", "BUYOTHER",
    "SELLSTOCK", "SELLMF", "SELLDEBT", "SELLOPT", "SELLOTHER",
    "INCOME", "REINVEST", "TRANSFER", "INVBANKTRAN",
)

# OFX 1.x SGML field-extraction regex: <TAG>value (value runs to next "<")
_TAG_VAL = re.compile(r"<([A-Z][A-Z0-9]*)>([^<]*)")
# OFX 1.x bank/CC transaction-block regex
_TXN_BLOCK = re.compile(r"<(STMTTRN|CCSTMTTRN)>(.*?)</\1>", re.DOTALL)
# OFX 1.x investment transaction-block regex
_INV_TXN_BLOCK = re.compile(
    r"<(" + "|".join(INV_TXN_TAGS) + r")>(.*?)</\1>", re.DOTALL
)
# OFX 1.x security-info block regex (inside <STOCKINFO>, <MFINFO>, etc.)
_SECINFO_BLOCK = re.compile(r"<SECINFO>(.*?)</SECINFO>", re.DOTALL)


def detect_version(data: str) -> str:
    """Detect OFX version from raw data.

    data -- decoded OFX/QFX text
    returns '1.x' for SGML or '2.x' for XML
    """
    head = data.lstrip()[:200]
    if head.startswith("<?xml"):
        return "2.x"
    return "1.x"


def parse_header(data: str) -> tuple[str, str]:
    """Split QFX/OFX text into (header, body).

    For 2.x there is no SGML header, so header is empty.
    For 1.x the header runs up to the first <OFX> tag.
    """
    if detect_version(data) == "2.x":
        return "", data
    idx = data.find("<OFX>")
    if idx == -1:
        return data, ""
    return data[:idx], data[idx:]


def normalize_date(ofx_date: str) -> str:
    """Convert an OFX date (YYYYMMDD[HHMMSS[.XXX][offset]]) to YYYY-MM-DD.

    Raises ValueError on input that doesn't start with 8 digits.
    """
    s = ofx_date.strip()
    if len(s) < 8 or not s[:8].isdigit():
        raise ValueError(f"invalid OFX date: {ofx_date!r}")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"


def _normalize_txn(raw: dict[str, str]) -> dict[str, str]:
    """Map a dict of raw OFX fields to our normalized output dict.

    Missing fields become empty strings. A malformed DTPOSTED becomes
    an empty date rather than raising.
    """
    date_str = raw.get("DTPOSTED", "").strip()
    try:
        date = normalize_date(date_str) if date_str else ""
    except ValueError:
        date = ""
    out = {f: "" for f in FIELDS}
    out["date"] = date
    for col, tag in _TAG_MAP.items():
        if col == "date":
            continue
        out[col] = raw.get(tag, "").strip()
    return out


def _extract_v1(data: str) -> list[dict[str, str]]:
    """Extract transactions from OFX 1.x SGML."""
    _, body = parse_header(data)
    txns: list[dict[str, str]] = []
    for match in _TXN_BLOCK.finditer(body):
        block = match.group(2)
        raw: dict[str, str] = {}
        for tag_match in _TAG_VAL.finditer(block):
            tag = tag_match.group(1)
            val = tag_match.group(2)
            # Keep first occurrence (e.g. <NAME> at the STMTTRN level
            # before any nested <PAYEE><NAME>...).
            raw.setdefault(tag, val)
        txns.append(_normalize_txn(raw))
    return txns


def _extract_v2(data: str) -> list[dict[str, str]]:
    """Extract transactions from OFX 2.x XML."""
    # Strip XML and OFX processing instructions; ET tolerates the xml
    # decl but the OFX PI sometimes confuses it on partial inputs.
    body = re.sub(r"<\?[^?]*\?>", "", data, count=2).strip()
    root = ET.fromstring(body)
    txns: list[dict[str, str]] = []
    for elem in root.iter():
        if elem.tag in ("STMTTRN", "CCSTMTTRN"):
            raw = {child.tag: (child.text or "") for child in elem}
            txns.append(_normalize_txn(raw))
    return txns


def build_security_map(data: str) -> dict[str, str]:
    """Build a map of UNIQUEID -> TICKER from <SECINFO> blocks.

    QFX/OFX investment files include a <SECLIST> with <STOCKINFO>,
    <MFINFO>, <DEBTINFO>, <OPTINFO>, and <OTHERINFO> entries. Each wraps
    a <SECINFO> containing a <SECID> (UNIQUEID + UNIQUEIDTYPE) and a
    <TICKER>. This function walks them and produces a CUSIP-to-ticker
    map (or whatever UNIQUEIDTYPE is in use). Returns empty dict if the
    file has no security-list data.
    """
    if detect_version(data) == "2.x":
        body = re.sub(r"<\?[^?]*\?>", "", data, count=2).strip()
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return {}
        sec_map: dict[str, str] = {}
        for elem in root.iter("SECINFO"):
            uid = ticker = ""
            for sub in elem.iter():
                if sub.tag == "UNIQUEID" and sub.text:
                    uid = sub.text.strip()
                elif sub.tag == "TICKER" and sub.text:
                    ticker = sub.text.strip()
            if uid and ticker:
                sec_map[uid] = ticker
        return sec_map
    # v1 SGML
    _, body = parse_header(data)
    sec_map = {}
    for match in _SECINFO_BLOCK.finditer(body):
        block = match.group(1)
        fields: dict[str, str] = {}
        for tag_match in _TAG_VAL.finditer(block):
            fields.setdefault(tag_match.group(1), tag_match.group(2))
        uid = fields.get("UNIQUEID", "").strip()
        ticker = fields.get("TICKER", "").strip()
        if uid and ticker:
            sec_map[uid] = ticker
    return sec_map


def _normalize_inv_txn(
    wrapper_tag: str,
    raw: dict[str, str],
    sec_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """Map raw OFX investment fields to our normalized output dict.

    Investment transactions and INVBANKTRAN cash transactions both flow
    through this. INVBANKTRAN reads bank-style fields (DTPOSTED, TRNAMT,
    TRNTYPE, NAME); investment txns read INVTRAN/SECID/wrapper fields.
    If sec_map maps UNIQUEID -> ticker, the security column shows the
    ticker; otherwise the UNIQUEID is preserved as-is.
    """
    is_bank = wrapper_tag == "INVBANKTRAN"

    date_str = raw.get("DTPOSTED" if is_bank else "DTTRADE", "").strip()
    try:
        date = normalize_date(date_str) if date_str else ""
    except ValueError:
        date = ""

    if is_bank:
        subtype = raw.get("TRNTYPE", "").strip()
        total = raw.get("TRNAMT", "").strip()
        memo = raw.get("MEMO", "").strip() or raw.get("NAME", "").strip()
    else:
        subtype = (
            raw.get("BUYTYPE")
            or raw.get("SELLTYPE")
            or raw.get("INCOMETYPE")
            or ""
        ).strip()
        total = raw.get("TOTAL", "").strip()
        memo = raw.get("MEMO", "").strip()

    uid = raw.get("UNIQUEID", "").strip()
    security = (sec_map or {}).get(uid, uid)

    return {
        "date": date,
        "type": wrapper_tag,
        "subtype": subtype,
        "security": security,
        "units": raw.get("UNITS", "").strip(),
        "unit_price": raw.get("UNITPRICE", "").strip(),
        "commission": raw.get("COMMISSION", "").strip(),
        "fees": raw.get("FEES", "").strip(),
        "total": total,
        "memo": memo,
        "fitid": raw.get("FITID", "").strip(),
    }


def _extract_inv_v1(data: str) -> list[dict[str, str]]:
    """Extract investment transactions from OFX 1.x SGML."""
    sec_map = build_security_map(data)
    _, body = parse_header(data)
    txns: list[dict[str, str]] = []
    for match in _INV_TXN_BLOCK.finditer(body):
        wrapper = match.group(1)
        block = match.group(2)
        raw: dict[str, str] = {}
        for tag_match in _TAG_VAL.finditer(block):
            tag = tag_match.group(1)
            val = tag_match.group(2)
            raw.setdefault(tag, val)
        txns.append(_normalize_inv_txn(wrapper, raw, sec_map))
    return txns


def _extract_inv_v2(data: str) -> list[dict[str, str]]:
    """Extract investment transactions from OFX 2.x XML."""
    sec_map = build_security_map(data)
    body = re.sub(r"<\?[^?]*\?>", "", data, count=2).strip()
    root = ET.fromstring(body)
    txns: list[dict[str, str]] = []
    for elem in root.iter():
        if elem.tag in INV_TXN_TAGS:
            raw: dict[str, str] = {}
            for sub in elem.iter():
                if sub is elem:
                    continue
                if sub.text and sub.text.strip():
                    raw.setdefault(sub.tag, sub.text)
            txns.append(_normalize_inv_txn(elem.tag, raw, sec_map))
    return txns


def extract_acctid(data: str) -> str:
    """Return the first <ACCTID> value from the file (or empty string).

    ACCTID lives inside the statement-level account-from wrapper
    (<BANKACCTFROM>, <CCACCTFROM>, <INVACCTFROM>). Files typically
    contain a single statement; if there are multiple distinct ACCTIDs
    we return the first one.
    """
    if detect_version(data) == "2.x":
        body = re.sub(r"<\?[^?]*\?>", "", data, count=2).strip()
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return ""
        for elem in root.iter("ACCTID"):
            if elem.text:
                return elem.text.strip()
        return ""
    _, body = parse_header(data)
    match = re.search(r"<ACCTID>([^<]*)", body)
    return match.group(1).strip() if match else ""


def extract_transactions(
    data: str,
    investments: bool = False,
) -> list[dict[str, str]]:
    """Extract all transactions from QFX/OFX data into normalized dicts.

    By default, returns bank/credit-card transactions (FIELDS schema).
    Raises ValueError if the file is an investment statement.

    With investments=True, returns investment transactions plus any
    INVBANKTRAN cash transactions (INV_FIELDS schema).

    Each dict gets an `acctid` field populated from the file's
    <ACCTID> tag (or empty string if absent).
    """
    if investments:
        if detect_version(data) == "2.x":
            txns = _extract_inv_v2(data)
        else:
            txns = _extract_inv_v1(data)
    else:
        if "<INVSTMTRS>" in data:
            raise ValueError(
                "investment statements (INVSTMTRS) are not supported "
                "without --investments"
            )
        if detect_version(data) == "2.x":
            txns = _extract_v2(data)
        else:
            txns = _extract_v1(data)

    acctid = extract_acctid(data)
    for txn in txns:
        txn["acctid"] = acctid
    return txns


def format_table(rows: list[dict], fieldnames: list[str]) -> str:
    """Format rows as a simple aligned table."""
    widths = [len(f) for f in fieldnames]
    for row in rows:
        for i, f in enumerate(fieldnames):
            widths[i] = max(widths[i], len(str(row.get(f, ""))))
    header = "  ".join(f.ljust(widths[i]) for i, f in enumerate(fieldnames))
    separator = "  ".join("-" * widths[i] for i in range(len(fieldnames)))
    lines = [header, separator]
    for row in rows:
        line = "  ".join(
            str(row.get(f, "")).ljust(widths[i]) for i, f in enumerate(fieldnames)
        )
        lines.append(line)
    return "\n".join(lines) + "\n"


def detect_encoding(raw: bytes) -> str:
    """Detect file encoding from QFX/OFX header bytes.

    OFX 2.x: assume UTF-8 (the XML declaration handles itself if we
             round-trip through ET, but for our string pipeline we
             just pick a sensible default).
    OFX 1.x: read ENCODING: and CHARSET: header lines. If ENCODING is
             USASCII, use the CHARSET codepage (default cp1252).
    """
    head = raw[:1024].decode("ascii", errors="replace")
    if head.lstrip().startswith("<?xml"):
        return "utf-8"
    enc = None
    charset = None
    for line in head.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("<"):
            break
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().upper()
            val = val.strip()
            if key == "ENCODING":
                enc = val.upper()
            elif key == "CHARSET":
                charset = val
    if enc in ("UTF-8", "UNICODE"):
        return "utf-8"
    if enc == "USASCII" and charset:
        return f"cp{charset}" if charset.isdigit() else charset
    return "cp1252"


def main() -> None:
    """Main handler."""
    parser = argparse.ArgumentParser(
        description="parse QFX/OFX transactions to CSV"
    )
    parser.add_argument(
        "-f",
        "--file",
        default=None,
        help="input QFX/OFX file path (default=stdin)",
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
        "--to-table",
        action="store_true",
        help="display output as a formatted table",
    )
    parser.add_argument(
        "--to-tsv",
        action="store_true",
        help="write output as TSV instead of CSV",
    )
    parser.add_argument(
        "--investments",
        action="store_true",
        help="parse investment statement transactions (BUYSTOCK, SELLSTOCK, "
        "INCOME, REINVEST, INVBANKTRAN, etc.) using a wider schema",
    )

    args = parser.parse_args()

    if args.file:
        with open(args.file, "rb") as fh:
            raw = fh.read()
        encoding = detect_encoding(raw)
        try:
            data = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            data = raw.decode("cp1252", errors="replace")
    else:
        data = sys.stdin.read()

    try:
        transactions = extract_transactions(data, investments=args.investments)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        sys.exit(1)
    except ET.ParseError as e:
        sys.stderr.write(f"error: failed to parse OFX 2.x XML: {e}\n")
        sys.exit(1)

    fieldnames = INV_FIELDS if args.investments else FIELDS

    if args.to_table:
        sys.stdout.write(format_table(transactions, fieldnames))
    else:
        out_dialect = "excel-tab" if args.to_tsv else "excel"
        out = args.output or sys.stdout
        buf = io.StringIO() if out is sys.stdout else out
        writer = csv.DictWriter(buf, fieldnames=fieldnames, dialect=out_dialect)
        writer.writeheader()
        writer.writerows(transactions)
        if out is sys.stdout:
            sys.stdout.write(buf.getvalue())
        if args.output:
            args.output.close()


if __name__ == "__main__":
    main()
