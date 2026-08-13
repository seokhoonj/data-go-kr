# data-go-kr

**한국어** | [English](README.en.md)

공공데이터포털 **data.go.kr**의 오픈 API를 키 하나로 읽어옵니다: 기상청 동네예보(단기·
초단기·실황)와 에어코리아 대기오염정보(미세먼지·오존 등), 한국천문연구원 특일 정보(공휴일·
24절기 등), 국토교통부 아파트 실거래가(매매·전월세·분양권), 기상청 중기예보(4~10일 육상·
기온), 조달청 나라장터 입찰공고(물품·용역·공사·외자), 관세청 수출입 무역통계(HS 부호별 월간
수출입실적), 금융투자협회 종합통계(투자자예탁금, 신용공여잔고, 펀드, CMA, ELS/DLS, 신탁,
해외파생). 런타임 의존성 없이 표준 라이브러리만 쓰고, 결과는 `pandas.DataFrame` /
`polars.DataFrame`이 바로 받는 `list[dict]`입니다.

## 1. 설치

```bash
pip install data-go-kr
```

data.go.kr 인증키가 필요합니다 -- 반드시 **디코딩**(원문) 키를 쓰세요(퍼센트
인코딩된 인코딩 키는 이중 인코딩되어 거부됩니다). 한 번 저장해 두려면
`~/.config/data-go-kr/credentials.json`:

```json
{ "DATA_GO_KR_API_KEY": "발급받은-디코딩-키" }
```

환경변수 `DATA_GO_KR_API_KEY`나 `api_key=` 인자로도 넣을 수 있습니다. 각
데이터셋은 계정에서 별도로 활용신청해야 합니다.

## 2. 빠른 시작

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

## 3. 서비스

지원 서비스 -- 아래 표는 오프라인 카탈로그(`data-go-kr list` / `catalog.services()`)와
동일합니다:

| 접근자 | 기관 · 통계 | 서비스ID | 포맷 | 오퍼레이션 |
|---|---|---|---|---|
| `client.weather` | 기상청 동네예보 | 1360000 | XML | 3개 -- `forecast`(단기예보) · `ultra_forecast`(초단기예보) · `nowcast`(초단기실황) |
| `client.airquality` | 한국환경공단 에어코리아 대기오염정보 | B552584 | XML | 2개 -- `by_sido`(시도별 실시간) · `by_station`(측정소별 실시간) |
| `client.holidays` | 한국천문연구원 특일 정보 | B090041 | XML | 5개 -- `holidays`(공휴일) · `national_holidays`(국경일) · `anniversaries`(기념일) · `solar_terms`(24절기) · `sundry_days`(잡절) |
| `client.realestate` | 국토교통부 아파트 실거래가 | 1613000 | XML | 4개 -- `apt_trade`(매매) · `apt_trade_detail`(매매상세) · `apt_rent`(전월세) · `apt_presale`(분양권전매) |
| `client.midforecast` | 기상청 중기예보 | 1360000 | XML | 2개 -- `land`(중기육상: 강수·날씨) · `temperature`(중기기온: 최저·최고) |
| `client.procurement` | 조달청 나라장터 입찰공고 | 1230000 | XML | 4개 -- `goods`(물품) · `services`(용역) · `construction`(공사) · `foreign`(외자) |
| `client.customs` | 관세청 품목별 수출입실적 | 1220000 | XML | `item_trade` -- HS부호별 월 수출/수입 금액·중량 |
| `client.kofia` | 금융투자협회 종합통계 | 1160100 | JSON | 8개 -- `market_funds` · `credit_balance` · `trust_scale` · `fund_net_asset` · `cma_status` · `dls_dlb` · `els_elb` · `overseas_derivatives` |

- 서비스마다 계정에서 **활용신청**이 따로 필요합니다(§6 참고).
- `clean=True`(기본)는 타입 파싱된 snake_case 컬럼을, `clean=False`는 벤더 토큰 원문을
  돌려줍니다.

## 4. 커맨드라인

호출 형태는 `data-go-kr <서비스> <오퍼레이션> [옵션]`입니다. 전체 서비스·오퍼레이션
목록은 `data-go-kr list`(오프라인, 키 불필요), 각 오퍼레이션의 옵션은 `data-go-kr
<서비스> <오퍼레이션> --help`로 확인합니다. 어느 명령에든 `--json`을 붙이면 JSON으로
나옵니다.

**weather — 기상청 동네예보** · `forecast`(단기) / `ultra_forecast`(초단기) / `nowcast`(실황)

```bash
data-go-kr weather forecast --base-date 20260811 --base-time 0500 --nx 60 --ny 127
```

`--nx`/`--ny`는 기상청 5km 격자좌표(서울 종로 ≈ 60,127), `--base-time`은 발표시각(0200·
0500·…·2300 중)입니다.

**airquality — 에어코리아 대기오염정보** · `by_sido`(시도별) / `by_station`(측정소별)

```bash
data-go-kr airquality by_sido 서울
data-go-kr airquality by_station 종로구 --data-term DAILY
```

`by_sido`는 시도명, `by_station`은 측정소명을 받습니다. `--data-term`은 조회기간(DAILY /
MONTH / 3MONTH).

**holidays — 한국천문연구원 특일 정보** · `holidays`(기본) / `national_holidays` /
`anniversaries` / `solar_terms` / `sundry_days`

```bash
data-go-kr holidays --year 2026
data-go-kr holidays solar_terms --year 2026
```

`--year`는 필수이고, `--month`(1–12)로 특정 달만 볼 수 있습니다(`solar_terms`는 24절기).

**realestate — 국토교통부 아파트 실거래가** · `apt_trade`(매매) / `apt_trade_detail`(매매
상세) / `apt_rent`(전월세) / `apt_presale`(분양권)

```bash
data-go-kr realestate apt_trade 11110 --deal-ym 202401
```

`11110`은 법정동 코드 앞 5자리(LAWD_CD, 종로구), `--deal-ym`은 계약년월입니다.

**midforecast — 기상청 중기예보** · `land`(육상: 강수·날씨) / `temperature`(기온: 최저·최고)

```bash
data-go-kr midforecast land --region 11B00000 --base-time 202608110600
```

`--region`은 예보구역코드(11B00000 = 서울·인천·경기), `--base-time`은 발표시각(매일 0600·
1800)입니다.

**procurement — 조달청 나라장터 입찰공고** · `goods`(물품) / `services`(용역) /
`construction`(공사) / `foreign`(외자)

```bash
data-go-kr procurement services --begin 202608010000 --end 202608102359
```

`--begin`/`--end`는 공고게시 구간(YYYYMMDDHHMM, 분 단위), `--inqry-div`로 기준을 바꿉니다(1
공고게시일시 / 2 개찰일시).

**customs — 관세청 품목별 수출입실적** · `item_trade`

```bash
data-go-kr customs item_trade 8542 --begin 202401 --end 202406
```

`8542`는 HS 부호(반도체 집적회로), 구간은 YYYYMM입니다.

**kofia — 금융투자협회 종합통계** · `market_funds` 등 8개 오퍼레이션(`data-go-kr list` 참고)

```bash
data-go-kr kofia market_funds --begin 20240101 --end 20240131
```

`--begin`/`--end`는 YYYYMMDD이며, 월간 통계는 YYYYMM으로 줍니다.

## 5. AI 코딩 에이전트에서 사용

- 이 저장소는 Claude Code와 Codex의 플러그인 마켓플레이스를 겸합니다.
- `list` / `weather` / `airquality` / `holidays` / `realestate` / `midforecast` /
  `procurement` / `customs` / `kofia` 아홉 스킬이 들어 있고, 각각 같은 이름의
  `data-go-kr` 명령을 얇게 감쌉니다.
- 패키지를 먼저 설치하세요(`list`는 키 없이 동작, 조회는 키 필요).

### 5.1 Claude Code (채팅)

```
/plugin marketplace add seokhoonj/data-go-kr
/plugin install data-go-kr@data-go-kr
```

### 5.2 Codex (터미널)

```
codex plugin marketplace add seokhoonj/data-go-kr
codex plugin add data-go-kr@data-go-kr
```

## 6. 에러 및 운영 참고

모든 운영 에러는 `DataGoKrError`에서 파생합니다: `DataGoKrConfigError`(키 없음),
`DataGoKrAuthError`(키 거부/미활용신청), `DataGoKrRateLimitError`(트래픽 제한),
`DataGoKrResponseError`(벤더 에러 코드), `DataGoKrNetworkError`(전송 실패). 에러
메시지에 키나 요청 URL은 절대 담기지 않습니다.

포털 reason 코드는 아래처럼 매핑됩니다(`DataGoKrResponseError`는 `.code`에 코드를
보존하므로 1/4/12/99는 직접 분기할 수 있습니다):

| 코드 | 의미 | 클래스 |
|---|---|---|
| 1  | APPLICATION_ERROR (포털 서버) | `DataGoKrResponseError` |
| 4  | HTTP_ERROR (제공기관 서버) | `DataGoKrResponseError` |
| 12 | NO_OPENAPI_SERVICE_ERROR (서비스 없음/폐기) | `DataGoKrResponseError` |
| 20 | SERVICE_ACCESS_DENIED (미신청/중지) | `DataGoKrAuthError` |
| 22 | 일일 트래픽 초과 | `DataGoKrRateLimitError` |
| 23 | 초당 요청 차단 | `DataGoKrRateLimitError` |
| 30 | SERVICE_KEY_IS_NOT_REGISTERED | `DataGoKrAuthError` |
| 31 | DEADLINE_HAS_EXPIRED | `DataGoKrAuthError` |
| 99 | UNKNOWN_ERROR | `DataGoKrResponseError` |

- **활용신청.** 데이터셋마다 따로 신청하며, 승인 안 된 API 호출은 잘못된 키와
  똑같이 코드 30으로 실패합니다. API는 자동승인(즉시)이거나 심의승인(제공기관 승인
  후)이며, 스펙 페이지의 "심의유형"과 마이페이지 > 데이터 활용 > Open API > 활용신청
  현황에서 상태를 확인하세요.
- **트래픽.** 키 하나에 API별 일일 호출 한도(코드 22)가 있고 매일 자정(KST)에
  초기화됩니다. 개발계정은 기본 한도가 낮고, 운영계정 전환으로 상향합니다. 코드
  22/23은 `DataGoKrRateLimitError`이며 즉시 재시도하지 마세요.
- **폐기.** 철회된 엔드포인트는 코드 12로 나오며, 변경은 data.go.kr API 공지
  게시판(`nttApiYn=Y`)에 공지됩니다.
- **CORS는 무관.** 서버사이드 클라이언트라, 일부 제공기관 API를 프런트엔드
  JavaScript에서 막는 브라우저 Same-Origin 정책이 여기엔 적용되지 않습니다.

## 7. 라이선스

**패키지 코드**는 MIT입니다(`LICENSE` 참고).

**데이터**는 제공기관의 것입니다. 공공데이터법 제3조에 따라 공공데이터는 원칙적으로
상업적 이용이 허용되나, 특정 데이터셋이 이를 제한하거나 기관이 제공을 중단할 수
있습니다(제28조). 데이터를 재배포하기 전에 해당 데이터셋의 이용 조건을 확인하세요.
