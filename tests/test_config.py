"""Config resolution -- explicit > env > file, and the failure modes."""

import json
from pathlib import Path

import pytest

from pydatagokr._config import credentials_path, resolve_api_key
from pydatagokr.errors import DataGoKrConfigError


def _point_config_at(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DATA_GO_KR_API_KEY", raising=False)
    return tmp_path / "pydatagokr" / "credentials.json"


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def test_explicit_key_wins(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"DATA_GO_KR_API_KEY": "from-file"}))
    monkeypatch.setenv("DATA_GO_KR_API_KEY", "from-env")
    assert resolve_api_key("from-arg") == "from-arg"


def test_env_beats_file(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"DATA_GO_KR_API_KEY": "from-file"}))
    monkeypatch.setenv("DATA_GO_KR_API_KEY", "from-env")
    assert resolve_api_key(None) == "from-env"


def test_file_is_last_resort(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"DATA_GO_KR_API_KEY": "from-file"}))
    assert resolve_api_key(None) == "from-file"


def test_missing_everywhere_raises(tmp_path, monkeypatch):
    _point_config_at(tmp_path, monkeypatch)  # no file written
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key(None)


def test_whitespace_key_is_not_a_key(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"DATA_GO_KR_API_KEY": "   "}))
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key("   ")


def test_present_but_invalid_json_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, "{not json")
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key(None)


def test_non_object_json_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, "[1, 2, 3]")
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key(None)


def test_present_but_invalid_utf8_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe not utf-8")  # present but undecodable
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key(None)


def test_key_with_control_char_raises_and_never_echoes_the_key():
    # A stray newline inside a pasted key can only be a broken key; reject it as a
    # config error without echoing the value.
    with pytest.raises(DataGoKrConfigError) as exc:
        resolve_api_key("prefix\nSECRETTAIL")
    assert "SECRETTAIL" not in str(exc.value)
    assert "prefix" not in str(exc.value)


def test_present_but_unreadable_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"DATA_GO_KR_API_KEY": "x"}))

    def boom(self, *args, **kwargs):
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "read_text", boom)  # file exists but cannot be read
    with pytest.raises(DataGoKrConfigError):
        resolve_api_key(None)


def test_credentials_path_honors_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert credentials_path() == tmp_path / "pydatagokr" / "credentials.json"
