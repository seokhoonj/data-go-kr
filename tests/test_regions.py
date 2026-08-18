import pytest

from data_go_kr import land_region, lawd_code, temp_region


def test_lawd_unique():
    assert lawd_code("종로구") == "11110"


def test_lawd_ambiguous_lists_candidates():
    # 중구 exists in several 시도; the error must name them and ask for a 시도 qualifier.
    with pytest.raises(ValueError) as exc:
        lawd_code("중구")
    msg = str(exc.value)
    assert "서울특별시 중구" in msg and "부산광역시 중구" in msg


def test_lawd_sido_qualifier():
    assert lawd_code("서울 중구") == "11140"


def test_lawd_sido_alias():
    # 경남 is not a substring of 경상남도, so the alias table must map it.
    assert lawd_code("경남 고성군") == lawd_code("경상남도 고성군")


def test_lawd_ilban_gu_by_parent_city():
    # 일반구: name stored as "수원시장안구"; both the parent-city qualifier and the bare 구 work.
    code = lawd_code("수원시장안구")
    assert code == lawd_code("수원시 장안구") == lawd_code("장안구")
    assert code.startswith("411")


def test_lawd_unknown():
    with pytest.raises(ValueError):
        lawd_code("없는구")


def test_land_region():
    assert land_region("서울") == "11B00000"      # matches "서울.인천.경기"


def test_temp_region():
    assert temp_region("서울") == "11B10101"


def test_temp_region_unknown():
    with pytest.raises(ValueError):
        temp_region("없는도시")
