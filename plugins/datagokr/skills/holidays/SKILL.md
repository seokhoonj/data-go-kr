---
name: holidays
description: "Fetch Korean special days from data.go.kr (한국천문연구원 특일 정보, service B090041) -- public holidays (공휴일), national holidays (국경일), anniversaries (기념일), the 24 solar terms (24절기), and sundry days (잡절), each with its date and whether it is a public holiday. Holds no logic of its own -- it calls the pydatagokr package's CLI (`datagokr holidays`) and shows the result to the user. Trigger phrases: 공휴일, 대체공휴일, 국경일, 24절기, 기념일, 특일 정보, 올해 공휴일, Korean holidays, public holidays, solar terms."
---

# datagokr — 한국천문연구원 특일 정보

Fetch a solar year's special days -- the clean columns are `date`, `name`, `is_holiday`
(`Y`/`N`), `kind_code`, `seq`. Five operations, one shape:

| operation | 특일 |
|---|---|
| `holidays` (default) | 관공서 공휴일 (대체공휴일 포함) |
| `national_holidays` | 국경일 |
| `anniversaries` | 기념일 |
| `solar_terms` | 24절기 |
| `sundry_days` | 잡절 |

## Prerequisite

```
pipx install pydatagokr      # or: pip install pydatagokr
```

A data.go.kr **decoding** key must be configured (env `DATAGOKR_API_KEY` or
`~/.config/pydatagokr/credentials.json`), and the 특일 정보 dataset (service B090041)
applied for (활용신청) on that account.

## Running

```
datagokr holidays [operation] --year YYYY [--month M] [--json]
```

`operation` defaults to `holidays`. `--month` (1-12) narrows to one month; omit it for the
whole year.

## Procedure

1. **Identify what the user wants.** "올해 공휴일" -> `holidays --year <this year>`; "24절기"
   -> `solar_terms`; a specific month -> add `--month`.
2. **Run.**
   ```bash
   datagokr holidays --year 2026
   datagokr holidays solar_terms --year 2026
   ```
   Add `--json` when the user wants machine-readable data.
3. **Relay the result.** Show the CLI's stdout (clean columns). The `is_holiday` column is
   the one that answers "is this a day off" -- a 기념일/절기 is usually `N`.
4. **Error handling.** A one-line `datagokr: <message>` on stderr:
   - a `[30]`/`[20]` auth error -> the key is wrong, is the *encoding* form by mistake,
     or service B090041 is not applied for yet.
   - a `[22]`/`[23]` rate limit -> wait and retry.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It does not compute business days -- it returns the special days; a caller derives
  workdays from `is_holiday` plus weekends.
