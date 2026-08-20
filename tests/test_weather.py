"""Weather -- XML session, forecast long rows, nowcast, grid params, three ops, offline."""

import pytest

from pydatagokr.services.weather import Weather


def _xml(items, total):
    rows = "".join(
        "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
        for item in items)
    return (f"<response><header><resultCode>00</resultCode>"
            f"<resultMsg>NORMAL_SERVICE</resultMsg></header>"
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


_FCST_ROW = {
    "baseDate":  "20260811",
    "baseTime":  "0500",
    "category":  "TMP",
    "fcstDate":  "20260811",
    "fcstTime":  "0600",
    "fcstValue": "24",
    "nx":        "60",
    "ny":        "127",
}

_NCST_ROW = {
    "baseDate":  "20260811",
    "baseTime":  "2300",
    "category":  "T1H",
    "obsrValue": "24.5",
    "nx":        "60",
    "ny":        "127",
}


def _weather(raw):
    weather = Weather(api_key="k")
    opener = _FakeOpener(raw)
    weather._session._opener = opener
    return weather, opener


def test_forecast_cleans_the_long_rows():
    weather, _ = _weather(_xml([_FCST_ROW], 1))
    assert weather.forecast(base_date="20260811", base_time="0500", nx=60, ny=127) == [{
        "base_date":      "2026-08-11",
        "base_time":      "0500",
        "category":       "TMP",
        "forecast_date":  "2026-08-11",
        "forecast_time":  "0600",
        "forecast_value": "24",
        "nx":             60,
        "ny":             127,
    }]


def test_nowcast_uses_the_observed_value_shape():
    weather, _ = _weather(_xml([_NCST_ROW], 1))
    assert weather.nowcast(base_date="20260811", base_time="2300", nx=60, ny=127) == [{
        "base_date":      "2026-08-11",
        "base_time":      "2300",
        "category":       "T1H",
        "observed_value": "24.5",
        "nx":             60,
        "ny":             127,
    }]


def test_the_operation_path_and_grid_params_reach_the_vendor():
    weather, opener = _weather(_xml([], 0))
    weather.ultra_forecast(base_date="20260811", base_time="0630", nx=60, ny=127)
    query = opener.requests[0].full_url
    assert "getUltraSrtFcst" in query
    assert "base_date=20260811" in query
    assert "base_time=0630" in query
    assert "nx=60" in query
    assert "ny=127" in query


def test_fetch_rejects_an_unknown_operation():
    weather, _ = _weather(_xml([], 0))
    with pytest.raises(ValueError, match="unknown operation"):
        weather.fetch("nope", base_date="20260811", base_time="0500", nx=60, ny=127)
