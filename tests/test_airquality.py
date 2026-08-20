"""AirQuality -- XML session, int/decimal measurements, both operations, offline."""

import pytest

from pydatagokr.services.airquality import AirQuality


def _xml(items, total):
    rows = "".join(
        "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
        for item in items)
    return (f"<response><header><resultCode>00</resultCode>"
            f"<resultMsg>NORMAL_CODE</resultMsg></header>"
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


_SIDO_ROW = {
    "sidoName": "서울", "stationName": "중구", "dataTime": "2026-08-12 01:00",
    "khaiValue": "54", "khaiGrade": "2",
    "pm10Value": "7", "pm10Grade": "1", "pm10Flag": "",
    "pm25Value": "7", "pm25Grade": "1", "pm25Flag": "",
    "so2Value": "0.002", "so2Grade": "1", "so2Flag": "",
    "coValue": "0.2", "coGrade": "1", "coFlag": "",
    "o3Value": "0.034", "o3Grade": "2", "o3Flag": "",
    "no2Value": "0.005", "no2Grade": "1", "no2Flag": "",
}


def _air(raw):
    air = AirQuality(api_key="k")
    opener = _FakeOpener(raw)
    air._session._opener = opener
    return air, opener


def test_by_sido_types_the_measurements():
    air, _ = _air(_xml([_SIDO_ROW], 1))
    row = air.by_sido(sido="서울")[0]
    assert row["sido"] == "서울"
    assert row["station"] == "중구"
    assert row["measured_at"] == "2026-08-12 01:00"
    assert row["pm10"] == 7 and row["pm25"] == 7 and row["khai"] == 54   # int
    assert row["o3"] == pytest.approx(0.034) and row["no2"] == pytest.approx(0.005)  # decimal
    assert row["pm10_flag"] is None                                      # empty -> None


def test_by_sido_raw_passthrough_keeps_vendor_tokens():
    air, _ = _air(_xml([_SIDO_ROW], 1))
    assert air.by_sido(sido="서울", clean=False) == [_SIDO_ROW]


def test_sido_operation_and_filter_reach_the_vendor():
    air, opener = _air(_xml([], 0))
    air.by_sido(sido="부산")
    query = opener.requests[0].full_url
    assert "getCtprvnRltmMesureDnsty" in query
    assert "sidoName=" in query   # 부산 is url-encoded; its presence is the point


def test_by_sido_with_no_rows_returns_empty_list():
    air, _ = _air(_xml([], 0))
    assert air.by_sido(sido="서울") == []


def test_by_station_sends_the_station_and_data_term():
    air, opener = _air(_xml([], 0))
    air.by_station(station="종로구", data_term="MONTH")
    query = opener.requests[0].full_url
    assert "getMsrstnAcctoRltmMesureDnsty" in query
    assert "stationName=" in query
    assert "dataTerm=MONTH" in query
