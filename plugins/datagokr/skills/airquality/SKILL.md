---
name: airquality
description: "Fetch 한국환경공단 에어코리아 대기오염정보 (AirKorea real-time air quality) from data.go.kr (service B552584) -- 미세먼지(PM10)·초미세먼지(PM2.5)·오존·통합대기환경지수 등, by 시도 (`by_sido`) or by 측정소 (`by_station`). Holds no logic of its own -- it calls the pydatagokr package's CLI (`datagokr airquality`) and shows the result to the user. Trigger phrases: 미세먼지, 초미세먼지, 대기오염, 대기질, 오존, 에어코리아, 통합대기환경지수, air quality, PM10, PM2.5, fine dust."
---

# datagokr — 에어코리아 대기오염정보

Fetch real-time air quality. Clean columns: `station`, `measured_at`, `khai`/`khai_grade`
(통합대기환경지수), and per pollutant a value + `_grade` + `_flag`: `pm10`/`pm25` (미세먼지·
초미세먼지, ㎍/㎥, integers), `so2`/`co`/`o3`/`no2` (ppm, decimals). Grades: 1 좋음 · 2 보통 ·
3 나쁨 · 4 매우나쁨.

| operation | 조회 |
|---|---|
| `by_sido` | 시도별 실시간 (a province's stations, latest) |
| `by_station` | 측정소별 실시간 (one station over a term) |

## Prerequisite

```
pipx install pydatagokr      # or: pip install pydatagokr
```

A data.go.kr **decoding** key must be configured (env `DATA_GO_KR_API_KEY` or
`~/.config/pydatagokr/credentials.json`), and the 대기오염정보 dataset (service B552584)
applied for (활용신청). It is 자동승인 for a development account.

## Running

```
datagokr airquality by_sido <시도명>                         [--json]
datagokr airquality by_station <측정소명> [--data-term TERM] [--json]
```

- `<시도명>`: 서울 / 부산 / 인천 / 경기 / ... (a 광역시도).
- `<측정소명>`: a station, e.g. 종로구. `--data-term` is `DAILY` (default) / `MONTH` / `3MONTH`.

## Procedure

1. **Pick the query.** "서울 미세먼지" -> `by_sido 서울`; a named station over time ->
   `by_station <name> --data-term MONTH`.
2. **Run.**
   ```bash
   datagokr airquality by_sido 서울
   ```
   Add `--json` for machine-readable data.
3. **Relay the result.** Report `pm10`/`pm25` with their grade (좋음/보통/나쁨/매우나쁨). A
   `_flag` value means that pollutant's measurement was unavailable.
4. **Error handling.** A one-line `datagokr: <message>` on stderr:
   - a `[30]`/`[20]` auth error -> the key is wrong, is the *encoding* form, or service
     B552584 is not applied for yet.
   - a `SERVICETIMEOUT` (`by_station` especially) is a transient AirKorea server timeout --
     retry.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It does not forecast; it returns measurements. (Air-quality forecasts are a separate
  operation not wrapped here.)
