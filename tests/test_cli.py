"""CLI -- the offline list command, argument validation, and the fetch dispatch paths
with the session's opener faked so no key file or network is needed."""

import json

import pytest

from data_go_kr import session as session_mod
from data_go_kr.cli import main


def _body(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _envelope(items, total):
    return _body({"response": {"header": {"resultCode": "00", "resultMsg": "NORMAL"},
                               "body": {"items": {"item": items}, "totalCount": total}}})


def _xml_envelope(items, total):
    rows = "".join(
        "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
        for item in items)
    return (f"<response><header><resultCode>00</resultCode>"
            f"<resultMsg>NORMAL</resultMsg></header>"
            f"<body><items>{rows}</items>"
            f"<totalCount>{total}</totalCount></body></response>").encode()


def _fake_opener(monkeypatch, body: bytes):
    """Point the package opener at a fake; returns the list of captured URLs."""
    urls = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return body

    def open(request, timeout=None):
        urls.append(request.full_url)
        return _Response()

    monkeypatch.setattr(session_mod._OPENER, "open", open)
    return urls


@pytest.fixture
def keyed_env(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("DATA_GO_KR_API_KEY", "test-key")


# --- list (offline, keyless) -------------------------------------------------

def test_list_needs_no_key(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "kofia market_funds" in out
    assert "kofia credit_balance" in out
    assert "customs item_trade" in out


def test_list_json(capsys):
    assert main(["list", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"kofia", "customs", "holidays", "realestate", "weather", "airquality"}
    assert "market_funds" in data["kofia"]
    assert data["customs"] == ["item_trade"]


# --- fields (offline, keyless) -----------------------------------------------

def test_fields_needs_no_key(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)
    assert main(["fields", "kofia", "market_funds"]) == 0
    out = capsys.readouterr().out
    assert "basDt" in out and "bas_dt" in out and "date_ymd" in out


def test_fields_json(capsys):
    assert main(["fields", "kofia", "market_funds", "--json"]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema[0] == {"token": "basDt", "column": "bas_dt",
                         "kind": "date_ymd", "is_key": True}


def test_fields_unknown_operation_is_usage_error(capsys):
    assert main(["fields", "kofia", "nope"]) == 2
    assert "unknown operation" in capsys.readouterr().err


def test_fields_unknown_service_is_usage_error(capsys):
    assert main(["fields", "nope", "market_funds"]) == 2
    assert "unknown service" in capsys.readouterr().err


def test_version_flag():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_bad_command_is_usage_error():
    with pytest.raises(SystemExit) as exc:
        main(["frobnicate"])
    assert exc.value.code == 2


# --- kofia -------------------------------------------------------------------

def test_kofia_unknown_operation_is_usage_error(capsys, keyed_env):
    assert main(["kofia", "nope"]) == 2
    assert "unknown operation" in capsys.readouterr().err


def test_kofia_fetch_renders_clean_rows(capsys, keyed_env, monkeypatch):
    urls = _fake_opener(monkeypatch, _envelope(
        [{"basDt": "20240105", "invrDpsgAmt": "50,123"}], total=1))
    assert main(["kofia", "market_funds", "--begin", "20240105", "--end", "20240105"]) == 0
    out = capsys.readouterr().out
    assert "bas_dt" in out and "2024-01-05" in out           # cleaned columns
    assert "50123" in out
    assert "beginBasDt=20240105" in urls[0]
    assert "resultType=json" in urls[0]


def test_kofia_fetch_json(capsys, keyed_env, monkeypatch):
    _fake_opener(monkeypatch, _envelope([{"basDt": "20240105"}], total=1))
    assert main(["kofia", "market_funds", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["bas_dt"] == "2024-01-05"


# --- customs -----------------------------------------------------------------

def test_customs_item_trade_sends_range_and_cleans(capsys, keyed_env, monkeypatch):
    # The XML-only service: the CLI cleans by default and never sends the JSON flag.
    urls = _fake_opener(monkeypatch, _xml_envelope(
        [{"year": "2026.01", "hsCode": "8542311000", "statKor": "집적회로",
          "expDlr": "123", "expWgt": "4", "impDlr": "5", "impWgt": "6",
          "balPayments": "118"}], total=1))
    assert main(["customs", "item_trade", "8542",
                 "--begin", "202601", "--end", "202603"]) == 0
    out = capsys.readouterr().out
    assert "item_name" in out and "export_usd" in out        # cleaned columns
    assert "2026-01" in out                                  # dotted period parsed
    assert "hsSgn=8542" in urls[0]
    assert "strtYymm=202601" in urls[0] and "endYymm=202603" in urls[0]
    assert "_type=json" not in urls[0] and "resultType=json" not in urls[0]


def test_customs_item_trade_requires_the_range(keyed_env):
    with pytest.raises(SystemExit) as exc:
        main(["customs", "item_trade", "8542"])
    assert exc.value.code == 2


# --- failures ----------------------------------------------------------------

def test_vendor_error_exits_1(capsys, keyed_env, monkeypatch):
    _fake_opener(monkeypatch, _body({"response": {
        "header": {"resultCode": "99", "resultMsg": "UNKNOWN_ERROR"}, "body": {}}}))
    assert main(["kofia", "market_funds"]) == 1
    assert "data-go-kr: " in capsys.readouterr().err
