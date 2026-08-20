"""Shared type aliases for data-go-kr.

data.go.kr services return each row as a JSON object; this package normalizes every
value to a string (``None`` becomes ``""``), so a row is ``dict[str, str]`` -- ``Row``.
The client passes rows through with the vendor's own field names, and a caller frames a
list of rows into a table in one line (``pandas.DataFrame(rows)`` /
``polars.DataFrame(rows)``) or hands them to :func:`pydatagokr.clean` for typed,
snake_case columns.

``JSONParam`` is the portal's *closed* vocabulary for the "answer in JSON" query
parameter -- older services take ``resultType=json`` (KOFIA), newer ones ``_type=json`` --
typed as a ``Literal`` so a wrong spelling is a type error at the call site rather than an
XML body from the server. ``ResponseFormat`` picks which envelope a session parses: a
service that answers JSON (KOFIA) vs one that is XML-only (customs 품목별 수출입실적, which
faults if the JSON param is sent at all).
"""

from __future__ import annotations

from typing import Literal

__all__ = ["JSONParam", "ResponseFormat", "Row"]

Row = dict[str, str]

JSONParam = Literal["resultType", "_type"]

ResponseFormat = Literal["json", "xml"]
