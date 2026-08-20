---
name: list
description: "List the data.go.kr services this package wraps and the operation names each accepts -- offline and without a key. Holds no logic of its own -- it calls the pydatagokr package's CLI (`datagokr list`) and shows the result to the user. Use this to turn a concept (날씨, 미세먼지, 공휴일, 아파트 실거래가, 중기예보, 입찰공고, 수출입실적, 예탁금) into the operation name the fetch skills need. Trigger phrases: 공공데이터 목록, data.go.kr 뭐 조회 가능, 어떤 데이터 있어, list data.go.kr services, what open data is there, datagokr operations."
---

# datagokr — list services

Show what the wrapped data.go.kr services offer and how to call them, in the same
operation names the Python client uses. `datagokr list` prints each service (`weather`,
`airquality`, `holidays`, `realestate`, `midforecast`, `procurement`, `customs`, `kofia`)
and the operations under it, one `service operation` per line -- exactly the words the
matching fetch skill takes. It reads an in-code catalog, so it runs **offline and needs no
service key**.

## Prerequisite

This plugin calls the `datagokr` CLI, so the package must be installed:

```
pipx install pydatagokr      # or: pip install pydatagokr
```

That puts the `datagokr` command on PATH. `datagokr list` needs **no** key -- only the fetch
skills do.

## Running

```
datagokr list [--json]
```

## Procedure

1. **From a concept, find the operation.** Run `datagokr list` and scan for the matching
   line (e.g. "날씨" -> `weather forecast`; "미세먼지" -> `airquality by_sido`; "공휴일" ->
   `holidays holidays`; "아파트 매매" -> `realestate apt_trade`; "입찰공고" ->
   `procurement services`; "수출입" -> `customs item_trade`).
2. **Relay the result.** Show the CLI's stdout. When the goal is one series, point out
   the operation the user needs, then offer to hand it to the matching fetch skill
   (same name as the service).
3. **Error handling.** `command not found: datagokr` -> not installed; point the user at
   `pipx install pydatagokr`.

## What this skill does not do

- It does not re-implement the catalog (the package ships it); it always calls the CLI.
- It lists names only -- to fetch data use the matching fetch skill (the service's name).
