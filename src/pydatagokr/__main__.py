"""``python -m pydatagokr`` -- the same entry point as the ``datagokr`` console script."""

from __future__ import annotations

from .cli import main

raise SystemExit(main())
