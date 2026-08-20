"""RealEstate -- deal_date synthesis, decimal area, the four operations, and the RTMS
three-digit result code, offline."""

import pytest

from pydatagokr.services.realestate import RealEstate


def _xml(items, total):
    rows = "".join(
        "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
        for item in items)
    # RTMS answers a three-digit result code ("000"), not the two-digit "00".
    return (f"<response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg>"
            f"</header><body><items>{rows}</items>"
            f"<totalCount>{total}</totalCount></body></response>").encode()


class _FakeResponse:
    def __init__(self, raw):
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._raw


class _FakeOpener:
    def __init__(self, raw):
        self._raw = raw
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return _FakeResponse(self._raw)


_TRADE_ROW = {
    "dealYear":   "2024",
    "dealMonth":  "1",
    "dealDay":    "19",
    "sggCd":      "11110",
    "umdNm":      "숭인동",
    "jibun":      "766",
    "aptNm":      "종로청계힐스테이트",
    "excluUseAr": "84.9478",
    "floor":      "13",
    "buildYear":  "2009",
    "dealAmount": "101,300",
    "dealingGbn": "중개거래",
    "aptDong":    "105",
}


def _re(raw):
    realestate = RealEstate(api_key="k")
    opener = _FakeOpener(raw)
    realestate._session._opener = opener
    return realestate, opener


def test_apt_trade_synthesizes_deal_date_and_types_the_measures():
    realestate, _ = _re(_xml([_TRADE_ROW], 1))
    row = realestate.apt_trade(region_code="11110", deal_ym="202401")[0]
    assert row["deal_date"] == "2024-01-19"       # from dealYear/dealMonth/dealDay
    assert row["exclusive_area"] == pytest.approx(84.9478)       # decimal -> float
    assert row["deal_amount"] == 101300           # comma stripped -> int
    assert row["floor"] == 13
    assert row["apt_name"] == "종로청계힐스테이트"
    assert "dealYear" not in row                  # split parts collapse into deal_date


def test_a_non_numeric_date_part_drops_only_that_row_not_the_whole_fetch():
    # A malformed vendor date part must not crash the entire month's fetch: _deal_date
    # yields no date, so _spec.clean drops just that one row on its required date-check.
    bad = dict(_TRADE_ROW, dealDay="19일")            # a stray non-numeric day
    realestate, _ = _re(_xml([bad, dict(_TRADE_ROW)], 2))
    rows = realestate.apt_trade(region_code="11110", deal_ym="202401")
    assert len(rows) == 1                              # the good row survives; no crash
    assert rows[0]["deal_date"] == "2024-01-19"


def test_raw_passthrough_keeps_the_vendor_tokens_unchanged():
    realestate, _ = _re(_xml([_TRADE_ROW], 1))
    assert realestate.apt_trade(region_code="11110", deal_ym="202401", clean=False) == [_TRADE_ROW]


def test_the_operation_path_and_filters_reach_the_vendor():
    realestate, opener = _re(_xml([], 0))
    realestate.apt_rent(region_code="11110", deal_ym="202401")
    query = opener.requests[0].full_url
    assert "RTMSDataSvcAptRent/getRTMSDataSvcAptRent" in query   # per-service path segment
    assert "LAWD_CD=11110" in query
    assert "DEAL_YMD=202401" in query


def test_a_three_digit_result_code_is_read_as_success():
    realestate, _ = _re(_xml([_TRADE_ROW], 1))
    assert len(realestate.apt_trade(region_code="11110", deal_ym="202401")) == 1


def test_fetch_rejects_an_unknown_operation():
    realestate, _ = _re(_xml([], 0))
    with pytest.raises(ValueError, match="unknown operation"):
        realestate.fetch("nope", region_code="11110", deal_ym="202401")
