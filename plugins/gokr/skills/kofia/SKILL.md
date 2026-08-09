---
name: kofia
description: "Fetch one KOFIA 종합통계 operation from data.go.kr over a date range -- investor deposits and forced selling (market_funds), margin loan balances (credit_balance), funds, CMA, ELS/DLS, trusts, overseas derivatives. Holds no logic of its own -- it calls the data-go-kr package's CLI (`gokr kofia`) and shows the result to the user. Trigger phrases: 투자자예탁금, 신용잔고, 신용거래융자, 반대매매, CMA 잔고, ELS 발행, KOFIA statistics, investor deposit, margin loan balance."
---

# gokr — KOFIA 종합통계

Fetch one 금융투자협회 (KOFIA) statistics operation over a date range. Daily
operations (`market_funds`, `credit_balance`, `fund_net_asset`, `cma_status`) take
YYYYMMDD bounds; monthly ones (`trust_scale`, `dls_dlb`, `els_elb`,
`overseas_derivatives`) take YYYYMM. The output is typed snake_case columns
(`bas_dt`, `investor_deposit`, `margin_loan_total`, ...). Data starts 2021-11-16 and
updates once a day.

## Prerequisite

```
pipx install data-go-kr      # or: pip install data-go-kr
```

A data.go.kr **decoding** key must be configured (env `DATA_GO_KR_API_KEY` or
`~/.config/data-go-kr/credentials.json`), and the KOFIA dataset applied for
(활용신청) on that account.

## Running

```
gokr kofia <operation> [--begin YYYYMMDD] [--end YYYYMMDD] [--json]
```

## Procedure

1. **Pick the operation.** Unsure? Run `gokr list` (offline) and match the concept.
2. **Run.**
   ```bash
   gokr kofia market_funds --begin 20240101 --end 20240131
   ```
   Add `--json` when the user wants machine-readable data.
3. **Relay the result.** Show the CLI's stdout; the text view caps at 20 rows, so use
   `--json` for a full series.
4. **Error handling.** A one-line `gokr: <message>` on stderr:
   - a `[30]`/`[20]` auth error -> the key is wrong, is the *encoding* form by mistake,
     or the dataset is not applied for.
   - a `[22]`/`[23]` rate limit -> the daily traffic limit; wait and retry.
   - `unknown operation` (exit 2) -> run `gokr list` and correct the name.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- Customs trade data is the **customs** skill's job.
