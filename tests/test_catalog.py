"""The offline catalog -- registry-derived services, operations, and field schemas."""

import pytest

from data_go_kr import catalog


def test_services_are_registry_derived():
    listed = {entry["service"]: entry for entry in catalog.services()}
    assert set(listed) == {"kofia", "customs", "holidays", "realestate", "weather"}
    assert listed["kofia"]["base_url"].endswith("GetKofiaStatisticsInfoService")
    assert "관세청" in listed["customs"]["agency"]


def test_operations_lists_a_services_tables():
    ops = catalog.operations("kofia")
    assert "market_funds" in ops and "overseas_derivatives" in ops
    assert catalog.operations("customs") == ["item_trade"]


def test_customs_fields_are_the_confirmed_tokens():
    schema = catalog.fields("customs", "item_trade")
    assert [(field["token"], field["column"]) for field in schema] == [
        ("year",        "period"),
        ("hsCode",      "hs_code"),
        ("statKor",     "item_name"),
        ("expDlr",      "export_usd"),
        ("expWgt",      "export_weight_kg"),
        ("impDlr",      "import_usd"),
        ("impWgt",      "import_weight_kg"),
        ("balPayments", "trade_balance_usd"),
    ]


def test_fields_returns_the_clean_column_schema():
    schema = catalog.fields("kofia", "market_funds")
    assert schema[0] == {"token": "basDt", "column": "bas_dt",
                         "kind": "date_ymd", "is_key": True}
    columns = [field["column"] for field in schema]
    assert "investor_deposit" in columns
    assert all(set(field) == {"token", "column", "kind", "is_key"} for field in schema)


def test_unknown_service_raises_value_error():
    with pytest.raises(ValueError, match="unknown service"):
        catalog.operations("nope")
    with pytest.raises(ValueError, match="unknown service"):
        catalog.fields("nope", "market_funds")


def test_unknown_operation_raises_value_error():
    with pytest.raises(ValueError, match="unknown operation"):
        catalog.fields("kofia", "nope")
