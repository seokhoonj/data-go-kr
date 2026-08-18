# data-go-kr

**English** | [한국어](README.md)

Read Korean government open-data services from **data.go.kr** with one key: KMA (기상청)
village weather forecasts (short-range, ultra-short, nowcast) and AirKorea (에어코리아)
air-quality measurements (PM, ozone, ...), Korea Astronomy and Space Science Institute
(KASI) special days (public holidays, 24 solar terms, ...), Ministry of Land (MOLIT)
apartment real-transaction prices (sale, rent, presale), KMA medium-range forecasts
(days 4-10, land and temperature), Korea Public Procurement Service (나라장터) bid
announcements (goods, services, construction, foreign), Korea Customs Service item trade
(monthly exports/imports by HS code), and KOFIA market statistics (investor deposits,
margin loans, funds, CMA, ELS/DLS, trusts, overseas derivatives). Zero runtime
dependencies; rows come back as `list[dict]` that `pandas.DataFrame` / `polars.DataFrame`
accept directly.

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
rows   = client.weather.forecast(base_date="20260811", base_time="0500", nx=60, ny=127)
trades = client.realestate.apt_trade(region_code="11110", deal_ym="202401")
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
| `client.weather` | 기상청 동네예보 (KMA village forecast) | 1360000 | XML | 3 -- `forecast` · `ultra_forecast` · `nowcast` |
| `client.airquality` | 한국환경공단 에어코리아 대기오염정보 (AirKorea) | B552584 | XML | 2 -- `by_sido` · `by_station` |
| `client.holidays` | 한국천문연구원 특일 정보 (KASI) | B090041 | XML | 5 -- `holidays` · `national_holidays` · `anniversaries` · `solar_terms` · `sundry_days` |
| `client.realestate` | 국토교통부 아파트 실거래가 (MOLIT RTMS) | 1613000 | XML | 4 -- `apt_trade` · `apt_trade_detail` · `apt_rent` · `apt_presale` |
| `client.midforecast` | 기상청 중기예보 (KMA medium-range) | 1360000 | XML | 2 -- `land` (강수·날씨) · `temperature` (최저·최고) |
| `client.procurement` | 조달청 나라장터 입찰공고 (Public Procurement) | 1230000 | XML | 4 -- `goods` · `services` · `construction` · `foreign` |
| `client.customs` | 관세청 품목별 수출입실적 (Korea Customs) | 1220000 | XML | `item_trade` -- monthly export/import value and weight by HS code |
| `client.kofia` | 금융투자협회 종합통계 (KOFIA) | 1160100 | JSON | 8 -- `market_funds` · `credit_balance` · `trust_scale` · `fund_net_asset` · `cma_status` · `dls_dlb` · `els_elb` · `overseas_derivatives` |

- Each service must be applied for (활용신청) separately on your account (see Sec. 6).
- `clean=True` (default) returns typed snake_case columns; `clean=False` the raw vendor
  tokens.

## 4. Command line

The call shape is `data-go-kr <service> <operation> [options]`. List every service and
operation with `data-go-kr list` (offline, no key); see an operation's options with
`data-go-kr <service> <operation> --help`. Add `--json` to any command for machine-readable
output.

**weather — 기상청 동네예보 (village forecast)** · `forecast` (단기) / `ultra_forecast`
(초단기) / `nowcast` (실황)

```bash
data-go-kr weather forecast --base-date 20260811 --base-time 0500 --nx 60 --ny 127
```

`--nx`/`--ny` are the KMA 5km grid coordinates (Seoul Jongno ≈ 60,127); `--base-time` is the
announcement time (0200, 0500, …, 2300). Get the grid from a lat/lon with
`data-go-kr grid <lat> <lon>`.

**airquality — 에어코리아 (AirKorea)** · `by_sido` (by province) / `by_station` (by station)

```bash
data-go-kr airquality by_sido 서울
data-go-kr airquality by_station 종로구 --data-term DAILY
```

`by_sido` takes a 시도 (province) name, `by_station` a station name. `--data-term` is the
window (DAILY / MONTH / 3MONTH).

**holidays — 한국천문연구원 (KASI)** · `holidays` (default) / `national_holidays` /
`anniversaries` / `solar_terms` / `sundry_days`

```bash
data-go-kr holidays --year 2026
data-go-kr holidays solar_terms --year 2026
```

`--year` is required; `--month` (1–12) narrows to one month (`solar_terms` = the 24 절기).

**realestate — 국토교통부 (MOLIT RTMS)** · `apt_trade` (sale) / `apt_trade_detail` (sale
detail) / `apt_rent` (rent) / `apt_presale` (presale)

```bash
data-go-kr realestate apt_trade 11110 --deal-ym 202401
```

`11110` is the first 5 digits of the 법정동 code (LAWD_CD, Jongno-gu) -- find it with
`data-go-kr lawd 종로구`; `--deal-ym` is the contract year-month.

**midforecast — 기상청 중기예보 (medium-range)** · `land` (강수·날씨) / `temperature`
(최저·최고)

```bash
data-go-kr midforecast land --region 11B00000 --base-time 202608110600
```

`--region` is the forecast-zone code (11B00000 = Seoul/Incheon/Gyeonggi) -- find it with
`data-go-kr land-region 서울` / `data-go-kr temp-region 서울`; `--base-time` is the
announcement time (0600 or 1800 daily).

**procurement — 조달청 나라장터 (Public Procurement)** · `goods` (물품) / `services` (용역) /
`construction` (공사) / `foreign` (외자)

```bash
data-go-kr procurement services --begin 202608010000 --end 202608102359
```

`--begin`/`--end` are the posting window (YYYYMMDDHHMM, minute precision); `--inqry-div`
switches the basis (1 posting time / 2 opening time).

**customs — 관세청 (Korea Customs)** · `item_trade`

```bash
data-go-kr customs item_trade 8542 --begin 202401 --end 202406
```

`8542` is the HS code (electronic integrated circuits); the range is YYYYMM.

**kofia — 금융투자협회 (KOFIA)** · `market_funds` and 7 more operations (see `data-go-kr list`)

```bash
data-go-kr kofia market_funds --begin 20240101 --end 20240131
```

`--begin`/`--end` are YYYYMMDD; monthly operations take YYYYMM.

## 5. AI coding agents

- This repo doubles as a plugin marketplace for Claude Code and Codex.
- It ships nine skills -- `list`, `weather`, `airquality`, `holidays`, `realestate`,
  `midforecast`, `procurement`, `customs`, `kofia` -- each a thin wrapper over the
  `data-go-kr` command.
- Install the package first (`list` works without a key; the fetches need one).

### 5.1 Claude Code (chat)

```
/plugin marketplace add seokhoonj/data-go-kr
/plugin install data-go-kr@data-go-kr
```

### 5.2 Codex (terminal)

```
codex plugin marketplace add seokhoonj/data-go-kr
codex plugin add data-go-kr@data-go-kr
```

## 6. Errors & operational notes

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

## 7. License

The **package code** is MIT (see `LICENSE`).

The **data** it fetches belongs to the providing agencies. Under Korea's Public Data Act
(공공데이터법 제3조) public data is commercially usable in principle, unless a specific
dataset restricts it or an agency withdraws it (제28조). Check the individual dataset's
terms on data.go.kr before redistributing its data.
