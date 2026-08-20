"""Holidays -- the XML session, clean-by-default rows, raw passthrough, params, offline."""

import pytest

from pydatagokr.services.holidays import Holidays


def _xml(items, total):
    rows = "".join(
        "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
        for item in items)
    return (f"<response><header><resultCode>00</resultCode>"
            f"<resultMsg>NORMAL SERVICE.</resultMsg></header>"
            f"<body><items>{rows}</items>"
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


_ROW = {
    "dateKind":  "01",
    "dateName":  "1월1일",
    "isHoliday": "Y",
    "locdate":   "20260101",
    "seq":       "1",
}


def _holidays(raw):
    holidays = Holidays(api_key="k")
    opener = _FakeOpener(raw)
    holidays._session._opener = opener
    return holidays, opener


def test_holidays_clean_by_default():
    holidays, _ = _holidays(_xml([_ROW], 1))
    assert holidays.holidays(year=2026) == [{
        "date":       "2026-01-01",
        "name":       "1월1일",
        "is_holiday": "Y",
        "kind_code":  "01",
        "seq":        1,
    }]


def test_holidays_raw_passthrough_keeps_vendor_tokens():
    holidays, _ = _holidays(_xml([_ROW], 1))
    assert holidays.holidays(year=2026, clean=False) == [_ROW]


def test_year_and_month_go_to_the_vendor_params():
    holidays, opener = _holidays(_xml([], 0))
    holidays.fetch("solar_terms", year=2026, month=3)
    query = opener.requests[0].full_url
    assert "get24DivisionsInfo" in query    # the solar_terms operation path
    assert "solYear=2026" in query
    assert "solMonth=03" in query           # zero-padded


def test_month_omitted_is_absent_from_the_query():
    holidays, opener = _holidays(_xml([], 0))
    holidays.holidays(year=2026)
    query = opener.requests[0].full_url
    assert "solYear=2026" in query
    assert "solMonth" not in query


def test_fetch_rejects_an_unknown_operation():
    holidays, _ = _holidays(_xml([], 0))
    with pytest.raises(ValueError, match="unknown operation"):
        holidays.fetch("nope", year=2026)
