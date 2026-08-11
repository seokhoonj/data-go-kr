"""Per-agency service surfaces over the shared data.go.kr transport.

Each module wraps one data.go.kr service: its base URL, its operations, and the
:class:`~data_go_kr._spec.Table` specs mapping the vendor's field tokens to clean
columns. The surfaces share nothing but :class:`~data_go_kr.session.DataGoKrSession`.
"""

from __future__ import annotations

from .customs import Customs
from .holidays import Holidays
from .kofia import Kofia
from .realestate import Realestate
from .weather import Weather

__all__ = ["Customs", "Holidays", "Kofia", "Realestate", "Weather"]
