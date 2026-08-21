# weather — 기상청 동네예보

기상청 동네예보 (서비스 `1360000`, XML). 단기예보와 초단기예보/실황을 기상청 5km 격자
한 칸(`nx`/`ny`)에 대해 조회합니다.

## 오퍼레이션

| 오퍼레이션 | 설명 |
|---|---|
| `forecast` | 단기예보 (오늘~모레) |
| `ultra_forecast` | 초단기예보 (6시간 이내) |
| `nowcast` | 초단기실황 (현재 관측값) |

결과는 **long** 형태(한 시각·한 항목당 한 행)이고, 값의 뜻은 `category`에 따라 다릅니다:

| category | 항목 | category | 항목 |
|---|---|---|---|
| TMP / T1H | 기온 (℃) | POP | 강수확률 (%) |
| SKY | 하늘상태 (1 맑음·3 구름많음·4 흐림) | PTY | 강수형태 (0 없음·1 비·2 비/눈·3 눈) |
| REH | 습도 (%) | WSD | 풍속 (m/s) |
| PCP / RN1 | 강수량 (mm) | SNO | 적설 (cm) |

## CLI

```bash
datagokr weather forecast --nx 60 --ny 127                          # 최신 발표분
datagokr weather forecast --base-date 20260811 --base-time 0500 --nx 60 --ny 127
```

`--base-date`/`--base-time`을 생략하면 최신 발표분을 씁니다. 지정할 때 `--base-time`은
발표시각(단기예보 0200·0500·…·2300 중), `--nx`/`--ny`는 기상청 5km 격자좌표입니다.

## Python

```python
from pydatagokr import DataGoKr, latlon_to_grid

client = DataGoKr()
g = latlon_to_grid(37.5714, 126.9658)      # 위경도 -> Grid(nx=60, ny=127)
rows = client.weather.forecast(nx=g.nx, ny=g.ny)               # 최신 발표분
# 특정 발표분이 필요하면 base_date/base_time을 함께 지정
rows = client.weather.forecast(base_date="20260811", base_time="0500", nx=g.nx, ny=g.ny)
```

`base_date`/`base_time`을 둘 다 생략하면 해당 오퍼레이션의 최신 발표분을 자동으로 씁니다
(단기예보는 하루 8회, 초단기예보는 매시 30분, 초단기실황은 매시 정시 발표). 하나만 지정하면
오류입니다. `ultra_forecast` / `nowcast`도 같은 인자를 받습니다. `clean=False`로 벤더 토큰
원문을 받을 수 있습니다.

## 격자 코드 찾기

`nx`/`ny`는 기상청 격자좌표입니다(서울 종로 ≈ 60,127). 위경도로 구하세요:

```bash
datagokr grid 37.5714 126.9658    # -> 60 127
```

Python은 `latlon_to_grid(lat, lon) -> Grid(nx, ny)` (`nx, ny = latlon_to_grid(...)`로 언패킹).
