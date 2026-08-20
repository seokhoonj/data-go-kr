"""Procurement -- 조달청 나라장터 입찰공고정보 on data.go.kr (service 1230000).

나라장터 bid announcements, one operation per 업무구분: `goods` (물품), `services` (용역),
`construction` (공사), `foreign` (외자). The vendor requires the operation to match the
announcement's 업무구분 -- a 공사 announcement answers only on the 공사 operation -- so each
is its own method here. A row is one 입찰공고, keyed by its number and ordinal
(``notice_no`` + ``notice_ord``); the 추정가격·배정예산 are exact won integers, the
announcement/close/opening times are the vendor's ``YYYY-MM-DD HH:MM:SS`` text.

A query is a time window over the 공고 게시일시 (``begin``/``end`` = YYYYMMDDHHMM) plus the
``inqry_div`` basis (``"1"`` 공고게시일시, ``"2"`` 개찰일시). Only a curated header subset of
the vendor's ~100 fields is mapped -- number, name, agencies, method, the money, the times,
and the detail URL. ``clean=True`` (the default) returns typed rows, ``clean=False`` the raw
vendor rows. The service answers XML.
"""

from __future__ import annotations

from typing import Literal, overload

from .. import _spec
from .._spec import CleanRow, Field, Table
from ..session import DataGoKrSession
from ..types import Row

__all__ = ["AGENCY", "BASE_URL", "Procurement", "SERVICE", "TABLES"]

SERVICE = "procurement"
AGENCY = "조달청 (Public Procurement Service, 나라장터)"
BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"

# The header fields shared by every 업무구분's 입찰공고목록. ``budget_amount`` is absent on
# 공사 announcements, so it stays ``None`` there rather than being a separate table.
_BID = (
    Field("bidNtceNo",         "notice_no",        "text", is_key=True),   # 입찰공고번호
    Field("bidNtceOrd",        "notice_ord",       "text", is_key=True),   # 입찰공고차수
    Field("bidNtceNm",         "notice_name",      "text"),                # 입찰공고명
    Field("ntceKindNm",        "notice_kind",      "text"),                # 공고종류(재공고 등)
    Field("ntceInsttNm",       "notice_agency",    "text"),                # 공고기관
    Field("dminsttNm",         "demand_agency",    "text"),                # 수요기관
    Field("bidMethdNm",        "bid_method",       "text"),                # 입찰방식(전자입찰 등)
    Field("cntrctCnclsMthdNm", "contract_method",  "text"),                # 계약체결방법
    Field("bidNtceDt",         "notice_at",        "text"),                # 입찰공고일시
    Field("bidClseDt",         "bid_close_at",     "text"),                # 입찰마감일시
    Field("opengDt",           "opening_at",       "text"),                # 개찰일시
    Field("presmptPrce",       "estimated_price",  "int"),                 # 추정가격(원)
    Field("asignBdgtAmt",      "budget_amount",    "int"),                 # 배정예산(원)
    Field("ntceInsttOfclNm",   "officer_name",     "text"),                # 공고담당자
    Field("bidNtceDtlUrl",     "notice_url",       "text"),                # 공고상세 URL
    Field("rgstDt",            "registered_at",    "text"),                # 등록일시
)

GOODS = Table("goods", "getBidPblancListInfoThngPPSSrch", "basDt", False,
              _BID, is_wide_key=True)
SERVICES = Table("services", "getBidPblancListInfoServcPPSSrch", "basDt", False,
                 _BID, is_wide_key=True)
CONSTRUCTION = Table("construction", "getBidPblancListInfoCnstwkPPSSrch", "basDt", False,
                     _BID, is_wide_key=True)
FOREIGN = Table("foreign", "getBidPblancListInfoFrgcptPPSSrch", "basDt", False,
                _BID, is_wide_key=True)

TABLES: dict[str, Table] = {table.name: table for table in (
    GOODS, SERVICES, CONSTRUCTION, FOREIGN,
)}


class Procurement:
    """The 나라장터 입찰공고 surface. Construct with a data.go.kr decoding key (or let it
    resolve ``DATAGOKR_API_KEY`` / the config file)::

        pr = Procurement()
        rows = pr.services(begin="202608010000", end="202608102359")   # 용역 입찰공고
        rows = pr.construction(begin="202608010000", end="202608102359")
    """

    def __init__(self, api_key: str | None = None, *, timeout: float = 30.0) -> None:
        self._session = DataGoKrSession(BASE_URL, api_key,
                                        timeout=timeout, response_format="xml")

    def __repr__(self) -> str:
        return f"Procurement({self._session!r})"

    @overload
    def goods(self, *, begin: str, end: str, inqry_div: str = ...,
              clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def goods(self, *, begin: str, end: str, inqry_div: str = ...,
              clean: Literal[False]) -> list[Row]: ...
    def goods(self, *, begin: str, end: str, inqry_div: str = "1",
              clean: bool = True) -> list[Row] | list[CleanRow]:
        """물품 입찰공고 over the ``begin``..``end`` window (YYYYMMDDHHMM). ``inqry_div`` is
        the window basis (``"1"`` 공고게시일시, ``"2"`` 개찰일시). ``clean=True`` (the default)
        returns typed rows; ``clean=False`` raw."""
        if clean:
            return self.fetch("goods", begin=begin, end=end, inqry_div=inqry_div, clean=True)
        return self.fetch("goods", begin=begin, end=end, inqry_div=inqry_div, clean=False)

    @overload
    def services(self, *, begin: str, end: str, inqry_div: str = ...,
                 clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def services(self, *, begin: str, end: str, inqry_div: str = ...,
                 clean: Literal[False]) -> list[Row]: ...
    def services(self, *, begin: str, end: str, inqry_div: str = "1",
                 clean: bool = True) -> list[Row] | list[CleanRow]:
        """용역 입찰공고. Args as :meth:`goods`."""
        if clean:
            return self.fetch("services", begin=begin, end=end,
                              inqry_div=inqry_div, clean=True)
        return self.fetch("services", begin=begin, end=end, inqry_div=inqry_div, clean=False)

    @overload
    def construction(self, *, begin: str, end: str, inqry_div: str = ...,
                     clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def construction(self, *, begin: str, end: str, inqry_div: str = ...,
                     clean: Literal[False]) -> list[Row]: ...
    def construction(self, *, begin: str, end: str, inqry_div: str = "1",
                     clean: bool = True) -> list[Row] | list[CleanRow]:
        """공사 입찰공고 (배정예산 미제공 -- ``budget_amount`` is ``None``). Args as
        :meth:`goods`."""
        if clean:
            return self.fetch("construction", begin=begin, end=end,
                              inqry_div=inqry_div, clean=True)
        return self.fetch("construction", begin=begin, end=end,
                          inqry_div=inqry_div, clean=False)

    @overload
    def foreign(self, *, begin: str, end: str, inqry_div: str = ...,
                clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def foreign(self, *, begin: str, end: str, inqry_div: str = ...,
                clean: Literal[False]) -> list[Row]: ...
    def foreign(self, *, begin: str, end: str, inqry_div: str = "1",
                clean: bool = True) -> list[Row] | list[CleanRow]:
        """외자 입찰공고. Args as :meth:`goods`."""
        if clean:
            return self.fetch("foreign", begin=begin, end=end,
                              inqry_div=inqry_div, clean=True)
        return self.fetch("foreign", begin=begin, end=end, inqry_div=inqry_div, clean=False)

    @overload
    def fetch(self, name: str, *, begin: str, end: str, inqry_div: str = ...,
              clean: Literal[True] = ...) -> list[CleanRow]: ...
    @overload
    def fetch(self, name: str, *, begin: str, end: str, inqry_div: str = ...,
              clean: Literal[False]) -> list[Row]: ...
    def fetch(self, name: str, *, begin: str, end: str, inqry_div: str = "1",
              clean: bool = True) -> list[Row] | list[CleanRow]:
        """Any of the four 업무구분 by name (see :meth:`operations`) over one time window.
        ``clean=True`` (the default) returns typed rows; ``clean=False`` raw."""
        try:
            table = TABLES[name]
        except KeyError:
            raise ValueError(f"unknown operation {name!r}; valid: {list(TABLES)}") from None
        rows = self._session.fetch(table.operation, type="xml", inqryDiv=inqry_div,
                                   inqryBgnDt=begin, inqryEndDt=end)
        return _spec.clean(rows, table) if clean else rows

    @staticmethod
    def operations() -> tuple[str, ...]:
        """The operation names :meth:`fetch` accepts."""
        return tuple(TABLES)
