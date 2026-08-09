---
name: list
description: "List the data.go.kr services this package wraps and the operation names each accepts -- offline and without a key. Holds no logic of its own -- it calls the data-go-kr package's CLI (`data-go-kr list`) and shows the result to the user. Use this to turn a concept (예탁금, 신용잔고, 수출입실적) into the operation name the kofia/customs skills need. Trigger phrases: 공공데이터 목록, data.go.kr 뭐 조회 가능, KOFIA 통계 목록, list data.go.kr services, what open data is there, data-go-kr operations."
---

# data-go-kr — list services

Show what the wrapped data.go.kr services offer and how to call them, in the same
operation names the Python client uses. `data-go-kr list` prints each service (`kofia`,
`customs`) and the operations under it, one `service operation` per line -- exactly the
words the **kofia** and **customs** skills take. It reads an in-code catalog, so it runs
**offline and needs no service key**.

## Prerequisite

This plugin calls the `data-go-kr` CLI, so the package must be installed:

```
pipx install data-go-kr      # or: pip install data-go-kr
```

That puts the `data-go-kr` command on PATH. `data-go-kr list` needs **no** key -- only the fetch
skills do.

## Running

```
data-go-kr list [--json]
```

## Procedure

1. **From a concept, find the operation.** Run `data-go-kr list` and scan for the matching
   line (e.g. "예탁금" -> `kofia market_funds`; "신용잔고" -> `kofia credit_balance`;
   "수출입" -> `customs item_trade`).
2. **Relay the result.** Show the CLI's stdout. When the goal is one series, point out
   the operation the user needs, then offer to hand it to the **kofia** or **customs**
   skill.
3. **Error handling.** `command not found: data-go-kr` -> not installed; point the user at
   `pipx install data-go-kr`.

## What this skill does not do

- It does not re-implement the catalog (the package ships it); it always calls the CLI.
- It lists names only -- to fetch data use the **kofia** or **customs** skill.
