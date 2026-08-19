# weather — 기상청 동네예보

기상청 동네예보 (서비스 `1360000`, XML). 단기예보와 초단기예보/실황을 기상청 5km 격자
한 칸(`nx`/`ny`)에 대해 조회합니다.

## 오퍼레이션

| 오퍼레이션 | 설명 |
|---|---|
| `forecast` | 단기예보 (오늘~모레) |
| `ultra_forecast` | 초단기예보 (6시간 이내) |
| `nowcast` | 초단기실황 (현재 관측값) |

## CLI

```bash
data-go-kr weather forecast --base-date 20260811 --base-time 0500 --nx 60 --ny 127
```

`--base-time`은 발표시각(0200·0500·…·2300 중), `--nx`/`--ny`는 기상청 5km 격자좌표입니다.

## Python

```python
from data_go_kr import DataGoKr, latlon_to_grid

client = DataGoKr()
g = latlon_to_grid(37.5714, 126.9658)      # 위경도 -> Grid(nx=60, ny=127)
rows = client.weather.forecast(base_date="20260811", base_time="0500", nx=g.nx, ny=g.ny)
```

`ultra_forecast` / `nowcast`도 같은 인자를 받습니다. `clean=False`로 벤더 토큰 원문을
받을 수 있습니다.

## 격자 코드 찾기

`nx`/`ny`는 기상청 격자좌표입니다(서울 종로 ≈ 60,127). 위경도로 구하세요:

```bash
data-go-kr grid 37.5714 126.9658    # -> 60 127
```

Python은 `latlon_to_grid(lat, lon) -> Grid(nx, ny)` (`nx, ny = latlon_to_grid(...)`로 언패킹).
