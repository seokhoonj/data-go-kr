"""Per-agency service surfaces over the shared data.go.kr transport.

Each module wraps one data.go.kr service: its base URL, its operations, and the
:class:`~pydatagokr._spec.Table` specs mapping the vendor's field tokens to clean
columns. The surfaces share nothing but :class:`~pydatagokr.session.DataGoKrSession`.
"""

from __future__ import annotations

from .airquality import AirQuality
from .customs import Customs
from .holidays import Holidays
from .kofia import Kofia
from .midforecast import MidForecast
from .procurement import Procurement
from .realestate import Realestate
from .weather import Weather

__all__ = ["AirQuality", "Customs", "Holidays", "Kofia", "MidForecast",
           "Procurement", "Realestate", "Weather"]
