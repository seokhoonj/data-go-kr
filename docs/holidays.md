# holidays — 한국천문연구원 특일 정보

한국천문연구원 특일 정보 (서비스 `B090041`, XML). 공휴일·국경일·기념일·24절기·잡절.

## 오퍼레이션

| 오퍼레이션 | 설명 |
|---|---|
| `holidays` | 공휴일 (기본) |
| `national_holidays` | 국경일 |
| `anniversaries` | 기념일 |
| `solar_terms` | 24절기 |
| `sundry_days` | 잡절 |

## CLI

```bash
data-go-kr holidays --year 2026
data-go-kr holidays solar_terms --year 2026
```

`--year`는 필수이고, `--month`(1~12)로 특정 달만 볼 수 있습니다. 오퍼레이션을 생략하면
`holidays`(공휴일)입니다.

## Python

```python
from pydatagokr import DataGoKr

client = DataGoKr()
공휴일 = client.holidays.holidays(year=2026)
절기   = client.holidays.fetch("solar_terms", year=2026)   # 그 외 오퍼레이션은 fetch(name, ...)
```
