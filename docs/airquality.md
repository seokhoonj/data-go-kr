# airquality — 에어코리아 대기오염정보

한국환경공단 에어코리아 대기오염정보 (서비스 `B552584`, XML). 미세먼지(PM10/PM2.5)·오존·
이산화질소 등 실시간 측정값.

## 오퍼레이션

| 오퍼레이션 | 설명 |
|---|---|
| `by_sido` | 시도별 실시간 측정 |
| `by_station` | 측정소별 실시간 측정 |

## CLI

```bash
datagokr airquality by_sido 서울
datagokr airquality by_station 종로구 --data-term DAILY
```

`by_sido`는 시도명(서울/부산/경기 …), `by_station`은 측정소명을 받습니다. `--data-term`은
조회기간(`DAILY` / `MONTH` / `3MONTH`).

## Python

```python
from pydatagokr import DataGoKr

client = DataGoKr()
rows = client.airquality.by_sido(sido="서울")
one  = client.airquality.by_station(station="종로구", data_term="DAILY")
```
