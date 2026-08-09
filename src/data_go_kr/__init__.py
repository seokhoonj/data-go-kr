"""data-go-kr -- read Korean government open-data services from data.go.kr.

    from data_go_kr import DataGoKr

    client = DataGoKr()                    # or set DATA_GO_KR_API_KEY (the *decoding* key)
    rows = client.kofia.market_funds(begin="20240101", end="20240131")
    raw  = client.customs.item_trade("8542", begin="202401", end="202406")

One key, many services: the shared :class:`DataGoKrSession` speaks the portal's common
envelope and paging protocol, and each wrapped agency -- 금융투자협회 (KOFIA) 종합통계,
관세청 수출입 무역통계 -- is a thin surface over it. Rows come back as ``list[dict]``
with the vendor's own field names (or cleaned to typed snake_case columns via the
per-operation table specs) -- frame them your own way, e.g. ``pandas.DataFrame(rows)`` or
``polars.DataFrame(rows)``. The offline :mod:`data_go_kr.catalog` lists every service and
operation without a call.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from . import catalog
from ._spec import Field, Table, clean
from .client import DataGoKr
from .errors import (
    DataGoKrAuthError,
    DataGoKrConfigError,
    DataGoKrError,
    DataGoKrNetworkError,
    DataGoKrRateLimitError,
    DataGoKrResponseError,
)
from .services.customs import Customs
from .services.kofia import Kofia
from .session import DataGoKrSession
from .types import Row

try:
    __version__ = version("data-go-kr")   # single source of truth: pyproject.toml
except PackageNotFoundError:              # running from source without an install
    __version__ = "0.0.0+unknown"

__all__ = [
    "Customs",
    "DataGoKr",
    "DataGoKrAuthError",
    "DataGoKrConfigError",
    "DataGoKrError",
    "DataGoKrNetworkError",
    "DataGoKrRateLimitError",
    "DataGoKrResponseError",
    "DataGoKrSession",
    "Field",
    "Kofia",
    "Row",
    "Table",
    "catalog",
    "clean",
]
