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

# Derived projection constants -- these depend only on the fixed parameters above, so they
# are computed once at import rather than on every call.
_DEGRAD = math.pi / 180.0
_RE_GRID = _RE / _GRID
_OLON_RAD = _OLON * _DEGRAD
_SLAT1_RAD = _SLAT1 * _DEGRAD
_SLAT2_RAD = _SLAT2 * _DEGRAD
_OLAT_RAD = _OLAT * _DEGRAD
_SN = (math.log(math.cos(_SLAT1_RAD) / math.cos(_SLAT2_RAD))
       / math.log(math.tan(math.pi * 0.25 + _SLAT2_RAD * 0.5)
                  / math.tan(math.pi * 0.25 + _SLAT1_RAD * 0.5)))
_SF = (math.tan(math.pi * 0.25 + _SLAT1_RAD * 0.5) ** _SN) * math.cos(_SLAT1_RAD) / _SN
_RO = _RE_GRID * _SF / (math.tan(math.pi * 0.25 + _OLAT_RAD * 0.5) ** _SN)


class Grid(NamedTuple):
    """A KMA grid cell -- ``nx``/``ny`` as the `weather` service's ``nx``/``ny`` take them."""

    nx: int
    ny: int


def latlon_to_grid(lat: float, lon: float) -> Grid:
    """The KMA grid cell containing decimal-degree ``lat``/``lon`` (Seoul -> ``Grid(60, 127)``).

    ``lat`` must be within (-90, 90) -- the projection is singular at the poles -- and ``lon``
    must be finite (any longitude is accepted; it is normalized into range)."""
    if not -90.0 < lat < 90.0:
        raise ValueError(f"lat must be between -90 and 90 degrees, got {lat}")
    if not math.isfinite(lon):
        raise ValueError(f"lon must be a finite number of degrees, got {lon}")
    ra = math.tan(math.pi * 0.25 + lat * _DEGRAD * 0.5)
    ra = _RE_GRID * _SF / (ra ** _SN)
    theta = lon * _DEGRAD - _OLON_RAD
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= _SN

    nx = int(ra * math.sin(theta) + _XO + 0.5)
    ny = int(_RO - ra * math.cos(theta) + _YO + 0.5)
    return Grid(nx, ny)
