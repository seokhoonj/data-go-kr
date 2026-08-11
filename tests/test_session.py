"""The portal envelope contract and paging, offline via an injected fake opener."""

import http.client
import io
import json
import urllib.error
import urllib.parse
from email.message import Message

import pytest

from data_go_kr.errors import (
    DataGoKrAuthError,
    DataGoKrError,
    DataGoKrNetworkError,
    DataGoKrRateLimitError,
    DataGoKrResponseError,
)
from data_go_kr.session import _PAGE_CAP, DataGoKrSession

_BASE = "https://apis.data.go.kr/0000000/service/TestService"
# A key with reserved characters, so single- vs double-encoding is observable.
_KEY = "raw+key/with==specials"


class _FakeResponse:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._raw


class _ReadFails:
    """A response that opens fine but raises when its body is read (a mid-read failure)."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        raise self._exc


class _FakeOpener:
    """Returns canned bodies (or raises canned exceptions), recording each request.

    An outcome may be ``bytes`` (wrapped in a response), an ``Exception`` (raised from
    ``open``), or a pre-built response object (returned as-is, e.g. one whose ``read``
    raises).
    """

    def __init__(self, *outcomes):
        self._outcomes = list(outcomes)
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, bytes):
            return _FakeResponse(outcome)
        return outcome


class _InfiniteOpener:
    """Returns the same non-empty, count-less body on every call (a runaway series)."""

    def __init__(self, body: bytes) -> None:
        self._body = body
        self.requests: list[object] = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return _FakeResponse(self._body)


def _session(*outcomes, **kwargs):
    opener = _FakeOpener(*outcomes)
    return DataGoKrSession(_BASE, _KEY, opener=opener, **kwargs), opener


def _body(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _envelope(items, *, total=None, code="00", message="NORMAL SERVICE."):
    body = {}
    if items is not None:
        body["items"] = {"item": items}
    if total is not None:
        body["totalCount"] = total
    return _body({"response": {"header": {"resultCode": code, "resultMsg": message},
                               "body": body}})


def _fault(code, err_msg="SERVICE ERROR.", auth_msg=None):
    header = {"returnReasonCode": code, "errMsg": err_msg}
    if auth_msg is not None:
        header["returnAuthMsg"] = auth_msg
    return _body({"OpenAPI_ServiceResponse": {"cmmMsgHeader": header}})


def _xml_envelope(items, *, total=None, code="00", message="NORMAL SERVICE."):
    """The XML-only service's envelope -- the same nested shape as ``_envelope`` in XML.
    ``items`` may be ``None`` (no ``<items>``) or a (possibly empty) list of row dicts."""
    parts = [f"<header><resultCode>{code}</resultCode>"
             f"<resultMsg>{message}</resultMsg></header>"]
    body = ""
    if items is not None:
        rows = "".join(
            "<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>"
            for item in items)
        body += f"<items>{rows}</items>"
    if total is not None:
        body += f"<totalCount>{total}</totalCount>"
    parts.append(f"<body>{body}</body>")
    return f"<response>{''.join(parts)}</response>".encode()


def _xml_fault(code, *, err_msg="SERVICE ERROR.", auth_msg=None):
    header = (f"<returnReasonCode>{code}</returnReasonCode>"
              f"<errMsg>{err_msg}</errMsg>")
    if auth_msg is not None:
        header += f"<returnAuthMsg>{auth_msg}</returnAuthMsg>"
    return (f"<OpenAPI_ServiceResponse><cmmMsgHeader>{header}"
            f"</cmmMsgHeader></OpenAPI_ServiceResponse>").encode()


def _http_error(status):
    return urllib.error.HTTPError("https://x", status, "msg", Message(), io.BytesIO(b""))


# --- request building --------------------------------------------------------

def test_decoding_key_is_single_encoded():
    session, opener = _session(_envelope([], total=0))
    session.fetch("getThing")
    url = opener.requests[0].full_url
    once = urllib.parse.quote_plus(_KEY)
    assert f"serviceKey={once}" in url                       # encoded exactly once
    assert urllib.parse.quote_plus(once) not in url          # never double-encoded
    assert _KEY not in url                                   # reserved chars did escape


def test_request_carries_json_param_paging_and_filters():
    session, opener = _session(_envelope([], total=0))
    session.fetch("getThing", num_of_rows=500, beginBasDt="20240101", endBasDt=None)
    url = opener.requests[0].full_url
    assert url.startswith(f"{_BASE}/getThing?")
    assert "resultType=json" in url
    assert "numOfRows=500" in url and "pageNo=1" in url
    assert "beginBasDt=20240101" in url
    assert "endBasDt" not in url                             # None filters are omitted


def test_underscore_type_json_param():
    session, opener = _session(_envelope([], total=0), json_param="_type")
    session.fetch("getThing")
    assert "_type=json" in opener.requests[0].full_url
    assert "resultType" not in opener.requests[0].full_url


# --- the success envelope ----------------------------------------------------

def test_rows_come_back_as_string_dicts():
    session, _ = _session(_envelope([{"basDt": "20240105", "amt": 1234, "gap": None}],
                                    total=1))
    assert session.fetch("getThing") == [{"basDt": "20240105", "amt": "1234", "gap": ""}]


def test_single_dict_item_is_normalized_to_a_list():
    # A one-row page arrives as a bare object, not a one-element array.
    session, _ = _session(_envelope({"basDt": "20240105"}, total=1))
    assert session.fetch("getThing") == [{"basDt": "20240105"}]


def test_empty_items_marker_is_empty_list():
    # An empty page arrives as items: "" on some services.
    session, _ = _session(_body({"response": {"header": {"resultCode": "00"},
                                              "body": {"items": "", "totalCount": 0}}}))
    assert session.fetch("getThing") == []


def test_paging_follows_total_count():
    session, opener = _session(
        _envelope([{"n": "1"}], total=2),
        _envelope([{"n": "2"}], total=2),
    )
    rows = session.fetch("getThing", num_of_rows=1)
    assert rows == [{"n": "1"}, {"n": "2"}]
    assert len(opener.requests) == 2                         # stopped at totalCount
    assert "pageNo=2" in opener.requests[1].full_url


def test_missing_total_count_stops_on_the_empty_page():
    session, opener = _session(
        _envelope([{"n": "1"}]),                             # no totalCount at all
        _envelope([], total=None),
    )
    assert session.fetch("getThing", num_of_rows=1) == [{"n": "1"}]
    assert len(opener.requests) == 2


def test_short_page_is_the_last_page():
    # A service that returns the whole result in one call -- fewer than num_of_rows, no
    # totalCount, ignoring pageNo (the customs endpoint) -- must stop after the one
    # request. Without the short-page stop this opener would loop to _PAGE_CAP.
    opener = _InfiniteOpener(_envelope([{"n": "1"}, {"n": "2"}, {"n": "3"}]))
    session = DataGoKrSession(_BASE, _KEY, opener=opener)
    rows = session.fetch("getThing", num_of_rows=1000)
    assert rows == [{"n": "1"}, {"n": "2"}, {"n": "3"}]
    assert len(opener.requests) == 1                         # 3 < 1000 = last page


def test_countless_run_raises_at_the_page_cap():
    # A service that returns a FULL page (num_of_rows rows) every time but never a
    # totalCount could page forever; the runaway guard stops at _PAGE_CAP calls and
    # refuses to return a silently truncated result.
    opener = _InfiniteOpener(_envelope([{"n": "1"}]))       # full page (1 == num_of_rows)
    session = DataGoKrSession(_BASE, _KEY, opener=opener)
    with pytest.raises(DataGoKrError) as exc:
        session.fetch("getThing", num_of_rows=1)
    assert len(opener.requests) == _PAGE_CAP
    assert "getThing" in str(exc.value)


def test_non_object_row_raises():
    session, _ = _session(_envelope(["junk"], total=1))
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


# --- error-A: the service's own resultCode -----------------------------------

def test_no_data_result_code_is_empty_not_error():
    session, _ = _session(_envelope(None, code="03", message="NODATA_ERROR"))
    assert session.fetch("getThing") == []


def test_other_result_code_raises_response_error():
    session, _ = _session(_envelope(None, code="99", message="UNKNOWN_ERROR"))
    with pytest.raises(DataGoKrResponseError) as exc:
        session.fetch("getThing")
    assert exc.value.code == "99"
    assert "[99]" in str(exc.value)


@pytest.mark.parametrize("code,exc_type", [
    ("1",   DataGoKrResponseError),
    ("4",   DataGoKrResponseError),
    ("30",  DataGoKrAuthError),
    ("030", DataGoKrAuthError),       # 3-digit zero-padded (국토부 RTMS style)
    ("22",  DataGoKrRateLimitError),
    ("022", DataGoKrRateLimitError),  # padded traffic code still backs off, not generic
])
def test_result_code_maps_like_the_portal_fault(code, exc_type):
    # The service-envelope resultCode (error-A) shares the portal's reason vocabulary, so
    # it must map to the same class -- and carry the raw code on .code -- as the fault
    # path, whether the agency zero-pads to two digits or three.
    session, _ = _session(_envelope(None, code=code, message="X"))
    with pytest.raises(exc_type) as exc:
        session.fetch("getThing")
    assert exc.value.code == code


# --- error-B: the portal fault envelope --------------------------------------

def test_fault_30_unregistered_key_raises_auth_error():
    session, _ = _session(_fault("30", auth_msg="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"))
    with pytest.raises(DataGoKrAuthError) as exc:
        session.fetch("getThing")
    assert exc.value.code == "30"


def test_fault_20_missing_key_raises_auth_error():
    session, _ = _session(_fault("20"))
    with pytest.raises(DataGoKrAuthError):
        session.fetch("getThing")


def test_fault_31_expired_deadline_raises_auth_error():
    # 31 = DEADLINE_HAS_EXPIRED: the service-use period lapsed, an access failure like a
    # rejected key, so it maps to the auth error, not a plain response error.
    session, _ = _session(_fault("31", auth_msg="DEADLINE_HAS_EXPIRED_ERROR"))
    with pytest.raises(DataGoKrAuthError):
        session.fetch("getThing")


@pytest.mark.parametrize("code", ["22", "23"])
def test_fault_traffic_codes_raise_rate_limit(code):
    session, _ = _session(_fault(code, auth_msg="LIMITED_NUMBER_OF_SERVICE_REQUESTS"))
    with pytest.raises(DataGoKrRateLimitError) as exc:
        session.fetch("getThing")
    assert exc.value.code == code    # carries the code so 22 (daily) vs 23 (per-second)


def test_fault_other_code_raises_response_error():
    session, _ = _session(_fault("12", err_msg="NO_OPENAPI_SERVICE_ERROR"))
    with pytest.raises(DataGoKrResponseError) as exc:
        session.fetch("getThing")
    assert exc.value.code == "12"


# --- transport failures ------------------------------------------------------

def test_http_429_raises_rate_limit():
    session, _ = _session(_http_error(429))
    with pytest.raises(DataGoKrRateLimitError):
        session.fetch("getThing")


def test_http_500_raises_network_error():
    session, _ = _session(_http_error(500))
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


def test_urlerror_raises_network_error():
    session, _ = _session(urllib.error.URLError(OSError("name resolution failed")))
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


def test_non_json_body_raises_network_error():
    # The portal's XML fault (or a maintenance page) is a non-JSON 200.
    session, _ = _session(b"<OpenAPI_ServiceResponse>...</OpenAPI_ServiceResponse>")
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


def test_non_object_json_raises_network_error():
    session, _ = _session(b"[1, 2, 3]")
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


@pytest.mark.parametrize("exc", [
    ConnectionResetError("reset"),
    http.client.IncompleteRead(b"partial"),
])
def test_read_failure_raises_network_error(exc):
    # The connection drops after open() succeeds but during response.read().
    session, _ = _session(_ReadFails(exc))
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


def test_recursion_error_decoding_raises_network_error(monkeypatch):
    # A pathological body can blow the recursion limit inside json.loads; that must
    # surface as our network error, not escape as a raw RecursionError.
    session, _ = _session(_envelope([{"n": "1"}], total=1))

    def boom(*args, **kwargs):
        raise RecursionError

    monkeypatch.setattr(json, "loads", boom)
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


def test_non_utf8_body_raises_network_error():
    session, _ = _session(b"\xff\xfe")                      # not decodable as UTF-8
    with pytest.raises(DataGoKrNetworkError):
        session.fetch("getThing")


# --- the XML transport (an XML-only service like customs) --------------------

def test_xml_rows_match_the_json_path():
    # The XML body decodes into the identical list-of-string-dicts the JSON path yields.
    session, _ = _session(
        _xml_envelope([{"hsCode": "8542", "expDlr": "10"},
                       {"hsCode": "8541", "expDlr": "20"}], total=2),
        response_format="xml")
    assert session.fetch("getThing") == [
        {"hsCode": "8542", "expDlr": "10"},
        {"hsCode": "8541", "expDlr": "20"},
    ]


def test_xml_single_item_is_normalized_to_a_list():
    session, _ = _session(
        _xml_envelope([{"hsCode": "8542"}], total=1), response_format="xml")
    assert session.fetch("getThing") == [{"hsCode": "8542"}]


def test_xml_empty_items_is_empty_list():
    session, _ = _session(_xml_envelope([], total=0), response_format="xml")
    assert session.fetch("getThing") == []


def test_xml_fault_maps_like_the_json_fault():
    session, _ = _session(
        _xml_fault("30", auth_msg="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"),
        response_format="xml")
    with pytest.raises(DataGoKrAuthError) as exc:
        session.fetch("getThing")
    assert exc.value.code == "30"


def test_malformed_xml_raises_network_error_without_the_key():
    session, _ = _session(b"<response><header>", response_format="xml")
    with pytest.raises(DataGoKrNetworkError) as exc:
        session.fetch("getThing")
    assert _KEY not in str(exc.value)
    assert urllib.parse.quote_plus(_KEY) not in str(exc.value)
    assert exc.value.__cause__ is None                       # the parser chain is broken
    assert exc.value.__context__ is None


def test_xml_mode_omits_the_json_param():
    session, opener = _session(_xml_envelope([], total=0), response_format="xml")
    session.fetch("getThing")
    url = opener.requests[0].full_url
    assert "_type=json" not in url and "resultType=json" not in url
    assert "serviceKey=" in url and "numOfRows=" in url and "pageNo=1" in url


# --- the secret never appears ------------------------------------------------

def _failing_sessions():
    return [
        _session(_http_error(500))[0],
        _session(_http_error(429))[0],
        _session(urllib.error.URLError(OSError("dns")))[0],
        _session(b"<xml/>")[0],
        _session(_ReadFails(ConnectionResetError("reset")))[0],
        _session(_fault("30", auth_msg="SERVICE_KEY_IS_NOT_REGISTERED_ERROR"))[0],
        _session(_envelope(None, code="99", message="UNKNOWN_ERROR"))[0],
    ]


def test_key_never_appears_in_any_error():
    encoded = urllib.parse.quote_plus(_KEY)
    for session in _failing_sessions():
        with pytest.raises(Exception) as exc:
            session.fetch("getThing")
        assert _KEY not in str(exc.value)
        assert encoded not in str(exc.value)
        assert exc.value.__cause__ is None                   # the chain is broken
        assert exc.value.__context__ is None


def test_vendor_message_echoing_the_key_is_redacted():
    # The portal error text is external; if it echoes the key (raw or encoded), the
    # session must scrub it before it reaches the message.
    encoded = urllib.parse.quote_plus(_KEY)
    session, _ = _session(_fault("31", err_msg=f"bad request {_KEY} / {encoded}"))
    with pytest.raises(DataGoKrResponseError) as exc:
        session.fetch("getThing")
    assert _KEY not in str(exc.value)
    assert encoded not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_vendor_message_echoing_the_path_encoded_key_is_redacted():
    # The path-encoded form (quote, '/' left intact) differs from the query form
    # (quote_plus); the session must scrub that representation too.
    path_encoded = urllib.parse.quote(_KEY)
    assert path_encoded != urllib.parse.quote_plus(_KEY)     # the two forms really differ
    session, _ = _session(_fault("31", err_msg=f"bad request {path_encoded}"))
    with pytest.raises(DataGoKrResponseError) as exc:
        session.fetch("getThing")
    assert path_encoded not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_repr_never_shows_the_key():
    session, _ = _session()
    assert _KEY not in repr(session)


# --- construction ------------------------------------------------------------

@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), "30", True])
def test_invalid_timeout_is_rejected(timeout):
    with pytest.raises(ValueError):
        DataGoKrSession(_BASE, _KEY, timeout=timeout)


def test_base_url_trailing_slash_is_normalized():
    opener = _FakeOpener(_envelope([], total=0))
    slashed = DataGoKrSession(_BASE + "/", _KEY, opener=opener)
    slashed.fetch("getThing")
    assert opener.requests[0].full_url.startswith(f"{_BASE}/getThing?")
