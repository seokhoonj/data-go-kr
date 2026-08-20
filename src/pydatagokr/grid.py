"""Convert a lat/lon to the 기상청 (KMA) 5km forecast grid nx/ny the `weather` service takes.

The formula is KMA's published Lambert Conformal Conic projection (dfs_xy_conv), with the
agency's fixed parameters; it is pure math -- no lookup table, no runtime dependency."""

from __future__ import annotations

import math
from typing import NamedTuple

__all__ = ["Grid", "latlon_to_grid"]

# KMA Lambert Conformal Conic parameters (published grid definition).
_RE = 6371.00877   # earth radius (km)
_GRID = 5.0        # grid spacing (km)
_SLAT1 = 30.0      # standard latitude 1 (deg)
_SLAT2 = 60.0      # standard latitude 2 (deg)
_OLON = 126.0      # reference longitude (deg)
_OLAT = 38.0       # reference latitude (deg)
_XO = 43           # reference X grid point
_YO = 136          # reference Y grid point


class Grid(NamedTuple):
    """A KMA grid cell -- ``nx``/``ny`` as the `weather` service's ``nx``/``ny`` take them."""

    nx: int
    ny: int


def latlon_to_grid(lat: float, lon: float) -> Grid:
    """The KMA grid cell containing decimal-degree ``lat``/``lon`` (Seoul -> ``Grid(60, 127)``)."""
    degrad = math.pi / 180.0
    re = _RE / _GRID
    slat1 = _SLAT1 * degrad
    slat2 = _SLAT2 * degrad
    olon = _OLON * degrad
    olat = _OLAT * degrad

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)

    ra = math.tan(math.pi * 0.25 + lat * degrad * 0.5)
    ra = re * sf / (ra ** sn)
    theta = lon * degrad - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(ra * math.sin(theta) + _XO + 0.5)
    ny = int(ro - ra * math.cos(theta) + _YO + 0.5)
    return Grid(nx, ny)
