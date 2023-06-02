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

import discord
import uvicorn

try:
    from server import Server
except ImportError:
    from .server import Server

import universal


async def main(client_: discord.Client, /) -> None:

    async with client:

        # Start the backend server...
        config = uvicorn.Config("__main__:app", port=universal.CONFIG['SERVER']['port'], log_level="info")
        server = uvicorn.Server(config)
        server_task: asyncio.Task = asyncio.create_task(server.serve())

        # Start the discord client loop, blocking until it closes...
        await client_.start(token=universal.CONFIG['TOKENS']['bot'])


if __name__ == '__main__':
    intents: discord.Intents = discord.Intents.default()
    intents.members = True

    client: discord.Client = discord.Client(intents=intents)
    app: Server = Server(client=client)

    asyncio.run(main(client))
