# 에러 및 운영 참고

모든 운영 에러는 `DataGoKrError`에서 파생합니다:

| 클래스 | 언제 |
|---|---|
| `DataGoKrConfigError` | 키 없음 |
| `DataGoKrAuthError` | 키 거부 / 미활용신청 |
| `DataGoKrRateLimitError` | 트래픽 제한 |
| `DataGoKrResponseError` | 벤더 에러 코드 |
| `DataGoKrNetworkError` | 전송 실패 |

에러 메시지에 키나 요청 URL은 절대 담기지 않습니다.

## reason 코드 매핑

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

## 운영 참고

- **활용신청.** 데이터셋마다 따로 신청하며, 승인 안 된 API 호출은 잘못된 키와 똑같이
  코드 30으로 실패합니다. API는 자동승인(즉시)이거나 심의승인(제공기관 승인 후)이며,
  스펙 페이지의 "심의유형"과 마이페이지 > 데이터 활용 > Open API > 활용신청 현황에서
  상태를 확인하세요.
- **트래픽.** 키 하나에 API별 일일 호출 한도(코드 22)가 있고 매일 자정(KST)에
  초기화됩니다. 개발계정은 기본 한도가 낮고, 운영계정 전환으로 상향합니다. 코드 22/23은
  `DataGoKrRateLimitError`이며 즉시 재시도하지 마세요.
- **폐기.** 철회된 엔드포인트는 코드 12로 나오며, 변경은 data.go.kr API 공지
  게시판(`nttApiYn=Y`)에 공지됩니다.
- **CORS는 무관.** 서버사이드 클라이언트라, 일부 제공기관 API를 프런트엔드
  JavaScript에서 막는 브라우저 Same-Origin 정책이 여기엔 적용되지 않습니다.
