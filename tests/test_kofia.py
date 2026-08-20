"""KOFIA -- every operation's typed row, its vendor path, and the right date-bound param
(daily basDt vs monthly basYm, bounds truncated to YYYYMM), over the JSON session, offline."""

import json

import pytest

from pydatagokr.services.kofia import KOFIA


def _json(items, total):
    body = {"response": {"header": {"resultCode": "00", "resultMsg": "OK"},
                         "body": {"items": {"item": items}, "totalCount": total}}}
    return json.dumps(body).encode()


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


def _kofia(raw):
    kofia = KOFIA(api_key="k")
    opener = _FakeOpener(raw)
    kofia._session._opener = opener
    return kofia, opener


# (operation name, one representative raw row, its exact cleaned row, the vendor operation
# path, the begin/end bound params) -- the daily tables filter on basDt (full YYYYMMDD), the
# monthly ones on their date_token truncated to YYYYMM (basYm for 신탁규모, basDt for the rest).
_CASES = [
    (
        "market_funds",
        {"basDt": "20240131", "invrDpsgAmt": "50,123", "onbdDrvPrdTrRcAdvAmt": "1,000",
         "toCstRpchCndBndSlgBal": "200", "brkTrdUcolMny": "30",
         "brkTrdUcolMnyVsOppsTrdAmt": "77", "ucolMnyVsOppsTrdRlImpt": "8.5"},
        {"base_date": "2024-01-31", "investor_deposit": 50123, "derivatives_deposit": 1000,
         "customer_rp_sale_balance": 200, "brokerage_receivable": 30,
         "forced_sell_amount": 77, "forced_sell_to_receivable_ratio": 8.5},
        "getSecuritiesMarketTotalCapitalInfo",
        "beginBasDt=20240131", "endBasDt=20240315",
    ),
    (
        "credit_balance",
        {"basDt": "20240131", "crdTrFingWhl": "1,000", "crdTrFingScrs": "600",
         "crdTrFingKosdaq": "400", "crdTrLndrWhl": "50", "crdTrLndrScrs": "30",
         "crdTrLndrKosdaq": "20", "sbscCapLn": "5", "dpsgScrtMogFing": "90"},
        {"base_date": "2024-01-31", "margin_loan_total": 1000, "margin_loan_kospi": 600,
         "margin_loan_kosdaq": 400, "stock_loan_total": 50, "stock_loan_kospi": 30,
         "stock_loan_kosdaq": 20, "subscription_loan": 5, "collateral_loan": 90},
        "getGrantingOfCreditBalanceInfo",
        "beginBasDt=20240131", "endBasDt=20240315",
    ),
    (
        "fund_net_asset",
        {"basDt": "20240131", "ctg": "PEF", "tstMthdCtg": "공모", "nPptTotAmt": "9,999"},
        {"base_date": "2024-01-31", "fund_type": "PEF", "offering_type": "공모",
         "net_asset_total": 9999},
        "getFundTotalNetEssetInfo",
        "beginBasDt=20240131", "endBasDt=20240315",
    ),
    (
        "cma_status",
        {"basDt": "20240131", "mngInvTgt": "RP형", "invrCtg": "개인", "scrtCmpyCnt": "10",
         "actCnt": "1,234", "actBal": "5,000"},
        {"base_date": "2024-01-31", "management_target": "RP형", "investor_type": "개인",
         "securities_firm_count": 10, "account_count": 1234, "account_balance": 5000},
        "getCMAStatus",
        "beginBasDt=20240131", "endBasDt=20240315",
    ),
    (
        "trust_scale",
        {"basYm": "202401", "bzds": "증권", "tstCtg": "금전신탁", "kind": "특정금전",
         "iqBs": "수탁총액", "val": "12,345"},
        {"base_ym": "2024-01", "sector": "증권", "trust_type": "금전신탁",
         "trust_kind": "특정금전", "measure_basis": "수탁총액", "measure_value": 12345},
        "getTrustScaleInfo",
        "beginBasYm=202401", "endBasYm=202403",
    ),
    (
        "dls_dlb",
        {"basDt": "202401", "ctgDlbDls": "합계", "ctgPrplcPsub": "공모",
         "presCtg": "발행실적", "amt": "9,000", "ccnt": "12"},
        {"base_ym": "2024-01", "product_type": "합계", "offering_type": "공모",
         "status_type": "발행실적", "amount_krw": 9000, "deal_count": 12},
        "getDLSAndDLBInfo",
        "beginBasDt=202401", "endBasDt=202403",
    ),
    (
        "els_elb",
        {"basDt": "202401", "ctgElbEls": "ELS", "ctgPrplcPsub": "공모",
         "presCtg": "발행실적", "amt": "8,000", "ccnt": "7"},
        {"base_ym": "2024-01", "product_type": "ELS", "offering_type": "공모",
         "status_type": "발행실적", "amount_krw": 8000, "deal_count": 7},
        "getELSAndELBInfo",
        "beginBasDt=202401", "endBasDt=202403",
    ),
    (
        "overseas_derivatives",
        {"basDt": "202401", "byPrdGrp": "통화", "actCtg": "자기", "ctgBsonCntrForm": "콜옵션",
         "prdNm": "EUR/USD", "brkPn": "개인", "xchNm": "CME", "csfBsonCntrForm": "옵션",
         "byNtnl": "미국", "prdGrp": "통화선물", "trqu": "5", "trPrcUsd": "1,000"},
        {"base_ym": "2024-01", "product_group": "통화", "account_type": "자기",
         "contract_form": "콜옵션", "product_name": "EUR/USD", "customer_type": "개인",
         "exchange": "CME", "contract_class": "옵션", "country": "미국",
         "underlying_asset_group": "통화선물", "trade_volume": 5, "trade_value_usd": 1000},
        "getDerivationProductTradingInfo",
        "beginBasDt=202401", "endBasDt=202403",
    ),
]


@pytest.mark.parametrize("name,raw_row,clean_row,operation,begin_param,end_param", _CASES,
                         ids=[case[0] for case in _CASES])
def test_every_operation_types_its_row_and_wires_the_bounds(
        name, raw_row, clean_row, operation, begin_param, end_param):
    kofia, opener = _kofia(_json([raw_row], 1))
    rows = kofia.fetch(name, begin="20240131", end="20240315")
    assert rows == [clean_row]                       # exact typed row, all columns
    query = opener.requests[0].full_url
    assert operation in query                        # the operation's own vendor path
    assert begin_param in query                      # basDt (daily) or basYm/basDt (monthly)
    assert end_param in query                        # monthly bounds truncated to YYYYMM
