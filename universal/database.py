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
import datetime
import logging
import secrets
import tomllib
from typing import Any, Self

import asyncpg

from .logger import Handler

# We have to do this for testing purposes, unfortunately...
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
            # We have to do this for testing purposes, unfortunately...
            try:
                with open('../SCHEMA.sql', 'r') as schema:
                    await connection.execute(schema.read())
            except FileNotFoundError:
                with open('SCHEMA.sql', 'r') as schema:
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
    ) -> asyncpg.Record:
        """Create a CodeJam team.

        A Unique ID, token and invite code will automatically be generated.

        Parameters
        ----------
        name: str
            The teams unique name. This must be unique.
        owner: int
            The Discord Member ID. This must be unique.
        role_id: int
            The Discord Role ID the bot has generated. This must be unique.
        text_id: int
            The Discord TextChannel ID the bot has generated. This must be unique.
        voice_id: int
            The Discord VoiceChannel ID the bot has generated. This must be unique.

        Returns
        -------
        asyncpg.Record
            A record containing the data of the created team.
        """
        id_: int = secrets.randbits(32)
        token: str = secrets.token_urlsafe(32)
        invite: str = secrets.token_urlsafe(4)

        query: str = """INSERT INTO teams(team_id, token, invite, name, owner, role_id, text_id, voice_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *"""
        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(
                query,
                id_,
                token,
                invite,
                name,
                owner,
                role_id,
                text_id,
                voice_id
            )

        return row

    async def create_member(
            self,
            *,
            member_id: int,
            languages: list[int],
            timezone: datetime.timedelta,
            solo: bool,
            team_id: int | None = None
    ) -> asyncpg.Record:
        """Create a CodeJam participant.

        Every member is unique.

        Parameters
        ----------
        member_id: int
            The Discord Member ID of the participant.
        languages: list[int]
            A list of ints referencing the programming languages this user prefers. See: enums.LanguageEnum
        timezone: datetime.timedelta
            A timedelta with a range from -12/+12 as the closest estimated timezone of the user.
        solo: bool
            Whether the participant wants to work on a solo team.
        team_id: int | None
            The team ID associated with this member. Could be None if they have no yet joined a team.

        Returns
        -------
        asyncpg.Record
            A record containing the data of the created member.
        """
        query: str = """INSERT INTO members(member_id, languages, timezone, solo, team_id)
                        VALUES ($1, $2, $3, $4, $5) RETURNING *"""

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, member_id, languages, timezone, solo, team_id)

        return row

    async def edit_member_team(self, *, member_id: int, team_id: int | None) -> asyncpg.Record:
        """Set a members team.

        Parameters
        ----------
        member_id: int
            The Discord member ID.
        team_id: int | None
            The unique team identifier. Could be None to remove this member from a team.

        Returns
        -------
        asyncpg.Record
            The data for this member after the update.
        """
        query: str = """
        UPDATE members
        SET team_id = $2
        WHERE member_id = $1
        RETURNING *
        """

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, member_id, team_id)

        return row

    async def edit_team_owner(self, *, member_id: int, team_id: int | None) -> asyncpg.Record:
        """Change the team owner.

        Parameters
        ----------
        member_id: int
            The Discord Member ID of the new owner.
        team_id: int
            The team to update.

        Returns
        -------
        asyncpg.Record
            The data for this team after the update.
        """
        query: str = """
        UPDATE teams
        SET owner = $1
        WHERE team_id = $2
        RETURNING *
        """

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, member_id, team_id)

        return row

    async def fetch_member(self, *, member_id: int) -> asyncpg.Record | None:
        """Fetch a member from the database.

        Parameters
        ----------
        member_id: int
            The Discord Member ID of the participant.

        Returns
        -------
        asyncpg.Record
            A record of the requested member. Could be None if no member was found.
        """
        query: str = """
        SELECT * FROM members
        LEFT OUTER JOIN teams ON members.team_id = teams.team_id
        WHERE member_id = $1
        """

        async with self._pool.acquire() as connection:
            row: asyncpg.Record | None = await connection.fetchrow(query, member_id)

        return row

    async def fetch_members(self) -> list[asyncpg.Record]:
        """Fetch all members and their team from the database.

        Returns
        -------
        list[asyncpg.Record]
            A list of members and their associated team.
        """
        query: str = """
        SELECT * FROM members
        LEFT OUTER JOIN teams ON (members.team_id = teams.team_id)
        """

        async with self._pool.acquire() as connection:
            rows: list[asyncpg.Record] = await connection.fetch(query)

        return rows

    async def fetch_team(
            self,
            *,
            team_id: int | None = None,
            token: str | None = None,
            invite: str | None = None,
            owner: int | None = None,
            name: str | None = None,
            text_id: int | None = None,
            voice_id: int | None = None,
            role_id: int | None = None
    ) -> list[asyncpg.Record]:
        """Fetch a CodeJam team and it's participants from the database.

        All parameters are optional, the first matching parameter will return the team data.
        For example:
            team_id = 1 (This will return the team of ID 1)

            OR

            name = Kroden Warriors (This will return the team of name 'Kroden Warriors', if team ID does not match)

        Parameters
        ----------
        team_id: int | None
            The unique team identifier.
        token: str | None
            The unique team token.
        invite: str | None
            The unique team invite.
        owner: int | None
            The unique Discord Member ID of the team owner.
        name: str | None
            The unique team name.
        text_id: int | None
            The unique Discord TextChannel ID of the team.
        voice_id: int | None
            The unique Discord VoiceChannel ID of the team.
        role_id: int | None
            The unique Discord Role ID of the team.

        Returns
        -------
        list[asyncpg.Record]
            A list of Team and Member data per member OR team data only if the team has no current members.
        """
        query: str = """
        SELECT * FROM teams
        LEFT OUTER JOIN members ON (teams.team_id = members.team_id)
        WHERE teams.team_id = $1 
        OR token = $2 
        OR invite = $3 
        OR owner = $4 
        OR name = $5 
        OR text_id = $6
        OR voice_id = $7
        OR role_id = $8
        """

        async with self._pool.acquire() as connection:
            rows: list[asyncpg.Record] = await connection.fetch(
                query,
                team_id,
                token,
                invite,
                owner,
                name,
                text_id,
                voice_id,
                role_id
            )

        return rows

    async def fetch_teams(self) -> list[asyncpg.Record]:
        """Fetch all teams from the database.

        This does not fetch any member data.
        """
        query: str = """SELECT * FROM teams"""

        async with self._pool.acquire() as connection:
            rows: list[asyncpg.Record] = await connection.fetch(query)

        return rows

    async def edit_team_name(self, *, team_id: int, name: str) -> asyncpg.Record:
        """Edit a CodeJam team name.

        Parameters
        ----------
        team_id: int
            The unique identifier of the team to edit.
        name: str
            The new name.

        Returns
        -------
        asyncpg.Record
            A record of data for the team.

        Raises
        ------
        asyncpg.UniqueViolationError
            The new name was identical to another teams name.
        """
        query: str = """
        UPDATE teams
        SET name = $2
        WHERE team_id = $1
        RETURNING *
        """

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, team_id, name)

        return row

    async def delete_team(self, team_id: int) -> asyncpg.Record:
        """Delete a team from the database.

        This will also remove the team_id data from every associated member of this team.

        Parameters
        ----------
        team_id: int
            The unique team identifier.

        Returns
        -------
        asyncpg.Record
            A record of data containing information of the deleted team.
        """
        query: str = """DELETE FROM teams WHERE team_id = $1 RETURNING *"""

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, team_id)

        return row

    async def create_log(self, *, channel: int, invoker: int, command: str, error: str, traceback: str) -> int:
        """Create an App Command Error Log.

        When an Application Command (Slash Command) fails, we log it in the database.

        Parameters
        ----------
        channel: int
            The Discord Channel ID the App Command failed in.
        invoker: int
            The Discord Member ID the App Command was invoked by.
        command: str
            The command name that triggered this error.
        error: str
            The name of the exception.
        traceback: str
            The exception traceback.

        Returns
        -------
        int
            The error log identifier.
        """
        query: str = """
        INSERT INTO error_log(channel, invoker, command, error, traceback)
        VALUES ($1, $2, $3, $4, $5) RETURNING *
        """

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, channel, invoker, command, error, traceback)

        return row['id']

    async def fetch_log(self, identifier: int) -> asyncpg.Record | None:
        """Fetch an error log from the database, with the given identifier.

        Parameters
        ----------
        identifier: int
            The ID of the error log to fetch.

        Returns
        -------
        asyncpg.Record
            A record of data containing information about the error. Could be None if no error matches that identifier.
        """
        query: str = """SELECT * FROM error_log WHERE id = $1"""

        async with self._pool.acquire() as connection:
            row: asyncpg.Record = await connection.fetchrow(query, identifier)

        return row
