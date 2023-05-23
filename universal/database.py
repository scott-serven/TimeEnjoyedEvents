"""
MIT License

Copyright (c) 2023 EvieePy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import logging
import secrets
import tomllib
from typing import Any, Self

import asyncpg

from .logger import Handler


with open('../config.toml', 'rb') as fp:
    CONFIG: dict[str, Any] = tomllib.load(fp)


logging_level: int = CONFIG['LOGGING']['level']
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(level=logging_level)
logger.addHandler(Handler(level=logging_level))
logger.propagate = False


class Database:

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    @classmethod
    async def setup(cls) -> Self:
        self_: Self = cls()

        logger.info('Setting up Database.')
        self_._pool = await asyncpg.create_pool(CONFIG['DATABASE']['dsn'])

        async with self_._pool.acquire() as connection:
            with open('../SCHEMA.sql', 'r') as schema:
                await connection.execute(schema.read())

        logger.info('Completed Database Setup.')

        return self_

    async def create_team(
            self,
            *,
            name: str,
            owner: int,
            role_id: int,
            text_id: int,
            voice_id: int
    ) -> None:
        id_: int = secrets.randbits(32)
        token: str = secrets.token_urlsafe(32)
        invite: str = secrets.token_urlsafe(4)

        query: str = """INSERT INTO teams(id, token, invite, name, owner, role_id, text_id, voice_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"""
        async with self._pool.acquire() as connection:
            await connection.execute(query, id_, token, invite, name, owner, role_id, text_id, voice_id)

    async def fetch_team(
            self,
            *,
            id_: int | None = None,
            token: str | None = None,
            invite: str | None = None,
            owner: int | None = None,
            name: str | None = None,
            text_id: int | None = None,
            role_id: int | None = None
    ) -> asyncpg.Record:

        query: str = """
        SELECT * FROM teams WHERE
            id = $1 OR token = $2 OR invite = $3 OR owner = $4 OR name = $5 OR text_id = $6 OR role_id = $7
            """
        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, id_, token, invite, owner, name, text_id, role_id)

        return row

    async def fetch_teams(self) -> list[asyncpg.Record]:
        query: str = """SELECT * FROM teams"""

        async with self._pool.acquire() as connection:
            rows: list[asyncpg.Record] = await connection.fetch(query)

        return rows
