# data-go-kr

공공데이터포털 **data.go.kr**의 오픈 API를 키 하나로 읽어옵니다. 포털에는 수천 개 기관
API가 있고, 그중 조회수와 활용신청이 높은 데이터들 -- 기상·대기·공휴일·부동산·중기예보·
조달·관세·금융투자 -- 을 미리 감싸 두었습니다.

미리 감싼 서비스는 `client.weather.forecast(...)`처럼 **접근자**로 바로 꺼내고, 표에 없는
서비스는 base URL만 주면 전송 계층이 그대로 조회합니다. 결과는 어느 쪽이든
`pandas.DataFrame` / `polars.DataFrame`이 바로 받는 `list[dict]`입니다.

## 1. 설치

```bash
pip install data-go-kr
```

data.go.kr 인증키가 필요합니다 -- 반드시 **디코딩**(원문) 키를 쓰세요(퍼센트 인코딩된
인코딩 키는 이중 인코딩되어 거부됩니다). 한 번 저장해 두려면
`~/.config/data-go-kr/credentials.json`:

```json
{ "DATA_GO_KR_API_KEY": "발급받은-디코딩-키" }
```

환경변수 `DATA_GO_KR_API_KEY`나 `api_key=` 인자로도 넣을 수 있습니다. 각 데이터셋은
계정에서 별도로 활용신청해야 합니다.

## 2. 빠른 시작

**미리 만들어 둔 서비스**(§3 표)는 한 클라이언트에서 바로 씁니다:

```python
from data_go_kr import DataGoKr

client = DataGoKr()
rows   = client.weather.forecast(base_date="20260811", base_time="0500", nx=60, ny=127)
trades = client.realestate.apt_trade(region_code="11110", deal_ym="202401")
```

**표에 없는(아직 안 감싼) 서비스**도 전송 계층으로 직접 조립합니다 -- base URL·오퍼레이션·
필터만 있으면 되고, 디코딩키 주입·페이징·두 에러 형식은 전송 계층이 처리해 벤더 원본
필드명 그대로 돌려줍니다. 위 `apt_trade`를 파사드 없이 직접 부르면(스펙 페이지에서 base
URL·오퍼레이션 경로·파라미터명을 얻습니다):

```python
from data_go_kr import DataGoKrSession

session = DataGoKrSession("https://apis.data.go.kr/1613000", response_format="xml")
rows = session.fetch(
    "RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade",  # 오퍼레이션 경로
    LAWD_CD="11110",    # 법정동 시군구코드 (앞 5자리)
    DEAL_YMD="202401",  # 계약년월 YYYYMM
)
```

결과는 어느 쪽이든 `list[dict]`이라 pandas·polars 표로 바로 만듭니다:

```python
import pandas as pd; pd.DataFrame(rows)     # pandas
import polars as pl; pl.DataFrame(rows)      # polars
```

## 3. 서비스

포털의 수많은 API 중 지금 바로 쓰도록 **미리 만들어 둔** 서비스입니다. 접근자마다 상세
문서가 있어 오퍼레이션·CLI/Python 예시·필요한 코드를 찾는 법을 담았습니다.

| 접근자 | 기관 · 통계 | 포맷 | 문서 |
|---|---|---|---|
| `client.weather` | 기상청 동네예보 (단기·초단기·실황) | XML | [docs/weather.md](docs/weather.md) |
| `client.airquality` | 한국환경공단 에어코리아 대기오염정보 | XML | [docs/airquality.md](docs/airquality.md) |
| `client.holidays` | 한국천문연구원 특일 정보 (공휴일·24절기 등) | XML | [docs/holidays.md](docs/holidays.md) |
| `client.realestate` | 국토교통부 아파트 실거래가 (매매·전월세·분양권) | XML | [docs/realestate.md](docs/realestate.md) |
| `client.midforecast` | 기상청 중기예보 (4~10일 육상·기온) | XML | [docs/midforecast.md](docs/midforecast.md) |
| `client.procurement` | 조달청 나라장터 입찰공고 (물품·용역·공사·외자) | XML | [docs/procurement.md](docs/procurement.md) |
| `client.customs` | 관세청 품목별 수출입실적 (HS 부호별 월간) | XML | [docs/customs.md](docs/customs.md) |
| `client.kofia` | 금융투자협회 종합통계 (예탁금·펀드·ELS/DLS 등) | JSON | [docs/kofia.md](docs/kofia.md) |

- **활용신청이 먼저.** 서비스마다 data.go.kr 계정에서 해당 데이터셋을 따로 신청해야
  호출됩니다.
- **정제(`clean`).** 기본값 `clean=True`는 벤더의 원본 필드명을 타입까지 파싱한
  snake_case 컬럼으로 바꿔 돌려주고, `clean=False`는 원문 토큰 그대로 돌려줍니다.
- **탐색.** 어떤 서비스·오퍼레이션이 있는지는 `data-go-kr list`(또는 `catalog.services()`),
  각 오퍼레이션이 받는 옵션은 `data-go-kr <서비스> <오퍼레이션> --help`로 봅니다.
- **에러·운영.** reason 코드, 활용신청 승인 방식, 트래픽 한도는 [docs/errors.md](docs/errors.md)에
  정리돼 있습니다.

## 4. 커맨드라인

```bash
data-go-kr list                                         # 서비스·오퍼레이션 (오프라인, 키 불필요)
data-go-kr holidays --year 2026                         # 공휴일
data-go-kr realestate apt_trade 11110 --deal-ym 202401  # 아파트 매매 실거래가
```

호출 형태는 `data-go-kr <서비스> <오퍼레이션> [옵션]`입니다. 기본 출력은 읽기 좋은
요약이고, `--json`을 붙이면 전체 결과를 JSON으로 냅니다. 서비스별 전체 명령과 옵션,
코드를 찾는 법은 위 표의 문서를 참고하세요.

## 5. AI 코딩 에이전트에서 사용

이 저장소는 Claude Code와 Codex의 플러그인 마켓플레이스를 겸합니다. `list` 외 여덟
서비스 스킬이 각각 같은 이름의 `data-go-kr` 명령을 얇게 감쌉니다(패키지를 먼저
설치하세요; `list`는 키 없이 동작, 조회는 키 필요).

```
# Claude Code (채팅)
/plugin marketplace add seokhoonj/data-go-kr
/plugin install data-go-kr@data-go-kr

# Codex (터미널)
codex plugin marketplace add seokhoonj/data-go-kr
codex plugin add data-go-kr@data-go-kr
```

## 6. 라이선스

**패키지 코드**는 MIT입니다(`LICENSE` 참고).

**데이터**는 제공기관의 것입니다. 공공데이터법 제3조에 따라 공공데이터는 원칙적으로
상업적 이용이 허용되나, 특정 데이터셋이 이를 제한하거나 기관이 제공을 중단할 수
있습니다(제28조). 데이터를 재배포하기 전에 해당 데이터셋의 이용 조건을 확인하세요.
