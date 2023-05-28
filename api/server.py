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
import json
import logging
import uuid
from typing import Any

import asyncpg
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
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
        self.commit_queues: dict[str, asyncio.Queue] = {}

        routes: list[Route] = [
            Route('/github/commit_feed', self.event_commit, methods=['GET']),
            Route('/github/{team_id:int}/{team_token:str}', self.receive_github, methods=['POST'])
        ]

        super().__init__(
            debug=universal.CONFIG['SERVER']['debug'],
            routes=routes,
            middleware=[Middleware(CORSMiddleware, allow_origins=['*'])],
            on_startup=[self.on_ready]
        )

    async def on_ready(self) -> None:
        self.database = await universal.Database.setup()

        logger.info('Successfully started API Server.')

    async def publisher_commit(self, request: Request, id_: str, /) -> dict[str, Any]:
        queue: asyncio.Queue = self.commit_queues[id_]

        while True:
            try:
                payload: dict[str, Any] = await queue.get()
                yield json.dumps(payload)
            except asyncio.CancelledError:
                break

            if await request.is_disconnected():
                break

        del self.commit_queues[id_]

    async def event_commit(self, request: Request) -> EventSourceResponse:
        id_: str = str(uuid.uuid4())

        self.commit_queues[id_] = asyncio.Queue()
        return EventSourceResponse(self.publisher_commit(request, id_))

    async def receive_github(self, request: Request) -> Response:
        id_: int = request.path_params['team_id']
        token: str = request.path_params['team_token']

        team: asyncpg.Record = await self.database.fetch_team(team_id=id_)
        if not team:
            return Response(status_code=404)

        if team['token'] != token:
            return Response(status_code=401)

        data: dict[str, Any] = await request.json()
        to_send: dict[str, Any] = {'team': {'id': team['team_id'], 'name': team['name']}}

        sender: dict[str, str] = {'name': data['sender']['login'], 'avatar': data['sender']['avatar_url']}
        commits: list[dict[str, str]] = []

        for commit in data['commits']:
            commit_: dict[str, str] = {'author': commit['author']['name'], 'message': commit['message']}
            commits.append(commit_)

        to_send.update(sender=sender, commits=commits[0:5], commit_length=len(commits))

        for queue in self.commit_queues.values():
            await queue.put(to_send)

        return Response(status_code=200)
