"""Weather -- XML session, forecast long rows, nowcast, grid params, three ops, offline."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from pydatagokr.services.weather import Weather, _latest_base, _resolve_base

_KST = timezone(timedelta(hours=9))


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


# --- latest-announcement default -------------------------------------------------------

def _kst(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi, tzinfo=_KST)


def test_forecast_default_picks_the_latest_issued_slot():
    # 20:55 KST: the 20:00 announcement (issued by 20:10) is the latest available;
    # 23:00 has not happened yet.
    assert _latest_base("forecast", now=_kst(2026, 8, 20, 20, 55)) == ("20260820", "2000")


def test_forecast_default_steps_back_when_a_slot_is_not_yet_published():
    # 14:05 KST is inside the 14:00 slot's publish lag, so the default is the 11:00 slot.
    assert _latest_base("forecast", now=_kst(2026, 8, 20, 14, 5)) == ("20260820", "1100")


def test_forecast_default_rolls_the_date_back_after_midnight():
    # 00:30 KST: no slot has been issued today yet, so it is yesterday's 23:00 announcement.
    assert _latest_base("forecast", now=_kst(2026, 8, 20, 0, 30)) == ("20260819", "2300")


def test_ultra_forecast_default_uses_the_half_hour_slots():
    # 초단기예보 announces at HH30 (published ~HH45); at 20:55 that is 20:30.
    assert _latest_base("ultra_forecast", now=_kst(2026, 8, 20, 20, 55)) == ("20260820", "2030")


def test_nowcast_default_uses_the_hourly_slots_with_its_longer_lag():
    # 초단기실황 announces on the hour but is served ~40 min later; at 20:55 that is 20:00.
    assert _latest_base("nowcast", now=_kst(2026, 8, 20, 20, 55)) == ("20260820", "2000")


def test_latest_base_converts_a_non_kst_now_to_kst():
    # 11:55 UTC == 20:55 KST -> same result as the KST case above.
    utc = datetime(2026, 8, 20, 11, 55, tzinfo=UTC)
    assert _latest_base("forecast", now=utc) == ("20260820", "2000")


def test_resolve_base_passes_an_explicit_pair_through():
    assert _resolve_base("forecast", "20260820", "0500") == ("20260820", "0500")


def test_resolve_base_rejects_exactly_one_of_the_pair():
    with pytest.raises(ValueError, match="both base_date and base_time, or neither"):
        _resolve_base("forecast", "20260820", None)
    with pytest.raises(ValueError, match="both base_date and base_time, or neither"):
        _resolve_base("forecast", None, "0500")


def test_forecast_without_a_base_sends_the_computed_announcement(monkeypatch):
    import pydatagokr.services.weather as weather_mod
    monkeypatch.setattr(weather_mod, "_latest_base", lambda name: ("20260101", "0500"))
    weather, opener = _weather(_xml([], 0))
    weather.forecast(nx=60, ny=127)                     # base_date/base_time omitted
    query = opener.requests[0].full_url
    assert "base_date=20260101" in query and "base_time=0500" in query
