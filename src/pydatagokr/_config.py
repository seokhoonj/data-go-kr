"""Resolve the data.go.kr service key from the caller, the environment, or the config file.

The key MUST be the data.go.kr **decoding** (raw) key. The portal issues every key in two
forms -- 인증키 (Encoding), a percent-escaped copy, and 인증키 (Decoding), the raw value --
and this package url-encodes query parameters exactly once, so the raw decoding key is
the one that authenticates; the pre-escaped encoding form gets double-encoded into a
rejected request.

The key is looked up in a fixed order, so an explicit value always wins and a set
environment variable beats a file on disk:

1. the ``api_key`` passed to ``DataGoKr(...)`` / a service surface / a session
2. the ``DATAGOKR_API_KEY`` environment variable
3. ``"DATAGOKR_API_KEY"`` in ``$XDG_CONFIG_HOME/pydatagokr/credentials.json``
   (``$XDG_CONFIG_HOME`` defaults to ``~/.config``)

The file is optional -- its absence just means "no key here." But a file that is present
and unreadable, not JSON, or not a JSON object is an error, because a caller who wrote
one meant it to be used and a silent skip would hide the mistake.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .errors import DataGoKrConfigError

_ENV_VAR = "DATAGOKR_API_KEY"
_CONFIG_DIR = "pydatagokr"
_CONFIG_FILE = "credentials.json"


def resolve_api_key(explicit: str | None) -> str:
    """Return the first key found across the three sources (explicit, env, file).

    Raises :class:`DataGoKrConfigError` when no source supplies a key, or when the resolved
    key contains a control character (a stray newline or tab, usually from a paste).
    """
    key = (explicit or "").strip() or os.environ.get(_ENV_VAR, "").strip() or _key_from_file()
    if not key:
        raise DataGoKrConfigError(
            f"no data.go.kr service key: pass api_key=, set the {_ENV_VAR} environment "
            f"variable, or put it in {credentials_path()} -- use the *decoding* (raw) key"
        )
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in key):
        # A control character (a stray newline/tab, often from a copy-paste) can only be
        # a broken key. Reject it as a config error, before it becomes a request, and
        # never echo the value itself.
        raise DataGoKrConfigError(
            "the data.go.kr service key contains a control character "
            "(a stray newline or tab?)")
    return key


def credentials_path() -> Path:
    """The path pydatagokr reads a stored key from (honoring ``$XDG_CONFIG_HOME``)."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / _CONFIG_DIR / _CONFIG_FILE


def _key_from_file() -> str:
    """The key stored in the credentials file, or ``""`` when the file is absent.

    An absent file is silent (the caller raises the one "no key anywhere" error); a file
    that is present but broken raises :class:`DataGoKrConfigError` here.
    """
    path = credentials_path()
    failure: DataGoKrConfigError | None = None
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        # A UnicodeDecodeError carries the offending bytes, and this file can hold the
        # service key -- from None keeps those bytes out of any traceback.
        failure = DataGoKrConfigError(f"{path} is not valid UTF-8")
    except OSError as err:
        raise DataGoKrConfigError(f"could not read {path}: {err}") from err
    if failure is not None:
        raise failure from None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # A JSONDecodeError retains the parsed text in .doc, and this file can hold the
        # service key -- from None keeps the key out of any traceback.
        failure = DataGoKrConfigError(f"{path} is not valid JSON")
    if failure is not None:
        raise failure from None
    if not isinstance(data, dict):
        raise DataGoKrConfigError(f"{path} must contain a JSON object")

    key = data.get(_ENV_VAR)
    return key.strip() if isinstance(key, str) else ""
