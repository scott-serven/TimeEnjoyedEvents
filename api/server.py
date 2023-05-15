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
import asyncio
import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from sse_starlette.sse import EventSourceResponse

import universal


logging_level: int = universal.CONFIG['LOGGING']['level']
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(level=logging_level)
logger.addHandler(universal.Handler(level=logging_level))
logger.propagate = False


class Server(Starlette):

    def __init__(self) -> None:
        self.database: universal.Database | None = None
        self.commit_queue: asyncio.Queue = asyncio.Queue()

        routes: list[Route] = [
            Route('/github/{team_id:int}', self.receive_github, methods=['POST'])
        ]

        super().__init__(debug=universal.CONFIG['SERVER']['debug'], routes=routes, on_startup=[self.on_ready])

    async def on_ready(self) -> None:
        self.database = await universal.Database.setup()

        logger.info('Successfully started API Server.')

    async def event_commit(self, request: Request) -> None:
        pass

    async def receive_github(self, request: Request) -> Response:
        pass
