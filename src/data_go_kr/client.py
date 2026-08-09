"""DataGoKr -- the entry point.

Built from one data.go.kr service key (constructor, ``DATA_GO_KR_API_KEY`` env, or the
config file), it exposes the wrapped services as lazy sub-surfaces -- ``kofia``
(금융투자협회 종합통계) and ``customs`` (관세청 수출입 무역통계) -- each holding its own
:class:`~data_go_kr.session.DataGoKrSession` built with the same key and timeout. A
surface is constructed on first access (``@cached_property``), so building ``DataGoKr()``
itself needs no key at all.
"""

from __future__ import annotations

from functools import cached_property

from .services.customs import Customs
from .services.kofia import Kofia

__all__ = ["DataGoKr"]


class DataGoKr:
    """Client for the wrapped data.go.kr services. Groups them as sub-surfaces::

        client = DataGoKr()                    # or set DATA_GO_KR_API_KEY
        rows = client.kofia.market_funds(begin="20240101", end="20240131")
        raw  = client.customs.item_trade("8542", begin="202401", end="202406")

    One data.go.kr account key serves every dataset it has applied for (활용신청); a call
    to one not yet approved raises :class:`~data_go_kr.errors.DataGoKrAuthError`.
    """

    _api_key: str | None
    _timeout: float

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0) -> None:
        self._api_key = api_key
        self._timeout = timeout

    def __repr__(self) -> str:
        # Never shows the service key, in whole or in part.
        return "DataGoKr(...)"

    @cached_property
    def kofia(self) -> Kofia:
        """금융투자협회 (KOFIA) 종합통계 -- 예탁금, 신용잔고, 펀드, CMA, ELS/DLS, 신탁,
        해외파생."""
        return Kofia(self._api_key, timeout=self._timeout)

    @cached_property
    def customs(self) -> Customs:
        """관세청 수출입 무역통계 -- 품목별(HS) 수출입실적."""
        return Customs(self._api_key, timeout=self._timeout)
