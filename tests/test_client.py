"""Client wiring -- lazy cached surfaces sharing one key and timeout, no network."""

from pydatagokr import Customs, DataGoKr, Kofia


def test_construction_needs_no_key(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("DATAGOKR_API_KEY", raising=False)
    # Surfaces are lazy: construction resolves no key and builds no sub-surface.
    assert "kofia" not in vars(DataGoKr())


def test_surfaces_are_lazy_and_cached():
    client = DataGoKr(api_key="k")
    assert "kofia" not in vars(client)           # not built at construction
    assert "customs" not in vars(client)
    kofia = client.kofia
    assert isinstance(kofia, Kofia)
    assert client.kofia is kofia                 # cached_property: built once
    assert isinstance(client.customs, Customs)


def test_surfaces_share_key_and_timeout():
    client = DataGoKr(api_key="shared-key", timeout=7.0)
    assert client.kofia._session._api_key == "shared-key"
    assert client.customs._session._api_key == "shared-key"
    assert client.kofia._session.timeout == 7.0
    assert client.customs._session.timeout == 7.0


def test_surface_response_formats_differ():
    client = DataGoKr(api_key="k")
    assert client.kofia._session.response_format == "json"
    assert client.kofia._session.json_param == "resultType"
    assert client.customs._session.response_format == "xml"


def test_repr_never_shows_the_key():
    client = DataGoKr(api_key="SECRETKEY123")
    assert "SECRETKEY123" not in repr(client)
    assert "SECRETKEY123" not in repr(client.kofia)
    assert "SECRETKEY123" not in repr(client.customs)
