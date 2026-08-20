from pydatagokr import _regions_data as d


def test_sigungu_anchor():
    assert ("서울특별시", "종로구", "11110") in d.SIGUNGU


def test_land_zone_anchors():
    assert ("서울.인천.경기", "11B00000") in d.LAND_ZONES
    assert ("전라남도", "11F20000") in d.LAND_ZONES   # KMA zone kept despite the 광주/전남 merge


def test_temp_city_anchor():
    assert ("서울", "11B10101") in d.TEMP_CITIES


def test_codes_are_wellformed():
    assert all(len(code) == 5 and code.isdigit() for _, _, code in d.SIGUNGU)
    assert all(len(code) == 8 for _, code in d.LAND_ZONES)
    assert all(len(code) == 8 for _, code in d.TEMP_CITIES)


def test_no_duplicate_sigungu_rows():
    assert len(d.SIGUNGU) == len(set(d.SIGUNGU))
