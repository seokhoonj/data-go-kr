import pytest

from pydatagokr import latlon_to_grid
from pydatagokr.grid import Grid


def test_seoul_reference_point():
    # KMA's canonical example: Seoul (37.5714, 126.9658) -> grid (60, 127).
    assert latlon_to_grid(37.5714, 126.9658) == Grid(60, 127)


def test_returns_named_tuple_for_unpacking():
    g = latlon_to_grid(37.5714, 126.9658)
    nx, ny = g
    assert (nx, ny) == (60, 127)
    assert g.nx == 60 and g.ny == 127


def test_busan_reference_point():
    # 부산 중구 (35.1028, 129.0403) -> (97, 74), a KMA-published grid assignment.
    assert latlon_to_grid(35.1028, 129.0403) == Grid(97, 74)


def test_known_points_pin_the_projection_output():
    # Not independent oracles -- these pin the canonical formula's output so a change to a
    # projection constant is caught. Seoul/부산 above are the real published anchors.
    assert latlon_to_grid(33.4996, 126.5312) == Grid(53, 38)   # 제주
    assert latlon_to_grid(36.3620, 127.3563) == Grid(67, 101)  # 대전 유성
    # Southern points whose cell shifts if a standard latitude drifts (_SLAT1 30->31 moves the
    # first, _SLAT2 60->61 the second), which the anchors above do not detect.
    assert latlon_to_grid(33.20, 126.57) == Grid(53, 31)
    assert latlon_to_grid(33.20, 126.70) == Grid(56, 31)


@pytest.mark.parametrize("lat", [-90.0, 90.0, 91.0, -100.0,
                                 float("nan"), float("inf"), float("-inf")])
def test_pole_or_non_finite_latitude_is_a_clear_error_not_a_zero_division(lat):
    # The projection is singular at the poles; an out-of-range or non-finite latitude must
    # raise a clear ValueError rather than a bare ZeroDivisionError from the formula (a
    # non-finite lat fails the open-interval guard, symmetric with the lon finite check).
    with pytest.raises(ValueError, match="lat must be between"):
        latlon_to_grid(lat, 126.0)


@pytest.mark.parametrize("lon", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_longitude_is_a_clear_error(lon):
    # A non-finite lon reaches int()/math.sin() with an opaque message; guard it symmetrically
    # with lat so the contract failure reads as a domain error.
    with pytest.raises(ValueError, match="lon must be a finite"):
        latlon_to_grid(37.5, lon)
