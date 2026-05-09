"""Tests for uqfx."""

import io
import sys
from unittest import mock

import pytest

from utool import uqfx


# --- fixtures ---

OFX_V1 = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKACCTFROM>
<BANKID>123456789
<ACCTID>9999000111
<ACCTTYPE>CHECKING
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20260101
<DTEND>20260131
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260105120000
<TRNAMT>-25.00
<FITID>1001
<NAME>STARBUCKS
<MEMO>downtown
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260110
<TRNAMT>1500.00
<FITID>1002
<NAME>PAYROLL
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""

OFX_V1_CC = """OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX>
<CREDITCARDMSGSRSV1>
<CCSTMTTRNRS>
<CCSTMTRS>
<BANKTRANLIST>
<CCSTMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260201
<TRNAMT>-50.00
<FITID>2001
<NAME>AMAZON
</CCSTMTTRN>
</BANKTRANLIST>
</CCSTMTRS>
</CCSTMTTRNRS>
</CREDITCARDMSGSRSV1>
</OFX>
"""

OFX_V1_CHECK = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<BANKMSGSRSV1>
<STMTTRN>
<TRNTYPE>CHECK
<DTPOSTED>20260115
<TRNAMT>-200.00
<FITID>3001
<CHECKNUM>1234
<NAME>RENT
</STMTTRN>
</BANKMSGSRSV1>
</OFX>
"""

OFX_V1_MISSING_DATE = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<STMTTRN>
<TRNTYPE>DEBIT
<TRNAMT>-10.00
<FITID>4001
<NAME>NO_DATE
</STMTTRN>
</OFX>
"""

OFX_V2 = """<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="200" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM>
          <BANKID>123456789</BANKID>
          <ACCTID>9999000111</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20260101</DTSTART>
          <DTEND>20260131</DTEND>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260105120000</DTPOSTED>
            <TRNAMT>-25.00</TRNAMT>
            <FITID>1001</FITID>
            <NAME>STARBUCKS</NAME>
            <MEMO>downtown</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20260110</DTPOSTED>
            <TRNAMT>1500.00</TRNAMT>
            <FITID>1002</FITID>
            <NAME>PAYROLL</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""

OFX_INVESTMENT = """OFXHEADER:100
DATA:OFXSGML

<OFX>
<INVSTMTMSGSRSV1>
<INVSTMTRS>
<INVTRANLIST>
</INVTRANLIST>
</INVSTMTRS>
</INVSTMTMSGSRSV1>
</OFX>
"""

OFX_INV_V1 = """OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX>
<INVSTMTMSGSRSV1>
<INVSTMTTRNRS>
<INVSTMTRS>
<INVACCTFROM>
<BROKERID>example.com
<ACCTID>BROKER-12345
</INVACCTFROM>
<INVTRANLIST>
<DTSTART>20260101
<DTEND>20260131
<BUYSTOCK>
<INVBUY>
<INVTRAN>
<FITID>20260105.001
<DTTRADE>20260105
<MEMO>Apple buy
</INVTRAN>
<SECID>
<UNIQUEID>037833100
<UNIQUEIDTYPE>CUSIP
</SECID>
<UNITS>10
<UNITPRICE>180.50
<COMMISSION>4.95
<TOTAL>-1809.95
<SUBACCTSEC>CASH
<SUBACCTFUND>CASH
</INVBUY>
<BUYTYPE>BUY
</BUYSTOCK>
<INCOME>
<INVTRAN>
<FITID>20260115.001
<DTTRADE>20260115
</INVTRAN>
<SECID>
<UNIQUEID>037833100
<UNIQUEIDTYPE>CUSIP
</SECID>
<INCOMETYPE>DIV
<TOTAL>5.50
<SUBACCTSEC>CASH
<SUBACCTFUND>CASH
</INCOME>
<INVBANKTRAN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260120
<TRNAMT>1000.00
<FITID>20260120.001
<NAME>DEPOSIT
</STMTTRN>
<SUBACCTFUND>CASH
</INVBANKTRAN>
</INVTRANLIST>
</INVSTMTRS>
</INVSTMTTRNRS>
</INVSTMTMSGSRSV1>
<SECLISTMSGSRSV1>
<SECLIST>
<STOCKINFO>
<SECINFO>
<SECID>
<UNIQUEID>037833100
<UNIQUEIDTYPE>CUSIP
</SECID>
<SECNAME>APPLE INC
<TICKER>AAPL
</SECINFO>
<STOCKTYPE>COMMON
</STOCKINFO>
<MFINFO>
<SECINFO>
<SECID>
<UNIQUEID>922908769
<UNIQUEIDTYPE>CUSIP
</SECID>
<SECNAME>VANGUARD TOTAL STOCK MARKET INDEX
<TICKER>VTI
</SECINFO>
<MFTYPE>OPENEND
</MFINFO>
</SECLIST>
</SECLISTMSGSRSV1>
</OFX>
"""

OFX_INV_V2 = """<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="200" SECURITY="NONE" OLDFILEUID="NONE" NEWFILEUID="NONE"?>
<OFX>
  <INVSTMTMSGSRSV1>
    <INVSTMTTRNRS>
      <INVSTMTRS>
        <INVTRANLIST>
          <BUYSTOCK>
            <INVBUY>
              <INVTRAN>
                <FITID>20260105.001</FITID>
                <DTTRADE>20260105</DTTRADE>
              </INVTRAN>
              <SECID>
                <UNIQUEID>037833100</UNIQUEID>
                <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
              </SECID>
              <UNITS>10</UNITS>
              <UNITPRICE>180.50</UNITPRICE>
              <COMMISSION>4.95</COMMISSION>
              <TOTAL>-1809.95</TOTAL>
            </INVBUY>
            <BUYTYPE>BUY</BUYTYPE>
          </BUYSTOCK>
        </INVTRANLIST>
      </INVSTMTRS>
    </INVSTMTTRNRS>
  </INVSTMTMSGSRSV1>
  <SECLISTMSGSRSV1>
    <SECLIST>
      <STOCKINFO>
        <SECINFO>
          <SECID>
            <UNIQUEID>037833100</UNIQUEID>
            <UNIQUEIDTYPE>CUSIP</UNIQUEIDTYPE>
          </SECID>
          <SECNAME>APPLE INC</SECNAME>
          <TICKER>AAPL</TICKER>
        </SECINFO>
        <STOCKTYPE>COMMON</STOCKTYPE>
      </STOCKINFO>
    </SECLIST>
  </SECLISTMSGSRSV1>
</OFX>
"""


# --- detect_version ---


@pytest.mark.parametrize(
    "data, expected",
    [
        (OFX_V1, "1.x"),
        (OFX_V2, "2.x"),
        ('<?xml version="1.0"?><foo/>', "2.x"),
        ("OFXHEADER:100\n", "1.x"),
    ],
)
def test_detect_version(data, expected):
    """Test version detection."""
    assert uqfx.detect_version(data) == expected


# --- parse_header ---


def test_parse_header_v1():
    """Test that v1 header is split before the <OFX> tag."""
    header, body = uqfx.parse_header(OFX_V1)
    assert "OFXHEADER:100" in header
    assert "<OFX>" not in header
    assert body.startswith("<OFX>")


def test_parse_header_v2():
    """Test that v2 has empty header."""
    header, body = uqfx.parse_header(OFX_V2)
    assert header == ""
    assert body == OFX_V2


# --- normalize_date ---


@pytest.mark.parametrize(
    "ofx_date, expected",
    [
        ("20260105", "2026-01-05"),
        ("20260105120000", "2026-01-05"),
        ("20260105120000.000", "2026-01-05"),
        ("20260105120000.000[-5:EST]", "2026-01-05"),
        ("  20260105  ", "2026-01-05"),
    ],
)
def test_normalize_date(ofx_date, expected):
    """Test OFX date normalization."""
    assert uqfx.normalize_date(ofx_date) == expected


@pytest.mark.parametrize("bad", ["", "abc", "2026", "2026-01-05"])
def test_normalize_date_invalid(bad):
    """Test that invalid dates raise ValueError."""
    with pytest.raises(ValueError, match="invalid OFX date"):
        uqfx.normalize_date(bad)


# --- extract_transactions: v1 ---


def test_extract_v1_basic():
    """Test extracting transactions from a basic v1 statement."""
    txns = uqfx.extract_transactions(OFX_V1)
    assert len(txns) == 2
    assert txns[0] == {
        "date": "2026-01-05",
        "amount": "-25.00",
        "type": "DEBIT",
        "payee": "STARBUCKS",
        "memo": "downtown",
        "check": "",
        "fitid": "1001",
        "acctid": "9999000111",
    }
    assert txns[1]["payee"] == "PAYROLL"
    assert txns[1]["memo"] == ""  # absent
    assert txns[1]["acctid"] == "9999000111"


def test_extract_v1_credit_card():
    """Test that CCSTMTTRN blocks are extracted just like STMTTRN."""
    txns = uqfx.extract_transactions(OFX_V1_CC)
    assert len(txns) == 1
    assert txns[0]["payee"] == "AMAZON"
    assert txns[0]["amount"] == "-50.00"


def test_extract_v1_check():
    """Test that CHECKNUM is extracted."""
    txns = uqfx.extract_transactions(OFX_V1_CHECK)
    assert len(txns) == 1
    assert txns[0]["check"] == "1234"
    assert txns[0]["type"] == "CHECK"


def test_extract_v1_missing_date():
    """Test that missing DTPOSTED produces an empty date string."""
    txns = uqfx.extract_transactions(OFX_V1_MISSING_DATE)
    assert len(txns) == 1
    assert txns[0]["date"] == ""
    assert txns[0]["payee"] == "NO_DATE"


def test_extract_v1_empty():
    """Test that input with no transactions returns empty list."""
    data = "OFXHEADER:100\n\n<OFX></OFX>\n"
    assert uqfx.extract_transactions(data) == []


# --- extract_transactions: v2 ---


def test_extract_v2_basic():
    """Test extracting transactions from v2 XML."""
    txns = uqfx.extract_transactions(OFX_V2)
    assert len(txns) == 2
    assert txns[0]["date"] == "2026-01-05"
    assert txns[0]["payee"] == "STARBUCKS"
    assert txns[0]["memo"] == "downtown"
    assert txns[1]["payee"] == "PAYROLL"


# --- extract_transactions: errors ---


def test_extract_investment_raises():
    """Test that investment statements raise ValueError without --investments."""
    with pytest.raises(ValueError, match="investment statements"):
        uqfx.extract_transactions(OFX_INVESTMENT)


# --- extract_transactions: investments mode ---


def test_extract_inv_v1_basic():
    """Test extracting investment transactions from v1 SGML."""
    txns = uqfx.extract_transactions(OFX_INV_V1, investments=True)
    assert len(txns) == 3
    # BUYSTOCK — CUSIP 037833100 mapped to AAPL via SECLIST
    buy = txns[0]
    assert buy["type"] == "BUYSTOCK"
    assert buy["subtype"] == "BUY"
    assert buy["date"] == "2026-01-05"
    assert buy["security"] == "AAPL"
    assert buy["units"] == "10"
    assert buy["unit_price"] == "180.50"
    assert buy["commission"] == "4.95"
    assert buy["total"] == "-1809.95"
    assert buy["memo"] == "Apple buy"
    assert buy["fitid"] == "20260105.001"
    # INCOME
    inc = txns[1]
    assert inc["type"] == "INCOME"
    assert inc["subtype"] == "DIV"
    assert inc["security"] == "AAPL"
    assert inc["total"] == "5.50"
    assert inc["units"] == ""
    # INVBANKTRAN: cash deposit, security/units empty
    bank = txns[2]
    assert bank["type"] == "INVBANKTRAN"
    assert bank["subtype"] == "CREDIT"
    assert bank["date"] == "2026-01-20"
    assert bank["total"] == "1000.00"
    assert bank["security"] == ""
    assert bank["units"] == ""
    assert bank["memo"] == "DEPOSIT"
    # All txns share the same investment-account ACCTID
    for txn in txns:
        assert txn["acctid"] == "BROKER-12345"


def test_extract_inv_v2_basic():
    """Test extracting investment transactions from v2 XML."""
    txns = uqfx.extract_transactions(OFX_INV_V2, investments=True)
    assert len(txns) == 1
    buy = txns[0]
    assert buy["type"] == "BUYSTOCK"
    assert buy["subtype"] == "BUY"
    assert buy["security"] == "AAPL"
    assert buy["units"] == "10"
    assert buy["unit_price"] == "180.50"
    assert buy["total"] == "-1809.95"


# --- build_security_map ---


def test_build_security_map_v1():
    """Test parsing CUSIP -> ticker map from v1 SECLIST."""
    sec_map = uqfx.build_security_map(OFX_INV_V1)
    assert sec_map == {"037833100": "AAPL", "922908769": "VTI"}


def test_build_security_map_v2():
    """Test parsing CUSIP -> ticker map from v2 SECLIST."""
    sec_map = uqfx.build_security_map(OFX_INV_V2)
    assert sec_map == {"037833100": "AAPL"}


def test_build_security_map_no_seclist():
    """Test that a file with no SECLIST returns empty map."""
    assert uqfx.build_security_map(OFX_V1) == {}


def test_extract_inv_falls_back_to_cusip_when_unmapped():
    """Test that an unmapped CUSIP is preserved as-is."""
    # Strip SECLIST from the fixture
    data = OFX_INV_V1.split("<SECLISTMSGSRSV1>")[0] + "</OFX>\n"
    txns = uqfx.extract_transactions(data, investments=True)
    assert txns[0]["security"] == "037833100"  # CUSIP, no ticker available


def test_extract_inv_no_error_on_inv_file():
    """Test that --investments mode doesn't raise on INVSTMTRS files."""
    txns = uqfx.extract_transactions(OFX_INV_V1, investments=True)
    assert len(txns) > 0


def test_extract_inv_on_bank_file_returns_empty():
    """Test --investments mode on a bank-only file returns empty list."""
    assert uqfx.extract_transactions(OFX_V1, investments=True) == []


def test_main_investments(capsys):
    """Test --investments mode emits the investment schema via main()."""
    sys.argv = ["uqfx", "--investments"]
    with mock.patch("sys.stdin", io.StringIO(OFX_INV_V1)):
        uqfx.main()
    out = capsys.readouterr().out
    lines = [line.rstrip("\r") for line in out.strip().split("\n")]
    assert lines[0] == (
        "date,type,subtype,security,units,unit_price,"
        "commission,fees,total,memo,fitid,acctid"
    )
    assert any("BUYSTOCK" in line for line in lines)
    assert any("INCOME,DIV" in line for line in lines)
    assert any("INVBANKTRAN" in line for line in lines)


# --- extract_acctid ---


def test_extract_acctid_v1():
    """Test extracting ACCTID from v1 SGML BANKACCTFROM."""
    assert uqfx.extract_acctid(OFX_V1) == "9999000111"


def test_extract_acctid_v2():
    """Test extracting ACCTID from v2 XML BANKACCTFROM."""
    assert uqfx.extract_acctid(OFX_V2) == "9999000111"


def test_extract_acctid_investment_v1():
    """Test extracting ACCTID from v1 SGML INVACCTFROM."""
    assert uqfx.extract_acctid(OFX_INV_V1) == "BROKER-12345"


def test_extract_acctid_missing():
    """Test that a file without ACCTID returns empty string."""
    data = "OFXHEADER:100\n\n<OFX></OFX>\n"
    assert uqfx.extract_acctid(data) == ""


# --- detect_encoding ---


def test_detect_encoding_v2_xml():
    """Test that XML files are detected as UTF-8."""
    assert uqfx.detect_encoding(OFX_V2.encode("utf-8")) == "utf-8"


def test_detect_encoding_v1_usascii_1252():
    """Test that USASCII + CHARSET 1252 maps to cp1252."""
    raw = OFX_V1.encode("cp1252")
    assert uqfx.detect_encoding(raw) == "cp1252"


def test_detect_encoding_v1_utf8():
    """Test that ENCODING:UTF-8 maps to utf-8."""
    header = (
        "OFXHEADER:100\nDATA:OFXSGML\nENCODING:UTF-8\n\n<OFX></OFX>\n"
    )
    assert uqfx.detect_encoding(header.encode("utf-8")) == "utf-8"


def test_detect_encoding_no_header_defaults_cp1252():
    """Test that an unknown header defaults to cp1252."""
    raw = b"<OFX></OFX>"
    assert uqfx.detect_encoding(raw) == "cp1252"


# --- main() ---


def test_main_csv_default(capsys):
    """Test default CSV output via stdin."""
    sys.argv = ["uqfx"]
    with mock.patch("sys.stdin", io.StringIO(OFX_V1)):
        uqfx.main()
    out = capsys.readouterr().out
    lines = [line.rstrip("\r") for line in out.strip().split("\n")]
    assert lines[0] == "date,amount,type,payee,memo,check,fitid,acctid"
    assert "2026-01-05,-25.00,DEBIT,STARBUCKS,downtown,,1001,9999000111" in lines


def test_main_to_table(capsys):
    """Test --to-table output."""
    sys.argv = ["uqfx", "-t"]
    with mock.patch("sys.stdin", io.StringIO(OFX_V1)):
        uqfx.main()
    out = capsys.readouterr().out
    assert "STARBUCKS" in out
    assert "----" in out  # separator line


def test_main_to_tsv(capsys):
    """Test --to-tsv output."""
    sys.argv = ["uqfx", "--to-tsv"]
    with mock.patch("sys.stdin", io.StringIO(OFX_V1)):
        uqfx.main()
    out = capsys.readouterr().out
    assert "\t" in out
    assert "date\tamount\ttype" in out


def test_main_v2_xml(capsys):
    """Test that v2 XML works through main()."""
    sys.argv = ["uqfx"]
    with mock.patch("sys.stdin", io.StringIO(OFX_V2)):
        uqfx.main()
    out = capsys.readouterr().out
    assert "STARBUCKS" in out
    assert "PAYROLL" in out


def test_main_investment_errors(capsys):
    """Test that investment statements exit with an error."""
    sys.argv = ["uqfx"]
    with mock.patch("sys.stdin", io.StringIO(OFX_INVESTMENT)):
        with pytest.raises(SystemExit) as excinfo:
            uqfx.main()
        assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "investment" in err
