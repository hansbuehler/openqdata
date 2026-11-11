"""WRDS connection selection, including a Python 3.14 compatible transport.

The upstream WRDS SDK pins Pandas below 2.3. Python 3.14 uses a narrow
SQLAlchemy transport instead, preserving the three operations IvyDB needs.
Credentials use libpq's standard .pgpass / PGPASSFILE support; no secrets
are read into package configuration or persisted by this module.
"""
from __future__ import annotations

import os
import sys
from typing import Protocol

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL


class WRDSConnection(Protocol):
    """Subset of the vendor connection interface used by the data client."""

    def raw_sql(self, query: str) -> pd.DataFrame: ...
    def list_libraries(self) -> list[str]: ...
    def list_tables(self, library: str) -> list[str]: ...
    def close(self) -> None: ...


class PostgreSQLConnection:
    """Read WRDS using SQLAlchemy and libpq authentication, without SDK pins.

    This is a data-query transport, not a replacement for all SDK features.
    PGHOST, PGPORT and PGDATABASE may override the standard WRDS endpoint.
    A configured .pgpass file (or PGPASSFILE) is required for password auth.
    """

    def __init__(self, username: str) -> None:
        url = URL.create(
            "postgresql+psycopg2", username=username,
            host=os.environ.get("PGHOST", "wrds-pgdata.wharton.upenn.edu"),
            port=int(os.environ.get("PGPORT", "9737")),
            database=os.environ.get("PGDATABASE", "wrds"),
        )
        self.engine = create_engine(url, connect_args={"sslmode": "require", "connect_timeout": 30})
        # Match the vendor SDK's eager connection check without issuing a query.
        with self.engine.connect():
            pass

    def raw_sql(self, query: str) -> pd.DataFrame:
        """Execute a query and return vendor-compatible Pandas observations."""
        with self.engine.connect() as connection:
            return pd.read_sql_query(text(query), connection)

    def list_libraries(self) -> list[str]:
        """List database schemas visible to the current account."""
        return inspect(self.engine).get_schema_names()

    def list_tables(self, library: str) -> list[str]:
        """List both physical tables and views in an IvyDB library."""
        inspector = inspect(self.engine)
        return sorted(set(inspector.get_table_names(schema=library)) | set(inspector.get_view_names(schema=library)))

    def close(self) -> None:
        """Release connections owned by this transport."""
        self.engine.dispose()


def connect_wrds(username: str) -> WRDSConnection:
    """Select the vendor SDK on 3.12/3.13 and the narrow transport on 3.14."""
    if sys.version_info >= (3, 14):
        return PostgreSQLConnection(username)
    import wrds
    return wrds.Connection(wrds_username=username)
