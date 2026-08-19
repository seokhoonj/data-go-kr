import json

from data_go_kr.cli import main


def test_grid_prints_nx_ny(capsys):
    assert main(["grid", "37.5714", "126.9658"]) == 0
    assert capsys.readouterr().out.strip() == "60 127"


def test_grid_json(capsys):
    assert main(["grid", "37.5714", "126.9658", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"nx": 60, "ny": 127}


def test_lawd_prints_code(capsys):
    assert main(["lawd", "종로구"]) == 0
    assert capsys.readouterr().out.strip() == "11110"


def test_lawd_ambiguous_exits_2(capsys):
    assert main(["lawd", "중구"]) == 2
    assert "add the 시도" in capsys.readouterr().err


def test_lawd_json(capsys):
    assert main(["lawd", "종로구", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"code": "11110"}


def test_land_region_prints_code(capsys):
    assert main(["land-region", "서울"]) == 0
    assert capsys.readouterr().out.strip() == "11B00000"


def test_temp_region_prints_code(capsys):
    assert main(["temp-region", "서울"]) == 0
    assert capsys.readouterr().out.strip() == "11B10101"


def test_land_region_json(capsys):
    assert main(["land-region", "서울", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"code": "11B00000"}


def test_region_unknown_exits_2(capsys):
    assert main(["land-region", "없는지역"]) == 2
    assert "data-go-kr:" in capsys.readouterr().err
    assert main(["temp-region", "없는도시"]) == 2
    assert "data-go-kr:" in capsys.readouterr().err
