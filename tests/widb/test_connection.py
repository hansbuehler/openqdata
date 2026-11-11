from types import SimpleNamespace

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

import openqdata.widb.connection as transport


def test_postgresql_queries_return_dataframe_without_provider_access(monkeypatch):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE observations (secid INTEGER, value FLOAT)"))
        connection.execute(text("INSERT INTO observations VALUES (101, 2.5), (102, 3.5)"))
    client = object.__new__(transport.PostgreSQLConnection)
    client.engine = engine
    result = client.raw_sql("SELECT secid, value FROM observations ORDER BY secid")
    assert result.to_dict("list") == {"secid": [101, 102], "value": [2.5, 3.5]}
    client.close()


def test_table_discovery_includes_views_and_deduplicates(monkeypatch):
    client = object.__new__(transport.PostgreSQLConnection)
    client.engine = object()
    inspector = SimpleNamespace(
        get_schema_names=lambda: ["optionm_all"],
        get_table_names=lambda **kw: ["opprcd2025", "securd"],
        get_view_names=lambda **kw: ["forward_price", "securd"],
    )
    monkeypatch.setattr(transport, "inspect", lambda _: inspector)
    assert client.list_libraries() == ["optionm_all"]
    assert client.list_tables("optionm_all") == ["forward_price", "opprcd2025", "securd"]


def test_python314_selects_transport(monkeypatch):
    marker = object()
    monkeypatch.setattr(transport, "sys", SimpleNamespace(version_info=(3, 14)))
    monkeypatch.setattr(transport, "PostgreSQLConnection", lambda username: marker if username == "fixture" else None)
    assert transport.connect_wrds("fixture") is marker


def test_python313_selects_vendor_sdk(monkeypatch):
    import sys
    marker = object()
    monkeypatch.setattr(transport, "sys", SimpleNamespace(version_info=(3, 13)))
    monkeypatch.setitem(sys.modules, "wrds", SimpleNamespace(Connection=lambda **kw: marker if kw == {"wrds_username": "fixture"} else None))
    assert transport.connect_wrds("fixture") is marker
