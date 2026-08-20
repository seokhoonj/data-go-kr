"""Weather -- 기상청 동네예보 on data.go.kr (service 1360000, VilageFcstInfoService_2.0).

Three operations for one 5km grid cell (``nx``/``ny``): the 단기예보 (`forecast`, to ~3 days),
the 초단기예보 (`ultra_forecast`, to 6 hours), and the 초단기실황 (`nowcast`, the latest
observation). A forecast is a long table -- one row per weather item (``category`` = TMP 기온,
POP 강수확률, SKY 하늘상태, PTY 강수형태, REH 습도, WSD 풍속, ...) per forecast time, its
value in ``forecast_value``; a nowcast carries the same item categories with an
``observed_value``. The value's meaning depends on ``category`` (a temperature, a code, a
percentage), so it is kept as text. ``clean=True`` (the default) returns typed rows,
``clean=False`` the raw vendor rows.

Pass ``base_date`` (YYYYMMDD) / ``base_time`` (HHMM) = the announcement time, and the grid
``nx``/``ny``. The service answers XML.
"""

from __future__ import annotations

from typing import Literal, overload

from .. import _spec
from .._spec import CleanRow, Field, Table
from ..session import DataGoKrSession
from ..types import Row

__all__ = ["AGENCY", "BASE_URL", "TABLES", "Weather", "SERVICE"]

SERVICE = "weather"
AGENCY = "기상청 (Korea Meteorological Administration)"
BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"

# A forecast row: the announcement (base), the item, the forecast time, and the value.
_FORECAST = (
    Field("baseDate",  "base_date",      "date_ymd"),                # 발표일자
    Field("baseTime",  "base_time",      "text"),                    # 발표시각 (HHMM)
    Field("category",  "category",       "text", is_key=True),       # 예보 항목 (TMP/POP/SKY...)
    Field("fcstDate",  "forecast_date",  "date_ymd", is_key=True),   # 예보일자
    Field("fcstTime",  "forecast_time",  "text", is_key=True),       # 예보시각 (HHMM)
    Field("fcstValue", "forecast_value", "text"),                    # 예보값 (항목별 해석)
    Field("nx",        "nx",             "int", is_key=True),        # 격자 X
    Field("ny",        "ny",             "int", is_key=True),        # 격자 Y
)

# A nowcast row: the same item categories, observed rather than forecast.
_NOWCAST = (
    Field("baseDate",  "base_date",      "date_ymd"),
    Field("baseTime",  "base_time",      "text"),
    Field("category",  "category",       "text", is_key=True),
    Field("obsrValue", "observed_value", "text"),                    # 관측값
    Field("nx",        "nx",             "int", is_key=True),
    Field("ny",        "ny",             "int", is_key=True),
)

FORECAST = Table("forecast", "getVilageFcst", "basDt", False, _FORECAST,
                 is_wide_key=True)
ULTRA_FORECAST = Table("ultra_forecast", "getUltraSrtFcst", "basDt", False, _FORECAST,
                       is_wide_key=True)
NOWCAST = Table("nowcast", "getUltraSrtNcst", "basDt", False, _NOWCAST,
                is_wide_key=True)

TABLES: dict[str, Table] = {
    table.name: table for table in (FORECAST, ULTRA_FORECAST, NOWCAST)}


class Weather:
    """The 동네예보 surface. Construct with a data.go.kr decoding key (or let it resolve
    ``DATAGOKR_API_KEY`` / the config file)::

        weather = Weather()
        rows = weather.forecast(base_date="20260811", base_time="0500", nx=60, ny=127)
    """

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0) -> None:
        self._session = DataGoKrSession(BASE_URL, api_key,
                                        timeout=timeout, response_format="xml")

    def __repr__(self) -> str:
        return f"Weather({self._session!r})"

    @overload
    def forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                 clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                 clean: Literal[False]) -> list[Row]: ...
    def forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                 clean: bool = True) -> list[Row] | list[CleanRow]:
        """단기예보 (``getVilageFcst``), to ~3 days, for the grid cell ``nx``/``ny`` at the
        ``base_date``/``base_time`` announcement. Args as :meth:`fetch`."""
        if clean:
            return self.fetch("forecast", base_date=base_date, base_time=base_time,
                              nx=nx, ny=ny, clean=True)
        return self.fetch("forecast", base_date=base_date, base_time=base_time,
                          nx=nx, ny=ny, clean=False)

    @overload
    def ultra_forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                       clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def ultra_forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                       clean: Literal[False]) -> list[Row]: ...
    def ultra_forecast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                       clean: bool = True) -> list[Row] | list[CleanRow]:
        """초단기예보 (``getUltraSrtFcst``), to 6 hours. Args as :meth:`fetch`."""
        if clean:
            return self.fetch("ultra_forecast", base_date=base_date, base_time=base_time,
                              nx=nx, ny=ny, clean=True)
        return self.fetch("ultra_forecast", base_date=base_date, base_time=base_time,
                          nx=nx, ny=ny, clean=False)

    @overload
    def nowcast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def nowcast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                clean: Literal[False]) -> list[Row]: ...
    def nowcast(self, *, base_date: str, base_time: str, nx: int, ny: int,
                clean: bool = True) -> list[Row] | list[CleanRow]:
        """초단기실황 (``getUltraSrtNcst``), the latest observation. Args as :meth:`fetch`."""
        if clean:
            return self.fetch("nowcast", base_date=base_date, base_time=base_time,
                              nx=nx, ny=ny, clean=True)
        return self.fetch("nowcast", base_date=base_date, base_time=base_time,
                          nx=nx, ny=ny, clean=False)

    @overload
    def fetch(self, name: str, *, base_date: str, base_time: str, nx: int, ny: int,
              clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def fetch(self, name: str, *, base_date: str, base_time: str, nx: int, ny: int,
              clean: Literal[False]) -> list[Row]: ...
    def fetch(self, name: str, *, base_date: str, base_time: str, nx: int, ny: int,
              clean: bool = True) -> list[Row] | list[CleanRow]:
        """Any of the three operations by name (see :meth:`operations`) for one grid cell.
        ``base_date`` = YYYYMMDD, ``base_time`` = HHMM (the announcement time), ``nx``/``ny``
        the 기상청 5km grid. ``clean=True`` (the default) returns typed rows; ``clean=False``
        raw."""
        try:
            table = TABLES[name]
        except KeyError:
            raise ValueError(f"unknown operation {name!r}; valid: {list(TABLES)}") from None
        rows = self._session.fetch(table.operation, base_date=base_date, base_time=base_time,
                                   nx=str(nx), ny=str(ny))
        return _spec.clean(rows, table) if clean else rows

    @staticmethod
    def operations() -> tuple[str, ...]:
        """The operation names :meth:`fetch` accepts."""
        return tuple(TABLES)
