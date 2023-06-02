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
import discord
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


TIMEENJOYED_SERVER: int = 859565527343955998


class Server(Starlette):

    def __init__(self, *, client: discord.Client) -> None:
        self.client = client

        self.database: universal.Database | None = None

        self.commit_queues: dict[str, asyncio.Queue] = {}
        self.team_feed_queues: dict[str, asyncio.Queue] = {}

        routes: list[Route] = [
            Route('/api/github/commit_feed', self.event_commit, methods=['GET']),
            Route('/api/github/{team_id:int}/{team_token:str}', self.receive_github, methods=['POST']),
            Route('/api/teams/feed', self.team_feed, methods=['GET']),
            Route('/api/teams/update', self.receive_team_feed_update, methods=['POST']),
            Route('/api/teams/feed_event', self.event_team_feed, methods=['GET']),
        ]

        super().__init__(
            debug=universal.CONFIG['SERVER']['debug'],
            routes=routes,
            middleware=[Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])],
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

        team: list[asyncpg.Record] = await self.database.fetch_team(team_id=int(id_))
        if not team:
            return Response(status_code=404)

        team: asyncpg.Record = team[0]

        if team['token'] != token:
            return Response(status_code=401)

        data: dict[str, Any] = await request.json()
        to_send: dict[str, Any] = {'team': {'name': team['name']}}

        try:
            data['commits']
        except KeyError:
            return Response(status_code=200)

        sender: dict[str, str] = {'name': data['sender']['login'], 'avatar': data['sender']['avatar_url']}
        commits: list[dict[str, str]] = []

        for commit in data['commits']:
            commit_: dict[str, str] = {'author': commit['author']['name'], 'message': commit['message']}
            commits.append(commit_)

        to_send.update(sender=sender, commits=commits[0:5], commit_length=len(commits))

        for queue in self.commit_queues.values():
            await queue.put(to_send)

        return Response(status_code=200)

    async def get_team_feed(self) -> dict[str | None, list[dict[str, str]]]:
        guild: discord.Guild = self.client.get_guild(TIMEENJOYED_SERVER)
        members: list[asyncpg.Record] = await self.database.fetch_members()

        data: dict[str | None, list[dict[str, str]]] = {}
        for member in members:

            dmember: discord.Member = guild.get_member(member['member_id'])
            member_data: dict[str, str | bool] = {
                'name': dmember.display_name,
                'avatar': dmember.display_avatar.url,
                'languages': member['languages'],
                'timezone': member['timezone'].total_seconds() / (60 * 60),
                'solo': member['solo']
            }

            try:
                # name is actually team name...
                data[member['name']].append(member_data)
            except KeyError:
                data[member['name']] = [member_data]

        return data

    async def team_feed(self, request: Request) -> JSONResponse | Response:
        data: dict[str | None, list[dict[str, str]]] = await self.get_team_feed()

        return JSONResponse(data, status_code=200)

    async def event_team_feed(self, request: Request) -> EventSourceResponse:
        id_: str = str(uuid.uuid4())

        self.team_feed_queues[id_] = asyncio.Queue()
        return EventSourceResponse(self.publisher_team_feed(request, id_))

    async def publisher_team_feed(self, request: Request, id_: str, /) -> dict[str, Any]:
        await self.client.wait_until_ready()

        queue: asyncio.Queue = self.team_feed_queues[id_]
        await queue.put(await self.get_team_feed())

        while True:
            try:
                payload: dict[str | None, list[dict[str, str]]] = await queue.get()
                yield json.dumps(payload)
            except asyncio.CancelledError:
                break

            if await request.is_disconnected():
                break

        del self.team_feed_queues[id_]

    async def receive_team_feed_update(self, request: Request) -> Response:
        auth: str = request.headers.get('authorization', None)
        if not auth:
            return Response(status_code=401)

        secret: str = universal.CONFIG['TOKENS']['backend']
        if secret != auth:
            return Response(status_code=401)

        data: dict[str | None, list[dict[str, str]]] = await self.get_team_feed()

        for queue in self.team_feed_queues.values():
            await queue.put(data)

        return Response(status_code=200)
