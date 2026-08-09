"""``python -m data_go_kr`` -- the same entry point as the ``gokr`` console script."""

from __future__ import annotations

from .cli import main

raise SystemExit(main())
