# data-go-kr

**English** | [한국어](README.md)

Read Korean government open-data services from **data.go.kr** with one key: KOFIA
market statistics (investor deposits, margin loans, funds, CMA, ELS/DLS, trusts,
overseas derivatives) and Korea Customs Service item trade (monthly exports/imports by
HS code). Zero runtime dependencies; rows come back as `list[dict]` that
`pandas.DataFrame` / `polars.DataFrame` accept directly.

> Scaffolding README -- the section skeleton is final, the prose is not.

## 1. Install

```bash
pip install data-go-kr
```

The package needs a data.go.kr service key -- the **decoding** (raw) form, not the
percent-escaped encoding form. Store it once in
`~/.config/data-go-kr/credentials.json`:

```json
{ "DATA_GO_KR_API_KEY": "your-decoding-key" }
```

or set the `DATA_GO_KR_API_KEY` environment variable, or pass `api_key=` directly.
Each dataset must also be applied for (활용신청) on your data.go.kr account.

## 2. Quick start

```python
from data_go_kr import DataGoKr

client = DataGoKr()
rows = client.kofia.market_funds(begin="20240101", end="20240131")
raw  = client.customs.item_trade("8542", begin="202401", end="202406")
```

```python
# pandas
import pandas as pd
pd.DataFrame(rows)

# polars
import polars as pl
pl.DataFrame(rows)
```

## 3. Services

Supported services -- this table matches the offline catalog (`data-go-kr list` /
`catalog.services()`):

| accessor | agency · statistics | service ID | format | operations |
|---|---|---|---|---|
| `client.kofia` | 금융투자협회 종합통계 (KOFIA) | 1160100 | JSON | 8 -- `market_funds` · `credit_balance` · `trust_scale` · `fund_net_asset` · `cma_status` · `dls_dlb` · `els_elb` · `overseas_derivatives` |
| `client.customs` | 관세청 품목별 수출입실적 (Korea Customs) | 1220000 | XML | `item_trade` -- monthly export/import value and weight by HS code |

- Each service must be applied for (활용신청) separately on your account (see Sec. 5).
- `clean=True` (default) returns typed snake_case columns; `clean=False` the raw vendor
  tokens.

**Offline browse (no key):** `catalog.services()` / `catalog.operations("kofia")` /
`catalog.fields("kofia", "market_funds")` (the per-operation clean column schema -- token,
column, kind, is_key). From the CLI: `data-go-kr list`, `data-go-kr fields kofia market_funds`.

**Cleaning on its own:** the public `clean(rows, table)` with the per-operation `Table` /
`Field` specs turns raw vendor rows into typed snake_case columns without a client
(`from data_go_kr import clean`).

### Adding a service

data.go.kr hosts thousands of agency APIs and they change over time, so services are
additive. The neutral `DataGoKrSession` transport already handles the portal contract
(the decoding-key single-encode, paging, both error envelopes, the reason-code
vocabulary) for every service, so a new one is a small, repeatable module -- nothing in
the transport changes:

1. Add `src/data_go_kr/services/<agency>.py` with a surface class that builds a
   `DataGoKrSession(base_url, api_key, timeout=..., json_param=...)` at that service's
   base URL (`json_param` is `"resultType"` for most, `"_type"` for some -- check the
   service's spec page).
2. Declare its operations and a `Table` spec per operation (`Field(token, column, kind)`)
   -- the one declarative place vendor tokens map to clean columns, so a later field
   change is a one-line edit, not a code change.
3. Register the service in `catalog.py` so `data-go-kr list` and the offline catalog show it.
4. Apply for the dataset (활용신청) on your account, then pin any pending field tokens
   with one live call.

## 4. Command line

```bash
data-go-kr list                                                # offline, no key
data-go-kr fields kofia market_funds                           # offline column schema
data-go-kr kofia market_funds --begin 20240101 --end 20240131
data-go-kr customs item_trade 8542 --begin 202401 --end 202406
```

Add `--json` for machine-readable output.

## 5. Errors & operational notes

Every operational error derives from `DataGoKrError`: `DataGoKrConfigError` (no key),
`DataGoKrAuthError` (key rejected / dataset not applied for), `DataGoKrRateLimitError`
(traffic limit), `DataGoKrResponseError` (vendor error code), `DataGoKrNetworkError`
(transport). Error messages never carry the key or the request URL.

The portal's reason codes map to those classes as follows (a `DataGoKrResponseError`
preserves the code on `.code`, so you can still branch on 1/4/12/99 yourself):

| code | meaning | class |
|---|---|---|
| 1  | APPLICATION_ERROR (portal server) | `DataGoKrResponseError` |
| 4  | HTTP_ERROR (provider server) | `DataGoKrResponseError` |
| 12 | NO_OPENAPI_SERVICE_ERROR (service gone/deprecated) | `DataGoKrResponseError` |
| 20 | SERVICE_ACCESS_DENIED (not applied / suspended) | `DataGoKrAuthError` |
| 22 | daily traffic exceeded | `DataGoKrRateLimitError` |
| 23 | per-second throttle | `DataGoKrRateLimitError` |
| 30 | SERVICE_KEY_IS_NOT_REGISTERED | `DataGoKrAuthError` |
| 31 | DEADLINE_HAS_EXPIRED | `DataGoKrAuthError` |
| 99 | UNKNOWN_ERROR | `DataGoKrResponseError` |

- **Activation (활용신청).** Each dataset is applied for separately; a call to one you
  have not been approved for fails with code 30 exactly as a bad key does. An API is
  either auto-approved (자동승인, instant) or review-approved (심의승인, after the
  provider approves) -- check its "심의유형" on the spec page and the status under
  마이페이지 > 데이터 활용 > Open API > 활용신청 현황.
- **Traffic.** One key has a per-API daily call cap (code 22) that resets at midnight
  KST; a development account has a low default, raised by switching to an operating
  account. Code 22/23 are `DataGoKrRateLimitError` and should not be retried immediately.
- **Deprecations.** A withdrawn endpoint returns code 12; the provider announces changes
  on the data.go.kr API notices board (`nttApiYn=Y`).
- **CORS is not a concern.** This is a server-side client, so the browser Same-Origin
  policy that blocks some providers' APIs from front-end JavaScript never applies here.

## 6. AI coding agents

- This repo doubles as a plugin marketplace for Claude Code and Codex.
- It ships three skills -- `list`, `kofia`, `customs` -- each a thin wrapper over the
  `data-go-kr` command.
- Install the package first (`list` works without a key; the fetches need one).

### 6.1 Claude Code (chat)

```
/plugin marketplace add seokhoonj/data-go-kr
/plugin install data-go-kr@data-go-kr
```

### 6.2 Codex (terminal)

```
codex plugin marketplace add seokhoonj/data-go-kr
codex plugin add data-go-kr@data-go-kr
```

## 7. License

The **package code** is MIT (see `LICENSE`).

The **data** it fetches belongs to the providing agencies. Under Korea's Public Data Act
(공공데이터법 제3조) public data is commercially usable in principle, unless a specific
dataset restricts it or an agency withdraws it (제28조). Check the individual dataset's
terms on data.go.kr before redistributing its data.
