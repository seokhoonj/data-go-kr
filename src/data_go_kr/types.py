"""Shared type aliases for data-go-kr.

data.go.kr services return each row as a JSON object; this package normalizes every
value to a string (``None`` becomes ``""``), so a row is ``dict[str, str]`` -- ``Row``.
The client passes rows through with the vendor's own field names, and a caller frames a
list of rows into a table in one line (``pandas.DataFrame(rows)`` /
``polars.DataFrame(rows)``) or hands them to :func:`data_go_kr.clean` for typed,
snake_case columns.

``JsonParam`` is the portal's *closed* vocabulary for the "answer in JSON" query
parameter -- older services take ``resultType=json`` (KOFIA), newer ones ``_type=json``
(customs) -- typed as a ``Literal`` so a wrong spelling is a type error at the call site
rather than an XML body from the server.
"""

from __future__ import annotations

from typing import Literal

__all__ = ["JsonParam", "Row"]

Row = dict[str, str]

JsonParam = Literal["resultType", "_type"]
