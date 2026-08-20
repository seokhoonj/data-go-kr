---
name: weather
description: "Fetch 기상청 동네예보 (KMA village weather forecast) from data.go.kr (service 1360000) -- the 단기예보 (`forecast`, ~3 days), 초단기예보 (`ultra_forecast`, 6 hours), and 초단기실황 (`nowcast`, latest observation) for one 5km grid cell (nx, ny). Holds no logic of its own -- it calls the pydatagokr package's CLI (`datagokr weather`) and shows the result to the user. Trigger phrases: 날씨, 동네예보, 단기예보, 초단기예보, 기온, 강수확률, 하늘상태, weather forecast, temperature, rain probability."
---

# datagokr — 기상청 동네예보

Fetch a grid cell's forecast or observation. The result is **long** -- one row per weather
item (`category`) per time. Clean columns: `base_date`, `base_time`, `category`,
`forecast_date`/`forecast_time` + `forecast_value` (forecasts) or `observed_value` (nowcast),
`nx`, `ny`. The value's meaning depends on `category`:

| category | 항목 | category | 항목 |
|---|---|---|---|
| TMP / T1H | 기온 (℃) | POP | 강수확률 (%) |
| SKY | 하늘상태 (1 맑음·3 구름많음·4 흐림) | PTY | 강수형태 (0 없음·1 비·2 비/눈·3 눈) |
| REH | 습도 (%) | WSD | 풍속 (m/s) |
| PCP / RN1 | 강수량 | POP | 강수확률 |

| operation | 예보 |
|---|---|
| `forecast` | 단기예보 (~3일) |
| `ultra_forecast` | 초단기예보 (6시간) |
| `nowcast` | 초단기실황 (현재 관측) |

## Prerequisite

```
pipx install pydatagokr      # or: pip install pydatagokr
```

A data.go.kr **decoding** key must be configured (env `DATAGOKR_API_KEY` or
`~/.config/pydatagokr/credentials.json`), and the 단기예보 dataset (service 1360000,
VilageFcstInfoService_2.0) applied for (활용신청) on that account.

## Running

```
datagokr weather <operation> --nx NX --ny NY [--base-date YYYYMMDD --base-time HHMM] [--json]
```

- `--base-date`/`--base-time`: the announcement time. **Omit both to use the latest published
  announcement** for the operation. 단기예보 is issued at 0200/0500/0800/1100/1400/1700/2000/
  2300; 초단기 is issued hourly (available ~40 min after the hour). Pass both or neither.
- `--nx`/`--ny`: the 기상청 5km grid coordinates (서울 시청 ≈ 60/127).

## Procedure

1. **Map the place to a grid.** Convert the user's location to `nx`/`ny` (ask if unsure;
   do not guess). Omit `base_date`/`base_time` for the latest announcement, or pick a valid
   pair for the operation.
2. **Run.**
   ```bash
   datagokr weather forecast --nx 60 --ny 127          # latest announcement
   ```
   Add `--json` for machine-readable data.
3. **Relay the result.** The rows are long; group by `forecast_date`/`forecast_time` and
   read `forecast_value` per `category` (translate the codes above for the user).
4. **Error handling.** A one-line `datagokr: <message>` on stderr:
   - a `[30]`/`[20]` auth error -> the key is wrong, is the *encoding* form by mistake,
     or service 1360000 is not applied for yet.
   - an empty result (no rows) usually means a `base_time` with no issued forecast yet.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It does not convert place names to grid coordinates; the caller supplies `nx`/`ny`.
