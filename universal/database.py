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
import tomllib
from typing import Any, Self

import asyncpg

from .logger import Handler


try:
    with open('../config.toml', 'rb') as fp:
        CONFIG: dict[str, Any] = tomllib.load(fp)
except FileNotFoundError:
    with open('config.toml', 'rb') as fp:
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
            try:
                with open('../SCHEMA.sql', 'r') as schema:
                    await connection.execute(schema.read())
            except FileNotFoundError:
                with open('SCHEMA.sql', 'r') as schema:
                    await connection.execute(schema.read())

        logger.info('Completed Database Setup.')

        return self_
