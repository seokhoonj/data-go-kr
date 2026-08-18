from data_go_kr import latlon_to_grid
from data_go_kr.grid import Grid


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


def test_regression_pins():
    # Not independent oracles -- these pin the canonical formula's output so a change to a
    # projection constant is caught. Seoul/부산 above are the real published anchors.
    assert latlon_to_grid(33.4996, 126.5312) == Grid(53, 38)   # 제주
    assert latlon_to_grid(36.3620, 127.3563) == Grid(67, 101)  # 대전 유성
