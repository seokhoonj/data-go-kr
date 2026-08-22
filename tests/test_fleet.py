"""Fleet parity across the hand-maintained service enumerations.

A service is declared in four independent places -- its module's registry constants,
`catalog._SERVICES`, a `DataGoKr` accessor, and a CLI subcommand. Adding a ninth service (or
renaming one) means editing all four; forgetting one ships a silently incomplete surface (in
the catalog but unreachable on the client, or listed but rejected by the CLI). These tests
fail the moment the four drift, so the drift is caught in CI, not by a user.
"""

import argparse
import pkgutil

import pydatagokr
import pydatagokr.services as services_pkg
from pydatagokr import cli
from pydatagokr.catalog import _SERVICES

_SERVICE_NAMES = {mod.SERVICE for mod in _SERVICES}


def test_every_registered_module_exposes_the_registry_surface():
    for mod in _SERVICES:
        for attr in ("SERVICE", "AGENCY", "BASE_URL", "TABLES"):
            assert hasattr(mod, attr), f"a registered service module is missing {attr}"
        assert isinstance(mod.TABLES, dict) and mod.TABLES, f"{mod.SERVICE} has no TABLES"


def test_every_catalog_service_is_reachable_on_the_client():
    # Class-level access returns the cached_property descriptor without building a session
    # (so no key is needed) -- it just proves the accessor exists.
    for name in _SERVICE_NAMES:
        assert hasattr(pydatagokr.DataGoKr, name), f"DataGoKr has no .{name} accessor"


def test_every_catalog_service_has_a_cli_subcommand():
    parser = cli._make_parser()
    subparsers = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    choices = set(subparsers.choices)
    for name in _SERVICE_NAMES:
        assert name in choices, f"service {name!r} has no CLI subcommand"


def test_no_service_module_is_left_out_of_the_registry():
    # By convention a service module's basename equals its SERVICE, so an unregistered
    # services/<name>.py is one whose basename is not among the registered service names.
    for info in pkgutil.iter_modules(services_pkg.__path__):
        if info.name.startswith("_"):
            continue
        assert info.name in _SERVICE_NAMES, (
            f"services/{info.name}.py exists but is not in catalog._SERVICES")
