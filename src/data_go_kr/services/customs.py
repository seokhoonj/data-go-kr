"""Customs -- the 관세청 수출입 무역통계 service on data.go.kr (service 1220000).

One operation, ``getNitemtradeList`` (품목별 수출입실적): monthly export/import totals
for one HS code over a year-month range. The service answers JSON through ``_type=json``
(the newer portal parameter, where KOFIA takes ``resultType``).

PENDING: exact vendor token names unconfirmed until the dataset is 활용신청'd (service
1220000); run one live ``getNitemtradeList`` call and pin the ``Field.token`` values,
then remove this note. Until then :data:`ITEM_TRADE` carries the fields the published
spec names -- 신고미화금액 (export USD), 과세가격미화금액 (import USD), 순중량 (net
weight, kg), 수량 (quantity), the HS code, and the Korean/English item names -- under
best-guess tokens, and :meth:`Customs.item_trade` returns RAW rows so it works
regardless of the exact tokens.
"""

from __future__ import annotations

from .._spec import Field, Table
from ..session import DataGoKrSession
from ..types import Row

__all__ = ["AGENCY", "BASE_URL", "Customs", "ITEM_TRADE", "SERVICE", "TABLES"]

SERVICE = "customs"
AGENCY = "관세청 (Korea Customs Service)"
BASE_URL = "https://apis.data.go.kr/1220000/nitemtrade"

# PENDING (see the module docstring): the tokens below are best guesses from the
# published spec; pin them against one live response, then remove this comment.
ITEM_TRADE = Table("item_trade", "getNitemtradeList", "year", True, (
    Field("year",    "period",        "date_ym", is_key=True),   # 기간 (YYYYMM)
    Field("hsSgn",   "hs_code",       "text", is_key=True),      # HS 부호
    Field("statKor", "item_name_kor", "text"),                   # 품목명 (한글)
    Field("statEng", "item_name_eng", "text"),                   # 품목명 (영문)
    Field("expDlr",  "export_usd",    "int"),                    # 수출 신고미화금액 (USD)
    Field("impDlr",  "import_usd",    "int"),                    # 수입 과세가격미화금액 (USD)
    Field("netWgt",  "net_weight",    "int"),                    # 순중량 (kg)
    Field("qty",     "quantity",      "int"),                    # 수량
), is_wide_key=True)

TABLES: dict[str, Table] = {ITEM_TRADE.name: ITEM_TRADE}


class Customs:
    """The 관세청 수출입 무역통계 surface. Construct with a data.go.kr decoding key (or
    let it resolve ``DATA_GO_KR_API_KEY`` / the config file)::

        customs = Customs()
        rows = customs.item_trade("8542", begin="202401", end="202406")
    """

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0) -> None:
        self._session = DataGoKrSession(BASE_URL, api_key,
                                        timeout=timeout, json_param="_type")

    def __repr__(self) -> str:
        return f"Customs({self._session!r})"

    def item_trade(self, hs_code: str, *, begin: str, end: str) -> list[Row]:
        """품목별 수출입실적 (``getNitemtradeList``) for one HS code, monthly over
        ``begin``/``end`` = YYYYMM. Returns RAW vendor rows (see the module's PENDING
        note); frame them with ``pandas.DataFrame(rows)`` and rename by hand until the
        :data:`ITEM_TRADE` tokens are pinned."""
        return self._session.fetch("getNitemtradeList",
                                   strtYymm=begin, endYymm=end, hsSgn=hs_code)
