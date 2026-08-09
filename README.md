# data-go-kr

**한국어** | [English](README.en.md)

공공데이터포털 **data.go.kr**의 오픈 API를 키 하나로 읽어옵니다: 금융투자협회
종합통계(투자자예탁금, 신용공여잔고, 펀드, CMA, ELS/DLS, 신탁, 해외파생)와 관세청
수출입 무역통계(HS 부호별 월간 수출입실적). 런타임 의존성 없이 표준 라이브러리만
쓰고, 결과는 `pandas.DataFrame` / `polars.DataFrame`이 바로 받는 `list[dict]`입니다.

> 뼈대 README -- 섹션 구조는 확정, 본문은 채워 나가는 중입니다.

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

gokr = DataGoKr()
rows = gokr.kofia.market_funds(begin="20240101", end="20240131")
raw  = gokr.customs.item_trade("8542", begin="202401", end="202406")
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

- `gokr.kofia` -- 금융투자협회 종합통계(서비스 1160100), 8개 오퍼레이션:
  `market_funds`, `credit_balance`, `trust_scale`, `fund_net_asset`, `cma_status`,
  `dls_dlb`, `els_elb`, `overseas_derivatives`. `clean=True`(기본)는 타입 파싱된
  snake_case 컬럼을, `clean=False`는 벤더 토큰 원문을 돌려줍니다.
- `gokr.customs` -- 관세청 수출입 무역통계(서비스 1220000): `item_trade(hs_code,
  begin=, end=)`, 원문 행 반환(필드 토큰 매핑은 라이브 검증 대기 중).

오프라인 목록은 키 없이: `data_go_kr.catalog.services()` /
`catalog.operations("kofia")` / `catalog.fields("kofia", "market_funds")`(오퍼레이션별
정제 컬럼 스키마 -- token, column, kind, is_key).

정제는 단독으로도 씁니다: 공개 함수 `clean(rows, table)`과 오퍼레이션별 `Table` /
`Field` 스펙으로, 클라이언트 없이 원문 벤더 행을 타입 파싱된 snake_case 컬럼으로
바꿉니다(`from data_go_kr import clean`).

### 서비스 추가하기

data.go.kr에는 수천 개 기관 API가 있고 시간에 따라 바뀌므로, 서비스는 더하는
구조입니다. 중립 `DataGoKrSession` 전송 계층이 포털 공통 계약(디코딩키 단일 인코딩,
페이징, 두 오류 envelope, reason-code 체계)을 모든 서비스에 대해 이미 처리하므로,
새 서비스는 작고 반복적인 모듈 하나면 됩니다 -- 전송 계층은 바뀌지 않습니다:

1. `src/data_go_kr/services/<기관>.py`에 surface 클래스를 두고, 그 서비스의 base URL로
   `DataGoKrSession(base_url, api_key, timeout=..., json_param=...)`을 만듭니다
   (`json_param`은 대개 `"resultType"`, 일부는 `"_type"` -- 스펙 페이지 확인).
2. 오퍼레이션과 오퍼레이션별 `Table` 스펙(`Field(token, column, kind)`)을 선언합니다 --
   벤더 토큰이 깨끗한 컬럼으로 매핑되는 단 하나의 자리라, 나중에 필드가 바뀌어도 한 줄
   수정으로 끝납니다.
3. `catalog.py`에 서비스를 등록하면 `gokr list`와 오프라인 목록에 나타납니다.
4. 계정에서 데이터셋을 활용신청한 뒤, 라이브 1콜로 미확정 필드 토큰을 확정합니다.

## 4. 커맨드라인

```bash
gokr list                                                # 오프라인, 키 불필요
gokr fields kofia market_funds                           # 오프라인 컬럼 스키마
gokr kofia market_funds --begin 20240101 --end 20240131
gokr customs item_trade 8542 --begin 202401 --end 202406
```

`--json`을 붙이면 JSON으로 나옵니다.

## 5. 오류 및 운영 참고

모든 운영 오류는 `DataGoKrError`에서 파생합니다: `DataGoKrConfigError`(키 없음),
`DataGoKrAuthError`(키 거부/미활용신청), `DataGoKrRateLimitError`(트래픽 제한),
`DataGoKrResponseError`(벤더 오류 코드), `DataGoKrNetworkError`(전송 실패). 오류
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

## 6. AI 코딩 에이전트에서 사용

- 이 저장소는 Claude Code와 Codex의 플러그인 마켓플레이스를 겸합니다.
- `list` / `kofia` / `customs` 세 스킬이 들어 있고, 각각 같은 이름의 `gokr` 명령을
  얇게 감쌉니다.
- 패키지를 먼저 설치하세요(`list`는 키 없이 동작, 조회는 키 필요).

### 6.1 Claude Code (채팅)

```
/plugin marketplace add seokhoonj/data-go-kr
/plugin install gokr@data-go-kr
```

### 6.2 Codex (터미널)

```
codex plugin marketplace add seokhoonj/data-go-kr
codex plugin add gokr@data-go-kr
```

## 7. 라이선스

**패키지 코드**는 MIT입니다(`LICENSE` 참고).

**데이터**는 제공기관의 것입니다. 공공데이터법 제3조에 따라 공공데이터는 원칙적으로
상업적 이용이 허용되나, 특정 데이터셋이 이를 제한하거나 기관이 제공을 중단할 수
있습니다(제28조). 데이터를 재배포하기 전에 해당 데이터셋의 이용 조건을 확인하세요.
