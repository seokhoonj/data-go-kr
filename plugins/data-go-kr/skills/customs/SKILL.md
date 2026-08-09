---
name: customs
description: "Fetch Korea Customs Service (관세청) monthly item trade for one HS code from data.go.kr -- exports, imports, weight, quantity by year-month. Holds no logic of its own -- it calls the data-go-kr package's CLI (`data-go-kr customs item_trade`) and shows the result to the user. Trigger phrases: 수출입실적, 품목별 수출입, HS 코드 수출, 관세청 무역통계, customs trade, item trade, exports by HS code."
---

# data-go-kr — 관세청 수출입 무역통계

Fetch one HS code's monthly 수출입실적 over a YYYYMM range. The output is the vendor's
raw rows (the clean field mapping is pending live verification of the dataset's token
names) -- relay the columns as they come.

## Prerequisite

```
pipx install data-go-kr      # or: pip install data-go-kr
```

A data.go.kr **decoding** key must be configured (env `DATA_GO_KR_API_KEY` or
`~/.config/data-go-kr/credentials.json`), and the 수출입 무역통계 dataset (service
1220000) applied for (활용신청) on that account.

## Running

```
data-go-kr customs item_trade <HS> --begin YYYYMM --end YYYYMM [--json]
```

## Procedure

1. **Get the HS code.** Take it from the user (e.g. semiconductors 8542, cars 8703);
   2-, 4-, 6-, or 10-digit prefixes narrow or widen the item.
2. **Run.**
   ```bash
   data-go-kr customs item_trade 8542 --begin 202401 --end 202406
   ```
   Add `--json` when the user wants machine-readable data.
3. **Relay the result.** Show the CLI's stdout as-is (raw vendor columns).
4. **Error handling.** A one-line `data-go-kr: <message>` on stderr:
   - a `[30]`/`[20]` auth error -> the key is wrong, is the *encoding* form by mistake,
     or service 1220000 is not applied for yet.
   - a `[22]`/`[23]` rate limit -> the daily traffic limit; wait and retry.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- KOFIA market statistics are the **kofia** skill's job.
