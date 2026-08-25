"""Connection pool and request-scoped connection dependency."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def create_pool(url: str) -> ConnectionPool:
    return ConnectionPool(url, min_size=1, max_size=5, open=False, kwargs={"row_factory": dict_row})


def get_conn(request: Request) -> Iterator[Connection]:
    pool: ConnectionPool = request.app.state.pool
    with pool.connection() as conn:
        yield conn
