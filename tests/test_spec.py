"""clean() -- typed parsing per field kind, and the key-drop rules."""

from pydatagokr._spec import clean
from pydatagokr.services.kofia import CMA_STATUS, DLS_DLB, MARKET_FUNDS, OVERSEAS_DERIVATIVES
from pydatagokr.services.procurement import SERVICES


def test_market_funds_row_parses_every_kind():
    rows = [{
        "basDt":                     "20240105",
        "invrDpsgAmt":               "50,123",
        "onbdDrvPrdTrRcAdvAmt":      "1234.0",       # decimal-formatted integer
        "toCstRpchCndBndSlgBal":     "-",            # vendor missing marker
        "brkTrdUcolMny":             "",
        "brkTrdUcolMnyVsOppsTrdAmt": "77",
        "ucolMnyVsOppsTrdRlImpt":    "8.5",
    }]
    assert clean(rows, MARKET_FUNDS) == [{
        "base_date":                          "2024-01-05",
        "investor_deposit":                50123,
        "derivatives_deposit":             1234,
        "customer_rp_sale_balance":        None,
        "brokerage_receivable":            None,
        "forced_sell_amount":              77,
        "forced_sell_to_receivable_ratio": 8.5,
    }]


def test_fractional_amount_is_none_not_rounded():
    rows = [{"basDt": "20240105", "invrDpsgAmt": "3.8"}]
    cleaned = clean(rows, MARKET_FUNDS)
    assert cleaned[0]["investor_deposit"] is None    # a contract breach, not a round


def test_non_finite_numbers_become_none():
    # Vendor "NaN"/"inf"/"Infinity" must not become a real nan/inf (int or ratio) -> None.
    rows = [{"basDt": "20240105", "invrDpsgAmt": "inf",
             "ucolMnyVsOppsTrdRlImpt": "NaN"}]
    cleaned = clean(rows, MARKET_FUNDS)
    assert cleaned[0]["investor_deposit"] is None
    assert cleaned[0]["forced_sell_to_receivable_ratio"] is None


def test_missing_date_drops_the_row():
    assert clean([{"invrDpsgAmt": "1"}], MARKET_FUNDS) == []
    assert clean([{"basDt": "2024-01-05", "invrDpsgAmt": "1"}], MARKET_FUNDS) == []


def test_invalid_calendar_date_drops_the_row():
    assert clean([{"basDt": "20240230"}], MARKET_FUNDS) == []


def test_missing_key_dimension_drops_a_composite_key_row():
    rows = [{"basDt": "20240105", "mngInvTgt": "RP형", "invrCtg": "", "actCnt": "10"}]
    assert clean(rows, CMA_STATUS) == []


def test_wide_key_table_keeps_a_row_with_a_null_dimension():
    rows = [{"basDt": "202401", "byPrdGrp": "", "actCtg": "자기", "trqu": "5"}]
    cleaned = clean(rows, OVERSEAS_DERIVATIVES)
    assert len(cleaned) == 1
    assert cleaned[0]["product_group"] is None       # kept, dimension NULL
    assert cleaned[0]["trade_volume"] == 5


def test_date_ym_parses_and_rejects():
    rows = [{"basDt": "202401", "ctgDlbDls": "합계", "ctgPrplcPsub": "공모",
             "presCtg": "발행실적", "amt": "9", "ccnt": "2"}]
    cleaned = clean(rows, DLS_DLB)
    assert cleaned[0]["base_year_month"] == "2024-01"
    assert cleaned[0]["amount_krw"] == 9             # unit encoded in the column name
    dotted = [{**rows[0], "basDt": "2026.01"}]       # customs "YYYY.MM" -> separators stripped
    assert clean(dotted, DLS_DLB)[0]["base_year_month"] == "2026-01"
    bad = [{**rows[0], "basDt": "2024"}]             # not a YYYYMM -> row dropped
    assert clean(bad, DLS_DLB) == []


def test_blank_and_marker_text_is_none():
    rows = [{"basDt": "202401", "byPrdGrp": "None", "actCtg": "nan", "xchNm": "CME"}]
    cleaned = clean(rows, OVERSEAS_DERIVATIVES)
    assert cleaned[0]["product_group"] is None
    assert cleaned[0]["account_type"] is None
    assert cleaned[0]["exchange"] == "CME"


def test_table_derived_properties():
    assert MARKET_FUNDS.date_column == "base_date"
    assert MARKET_FUNDS.key_columns == ("base_date",)
    assert MARKET_FUNDS.columns[0] == "base_date"
    assert CMA_STATUS.key_columns == ("base_date", "management_target", "investor_type")
    assert OVERSEAS_DERIVATIVES.is_wide_key


def test_date_column_is_none_for_a_wide_key_table_without_a_date_field():
    # A wide-key table keyed by a surrogate id, not a period, has no date field; the
    # property returns None rather than raising StopIteration.
    assert SERVICES.date_column is None
