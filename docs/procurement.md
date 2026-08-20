# procurement — 조달청 나라장터 입찰공고

조달청 나라장터 입찰공고 (서비스 `1230000` `BidPublicInfoService`, XML). 업무구분별로 한
시간창 안에 게시된 입찰공고를 조회합니다.

## 오퍼레이션

| 오퍼레이션 | 업무구분 |
|---|---|
| `goods` | 물품 |
| `services` | 용역 |
| `construction` | 공사 |
| `foreign` | 외자 |

벤더가 업무구분이 맞는 오퍼레이션에만 답합니다(공사 공고는 `construction`에서만).

## CLI

```bash
datagokr procurement services --begin 202608010000 --end 202608102359
```

`--begin`/`--end`는 공고게시 구간(YYYYMMDDHHMM, 분 단위). `--inqry-div`로 기준을 바꿉니다
(`1` 공고게시일시 / `2` 개찰일시).

## Python

```python
from pydatagokr import DataGoKr

client = DataGoKr()
rows = client.procurement.services(begin="202608010000", end="202608102359")
```

한 행이 입찰공고 하나이며, `notice_no`(입찰공고번호) + `notice_ord`(차수)로 식별됩니다.
