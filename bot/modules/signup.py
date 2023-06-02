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
import datetime
import re
import traceback
from typing import Any, Union

import aiohttp
import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

try:
    from .core import *
except ImportError:
    from core import *

import universal


# Only allow A to z, 0 to 9, spaces and _ in team name...
NAME_VALIDATION: re.Pattern = re.compile(r'^[A-Za-z0-9_ ]+$')


# Team Creation Payload type...
CTeamPayload = dict[str, Union[discord.TextChannel, discord.VoiceChannel, discord.Role, asyncpg.Record]]


# Various Discord IDs...
CODEJAM_CATEGORY: int = 1099190969221521469
SIGNUP_CHANNEL: int = 1113310515712770128
MANAGER_ID: int = 1099191306359672894
ANNOUNCEMENTS_ID: int = 1099472498430586970
ERROR_CHANNEL: int = 1112358404992802906
TEAM_ANNOUNCEMENTS_CHANNEL: int = ...


SIGNUP_MESSAGE: str = 'Please select your desired preferences from below:\n\n' \
                      '**1 - Timezone:** Your timezone to nearest hour.\n' \
                      '**2 - Languages:** The languages you would prefer to use (Up to 5).\n' \
                      '**3 - Solo/Team:** Participate as a solo contestant or open to join teams.\n\n' \
                      '**Timezone:**\n{TIMEZONE}\n' \
                      '**Languages:**\n{LANGUAGES}\n' \
                      '**Preference:**\n{PREFERENCES}'


def is_manager():
    """Check whether the command was run by a manager.

    If not NotManagerError is raised.
    """
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.get_role(MANAGER_ID):
            return True

        raise NotManagerError
    return app_commands.check(predicate)


def is_team_owner_or_manager():
    """Check whether the command was run by a team owner or manager.

    If not NotTeamOwnerError is raised.
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.get_role(MANAGER_ID):
            return True

        owners: list[int] = [t['owner'] for t in await interaction.client.database.fetch_teams()]
        if interaction.user.id in owners:
            return True

        raise NotTeamOwnerError
    return app_commands.check(predicate)


def name_validator():
    """Check whether the name provided for '/team create' or '/team name' is valid.

    If not NameViolationError is raised. Which is handled in the Error Handler, and sends back the provided message.
    """
    async def predicate(interaction: discord.Interaction) -> bool:
        name: str = interaction.namespace.name

        if len(name) > 25:
            message: str = 'Your team name can not be over 25 characters long.'
            raise NameViolationError(message)

        if not NAME_VALIDATION.fullmatch(name):
            message: str = 'Your team name can only contain letters, spaces, numbers and underscores.'
            raise NameViolationError(message)

        teams: list[asyncpg.Record] = await interaction.client.database.fetch_teams()
        team_names: list[str] = [t['name'].lower() for t in teams]

        if name.lower() in team_names:
            message: str = f'A team with the name: `{name}` already exists. Please try a new name and try again.'
            raise NameViolationError(message)

        return True
    return app_commands.check(predicate)


async def update_backend(bot: Bot, /) -> None:
    headers: dict[str, str] = {'Authorization': universal.CONFIG['TOKENS']['backend']}
    url: str = 'https://codejam.timeenjoyed.dev/api/teams/update'

    try:
        async with bot.session.post(url, headers=headers) as resp:
            if resp.status != 200:
                logger.warning(f'Unable to reach backend server. Failed with status code: {resp.status}')
            else:
                logger.info('Successfully updated backend server.')
    except aiohttp.ClientConnectorError:
        logger.warning('Unable to reach backend server. Fatal exception occurred.')


class SignupButtonSelect(discord.ui.Select):
    """Select Menu for Signups.

    Could be either:
    - TZSELECT
    - LANGSELECT
    - SOLOSELECT

    Parameters
    ----------
    items: dict[Any, Any]
        The dict of items relating to this select.
    /
    id_: str
        The menu type. 'TZSELECT', 'LANGSELECT', 'SOLOSELECT'.
    placeholder: str
        The placeholder text for the select menu.
    row: int
        The row the menu is on. Between 0 and 4.
    max_selects: int
        The maximum amount of options that could be selected. Defaults to 1.

    Note: The select menus minimum selection is 1. This can not be changed.
    """

    def __init__(self, items: dict[Any, Any], /, *, id_: str, placeholder: str, row: int, max_selects: int = 1) -> None:
        super().__init__(placeholder=placeholder, row=row, max_values=max_selects, min_values=1)

        self._items = items
        self._id = id_

        self.selected_items: list[dict[Any, Any]] = []

        for key, data in items.items():
            self.add_option(label=data['name'], emoji=data['emoji'], value=str(data['value']))

    async def callback(self, interaction: discord.Interaction) -> None:
        """Coroutine called when a selection has been made."""
        view: SignupSelectView = self.view

        try:
            timezone: str = f'{view.timezone_s.selected_items[0]["name"]}'
        except IndexError:
            timezone = '`Not Set`'

        try:
            solo: str = f'`{view.solo_s.selected_items[0]["name"]}`'
        except IndexError:
            solo = '`Not Set`'

        languages: str = '\n'.join(f'{l["emoji"]} - **`{l["name"]}`**' for l in view.languages_s.selected_items)
        if not languages:
            languages = '`Not Set`'

        self.selected_items = [self._items[int(v)] for v in self.values]

        if self._id == 'TZSELECT':
            timezone: str = f'`{self.selected_items[0]["name"]}`'
        elif self._id == 'LANGSELECT':
            languages: str = '\n'.join(f'{l["emoji"]} - **`{l["name"]}`**' for l in self.selected_items)
        else:
            solo: str = f'`{self.selected_items[0]["name"]}`'

        # Resend the message with updated values...
        message: str = SIGNUP_MESSAGE.format(TIMEZONE=timezone, LANGUAGES=languages, PREFERENCES=solo)
        await interaction.response.edit_message(content=message, view=view)


class SignupSelectView(discord.ui.View):
    """Select View for Signups. This view holds the Select Menus."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

        self.all_done: bool = False

        self.timezone_s = SignupButtonSelect(
            timezones,
            placeholder='Please select your timezone...',
            row=0,
            id_='TZSELECT'
        )
        self.languages_s = SignupButtonSelect(
            languages,
            placeholder='Please select your preferred languages...',
            max_selects=5,
            row=1,
            id_='LANGSELECT'
        )
        self.solo_s = SignupButtonSelect(
            preferences,
            placeholder='Please select your team preferences...',
            max_selects=1,
            row=2,
            id_='SOLOSELECT'
        )

        self.add_item(self.timezone_s)
        self.add_item(self.languages_s)
        self.add_item(self.solo_s)

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=3)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.Button) -> None:
        """Button pressed to confirm Select Menu choices."""

        # Check all our children, E.g. each SignupButtonSelect; to see if they have been selected...
        all_done: bool = all(s.selected_items for s in self.children if isinstance(s, SignupButtonSelect))

        if all_done:
            # All menus have had a selection... Stop the view and set all_done
            self.all_done = True
            self.stop()
        else:
            # Not all menus have been selected...
            await interaction.response.send_message('Please finish selecting the required options.', ephemeral=True)


class SignupView(discord.ui.View):
    """Main Signup view.

    Note: This view is persistent. Timeout is None, and each component has a custom_id.
    This view will be added back to the message it was sent from between restarts.
    """

    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        """Check if the member clicking the button has already registered before."""
        member: asyncpg.Record = await interaction.client.database.fetch_member(member_id=interaction.user.id)

        if member:
            await interaction.response.send_message('You are already signed up!', ephemeral=True)
            return False

        return True

    @discord.ui.button(label='Signup', custom_id='SIGNUP_BUTTON', style=discord.ButtonStyle.blurple)
    async def signup_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Start the Signup process for the user.

        This sends the SignupSelectView which holds all our select menus.
        When the SignupSelectView has completed, enter the data into the database, and give them a role.
        """
        select_view: SignupSelectView = SignupSelectView()

        message: str = SIGNUP_MESSAGE.format(TIMEZONE='`Not Set`', LANGUAGES='`Not Set`', PREFERENCES='`Not Set`')
        await interaction.response.send_message(content=message, view=select_view, ephemeral=True)

        await select_view.wait()
        if not select_view.all_done:
            return

        member: discord.Member = interaction.user
        timezone: datetime.timedelta = select_view.timezone_s.selected_items[0]['delta']
        languages: list[int] = [v['value'] for v in select_view.languages_s.selected_items]
        solo: bool = select_view.solo_s.selected_items[0]['bool']

        try:
            await interaction.client.database.create_member(
                member_id=member.id,
                languages=languages,
                timezone=timezone,
                solo=solo
            )
        except asyncpg.UniqueViolationError:
            await interaction.delete_original_response()
            return

        role: discord.Role = interaction.guild.get_role(ANNOUNCEMENTS_ID)
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)

        message: str = "You've Successfully registered for the CodeJam! Next up:\n\n" \
                       "**Creating teams:**\n" \
                       "Once you've found team members, please designate a team leader, " \
                       "someone who will be in charge of creating the team. " \
                       "When a team is created, a new text channel and voice channel will be created " \
                       "as a meeting ground for everyone in the team. " \
                       "These two channels will be accessible to team members only (as well as <@&1099191306359672894>).\n" \
                       "- To create a team: " \
                       "The team leader will type `/team create <team name>` anywhere in this server.\n" \
                       "- Soloists, go ahead and also create a team. (If you want)\n" \
                       "- Note: The team name can **not** be changed. To leave the the team use `/team leave`. " \
                       "The are very strict rate-limits on creating and leaving teams. Please be certain of your name " \
                       "before creating a team.\n\n" \
                       "**Commands:**\n" \
                       "`/team create <team name>` - Creates a team with the given name.\n" \
                       "`/team invite` - Retrieves your teams unique invite code.\n" \
                       "`/team join <code>` - Join a team with the provided invite code.\n" \
                       "`/team leave` - Leave your current team."

        await interaction.delete_original_response()
        await interaction.followup.send(message, ephemeral=True)

        await update_backend(interaction.client)


class Signup(commands.Cog):
    """Signup Cog. This holds all the Application Commands for the Signup/Management of the CodeJam."""

    group = app_commands.Group(name="team", description="Team Management related commands")

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        await update_backend(self.bot)

        view: int = universal.CONFIG['BOT']['view']
        if view == 0:
            return

        self.bot.add_view(SignupView(), message_id=view)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        """Global CodeJam command check.

        Managers bypass this check automatically.
        If not registered or not manager an error is raised and propagated to cog_app_command_error.
        """
        if interaction.user.get_role(MANAGER_ID):
            return True

        if await interaction.client.database.fetch_member(member_id=interaction.user.id):
            return True

        raise NotRegisteredError

    async def cog_app_command_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError
    ) -> None:
        """Handle our command errors.

        If an error is unexpected, catch it and log it into the database and send the ERROR_ID to a channel.
        You can then review the error at anytime with '/error ERROR_ID'.

        Expected Errors:
            core.NotRegisteredError
            core.NotManagerError
            core.NotTeamOwnerError
            core.NameViolationError
            app_commands.CommandOnCooldown
        """
        if interaction.response.is_done():
            send = interaction.followup.send
        else:
            send = interaction.response.send_message

        if isinstance(error, NotRegisteredError):
            message: str = 'You need to be registered for the CodeJam to use this command.'
            await send(message, ephemeral=True)

        elif isinstance(error, NotManagerError):
            message: str = 'Only CodeJam Managers are able to use this command.'
            await send(message, ephemeral=True)

        elif isinstance(error, NotTeamOwnerError):
            message: str = 'Only Team Owners are able to use this command.'
            await send(message, ephemeral=True)

        elif isinstance(error, NameViolationError):
            await send(error.message, ephemeral=True)

        elif isinstance(error, app_commands.CommandOnCooldown):
            dt: datetime.datetime = datetime.datetime.now() + datetime.timedelta(seconds=error.retry_after)
            relative: str = f'<t:{int(dt.timestamp())}:R>'

            message: str = f'This command is currently on cooldown. Try again {relative}'
            await send(message, ephemeral=True)

        else:
            # Notify the user that the command failed...
            message: str = 'An error has occurred. The CodeJam Managers have been notified.'
            await send(message, ephemeral=True)

            # Gather meta data... Including Traceback.
            name: str = type(error).__name__
            message: str = str(error)
            tb: str = ''.join(traceback.format_exception(error))
            channel: int = interaction.channel.id
            invoker: int = interaction.user.id
            command: str = interaction.command.name

            # Enter log into database and return the log ID...
            id_: int = await self.bot.database.create_log(
                channel=channel,
                invoker=invoker,
                command=command,
                error=name,
                traceback=tb
            )

            # Grab the error log channel...
            channel: discord.TextChannel = interaction.guild.get_channel(ERROR_CHANNEL)

            # Send the error log with advice to our error log channel...
            advice: str = f'For more info use `/error {id_}`'
            await channel.send(f'Exception Log **(ID: `{id_}`)**: **{name}** - `{message}` | {advice}')

            # Log that an error occurred in the bot logs...
            logger.warning(f'An exception was logged to the database. ID: {id_}')

    async def fetch_team_by_member_or_channel(self, interaction: discord.Interaction, /) -> list[asyncpg.Record] | None:
        """This allows CodeJam Managers to execute commands in Team Channels."""
        member: asyncpg.Record = await self.bot.database.fetch_member(member_id=interaction.user.id)
        if not member:
            if interaction.user.get_role(MANAGER_ID):
                text_id = voice_id = interaction.channel.id
                team: list[asyncpg.Record] = await self.bot.database.fetch_team(text_id=text_id, voice_id=voice_id)

                return team
            return None

        team: list[asyncpg.Record] = await self.bot.database.fetch_team(team_id=member['team_id'])
        return team

    async def create_team_(self, interaction: discord.Interaction, name: str, owner: discord.Member) -> CTeamPayload:
        """Create a CodeJam Team. This should only be called via the App Command.

        Parameters
        ----------
        interaction: discord.Interaction
            The app command interaction.
        name: str
            The team name.
        owner: discord.Member
            The team creator.

        Returns
        -------
        CTeamPayload
        """
        category: discord.CategoryChannel = interaction.guild.get_channel(CODEJAM_CATEGORY)
        reason: str = f'CodeJam Team Creation: ({owner})'

        # Create Team Role...
        role: discord.Role = await interaction.guild.create_role(name=f'\u2B50-{name}', colour=0xF0B7B1, reason=reason)

        # Channel Permissions...
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.get_role(MANAGER_ID): discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True
            ),
            role: discord.PermissionOverwrite(read_messages=True)
        }

        # Create appropriate Team Channels...
        cname: str = f'\u2B50-{name}'
        text: discord.TextChannel = await category.create_text_channel(cname, reason=reason, overwrites=overwrites)
        voice: discord.VoiceChannel = await category.create_voice_channel(cname, reason=reason, overwrites=overwrites)

        # ADd Team to Database...
        row: asyncpg.Record = await interaction.client.database.create_team(
            name=name,
            owner=owner.id,
            role_id=role.id,
            text_id=text.id,
            voice_id=voice.id
        )

        # The member needs to have their new team id assigned...
        await self.bot.database.edit_member_team(member_id=owner.id, team_id=row['team_id'])

        # Add role to creator...
        await owner.add_roles(role, reason=reason)

        # Send back Team Creation Payload...
        data: CTeamPayload = {'role': role, 'text': text, 'voice': voice, 'team': row}
        return data

    """
    async def change_name_(self, interaction: discord.Interaction, name: str, owner: discord.Member) -> asyncpg.Record:
        reason: str = f'CodeJam Team Edit: ({owner})'
        team: list[asyncpg.Record] = await self.bot.database.fetch_team(owner=owner.id)
        team: asyncpg.Record = team[0]

        role: discord.Role = interaction.guild.get_role(team['role_id'])
        text: discord.TextChannel = interaction.guild.get_channel(team['text_id'])
        voice: discord.VoiceChannel = interaction.guild.get_channel(team['voice_id'])

        await role.edit(name=name, reason=reason)
        await text.edit(name=f'\u2B50-{name}', reason=reason)
        await voice.edit(name=f'\u2B50-{name}', reason=reason)

        row: asyncpg.Record = await self.bot.database.edit_team_name(team_id=team['team_id'], name=name)
        return row
    """

    @group.command(name='create', description='Create a team for the CodeJam')
    @app_commands.checks.cooldown(1, 60 * 60)
    @name_validator()
    async def create_team(self, interaction: discord.Interaction, *, name: str) -> None:
        """Command for '/team create'

        Creates a team and assigns the user as owner.
        """
        # Since we have to call the database a few times, defer this command...
        await interaction.response.defer(ephemeral=True, thinking=True)

        member: asyncpg.Record = await self.bot.database.fetch_member(member_id=interaction.user.id)
        if interaction.user.get_role(MANAGER_ID) and not member:
            await interaction.followup.send('You are unable to create a team until you register.', ephemeral=True)
            return

        if member['team_id']:
            message: str = 'You can not create a team because you are already in one. Please use `/team leave` first.'

            await interaction.followup.send(message, ephemeral=True)
            return

        payload: CTeamPayload = await self.create_team_(interaction=interaction, name=name, owner=interaction.user)

        message: str = f'{payload["role"].mention}\n' \
                       f'Successfully created the team: `{name}`\n\n' \
                       f'**Channels:**\n' \
                       f'{payload["text"].mention}\n' \
                       f'{payload["voice"].mention}\n\n' \
                       f'**Role:**\n' \
                       f'{payload["role"].mention}\n\n' \
                       f'**People can join this team via:**\n' \
                       f'`/team join {payload["team"]["invite"]}`\n' \
                       f'Send a Private Message with this command to the member(s) for use in this server.\n\n' \
                       f'**Useful commands:**\n' \
                       f'`/team invite` - Get your team invite code.\n' \
                       f'`/team leave` - Leave this team.\n\n' \
                       f'Please note there are very strict rate limits on creating and leaving teams.'

        # Send this message to the newly created team channel...
        # Pin the message...
        response: discord.Message = await payload['text'].send(message)
        await response.pin(reason=f'CodeJam Team Creation: ({interaction.user})')

        # We need to send this in order for the command to know it's done...
        await interaction.followup.send('Successfully created team!', ephemeral=True)

        await update_backend(self.bot)

    @group.command(name='leave', description='Leave your current CodeJam team')
    @app_commands.checks.cooldown(1, 60 * 60)
    async def leave_team(self, interaction: discord.Interaction) -> None:
        """Command for '/team leave'

        Leaves your current team. If you are the only remaining member, the team is deleted.
        """
        # Since we have to call the database a few times, defer this command...
        await interaction.response.defer(ephemeral=True, thinking=True)

        member: asyncpg.Record = await self.bot.database.fetch_member(member_id=interaction.user.id)
        if interaction.user.get_role(MANAGER_ID) and not member:
            await interaction.followup.send('You are unable to leave a team until you register.', ephemeral=True)
            return

        if not member['team_id']:
            message: str = 'You can not leave a team because you are not already in one.'

            await interaction.followup.send(message, ephemeral=True)
            return

        team_members: list[asyncpg.Record] = await self.bot.database.fetch_team(team_id=member['team_id'])
        team: asyncpg.Record = team_members[0]

        if len(team_members) == 1:
            role: discord.Role = interaction.guild.get_role(team['role_id'])
            text: discord.TextChannel = interaction.guild.get_channel(team['text_id'])
            voice: discord.VoiceChannel = interaction.guild.get_channel(team['voice_id'])

            # Delete the team from the database...
            await self.bot.database.delete_team(team_id=team['team_id'])

            # Delete all associated channels and roles with the team...
            reason: str = f'CodeJam Team Deletion: ({interaction.user})'
            await role.delete(reason=reason)
            await text.delete(reason=reason)
            await voice.delete(reason=reason)

            try:
                await interaction.followup.send(f'Successfully left the team: `{team["name"]}`')
            except discord.HTTPException:
                pass

            await update_backend(self.bot)

            return

        if interaction.user.id == team_members[0]['owner']:
            # Assign a new team owner...
            new: int = [m['member_id'] for m in team_members if m['member_id'] != interaction.user.id][0]
            await self.bot.database.edit_team_owner(member_id=new, team_id=member['team_id'])

        # Get role and remove it...
        role: discord.Role = interaction.guild.get_role(team['role_id'])
        await interaction.user.remove_roles(role, reason=f'CodeJam Team Leave: ({interaction.user})')

        # Remove team from this member...
        await self.bot.database.edit_member_team(member_id=interaction.user.id, team_id=None)

        channel: discord.TextChannel = interaction.guild.get_channel(team['text_id'])
        await channel.send(f'{interaction.user.mention} just left the team.')

        try:
            await interaction.followup.send(f'Successfully left the team: `{team["name"]}`')
        except discord.HTTPException:
            pass

        await update_backend(self.bot)

    @group.command(name='join', description='Join a CodeJam team with an invite code')
    @app_commands.checks.cooldown(3, 60 * 10)
    async def join_team(self, interaction: discord.Interaction, *, code: str) -> None:
        """Command for '/team join'

        Joins the team the unique 'code' belongs to.
        """
        # Since we need to call the database a few times we should defer this command...
        await interaction.response.defer(ephemeral=True, thinking=True)

        member: asyncpg.Record = await self.bot.database.fetch_member(member_id=interaction.user.id)
        if interaction.user.get_role(MANAGER_ID) and not member:
            await interaction.followup.send('You are unable to join a team until you register.')
            return

        if member['team_id']:
            message: str = 'You can not join a team because you are already in one. Please use `/team leave` first.'
            await interaction.followup.send(message, ephemeral=True)
            return

        team: list[asyncpg.Record] = await self.bot.database.fetch_team(invite=code)
        if not team:
            message: str = f'The code: `{code}` is invalid or does not match any current team.'
            await interaction.followup.send(message, ephemeral=True)
            return

        # Update the database...
        team: asyncpg.Record = team[0]
        await self.bot.database.edit_member_team(member_id=interaction.user.id, team_id=team['team_id'])

        # Give the team role to our new team member, so they can see channels etc...
        role: discord.Role = interaction.guild.get_role(team['role_id'])
        await interaction.user.add_roles(role, reason=f'CodeJam Team Joined: ({interaction.user})')

        # Channels for mentioning...
        text: discord.TextChannel = interaction.guild.get_channel(team['text_id'])
        voice: discord.VoiceChannel = interaction.guild.get_channel(team['voice_id'])

        message: str = f'Successfully joined the team: `{team["name"]}`\n\n**Channels:**\n{text.mention}\n{voice.mention}'
        await interaction.followup.send(message, ephemeral=True)

        await text.send(f'{interaction.user.mention} has just joined the team.', silent=True)

        await update_backend(self.bot)

    @group.command(name='invite', description='Generate an invite for someone to join your team')
    async def invite(self, interaction: discord.Interaction) -> None:
        """Command for '/team invite'

        Sends a unique invite code for another user to use.
        """
        team: list[asyncpg.Record] = await self.fetch_team_by_member_or_channel(interaction)

        if team:
            invite: str = team[0]['invite']
            msg: str = f'Your team invite code is: `{invite}`\n\nParticipants can use `/team join {invite}` to join.\n' \
                       'Send a Private Message with this command to the member(s) for use in this server.\n\n'

            await interaction.response.send_message(msg, ephemeral=True)
            return

        # No team was found if we reach here...
        advice: str = ''
        if interaction.user.get_role(MANAGER_ID):
            advice = '**Managers please use this command in the appropriate team channel.**'

        message: str = f'You can not invite someone without being in a team. {advice}'
        await interaction.response.send_message(message, ephemeral=True)

    """ 
    @group.command(name='delete', description='Remove your team from the CodeJam')
    @app_commands.checks.dynamic_cooldown(factory=manager_cooldown_bypass, key=lambda i: i.user.id)
    @is_team_owner_or_manager()
    async def delete_team(self, interaction: discord.Interaction) -> None:
        \"""Command for '/team delete'

        Allows a team owner or CodeJam manager to delete their/a team.
        \"""
        # Since we need to call the database a few times we should defer this command...
        await interaction.response.defer(ephemeral=True, thinking=True)

        team: list[asyncpg.Record] = await self.fetch_team_by_member_or_channel(interaction)

        if not team:
            message: str = 'Please use this command in the team channel that you want to delete.'
            await interaction.followup.send(message, ephemeral=True)

            return

        # We need to gather all discord members of this team, so we can mention them in a channel...
        members: list[discord.Member] = [interaction.guild.get_member(t['member_id']) for t in team]
        team: asyncpg.Record = team[0]

        role: discord.Role = interaction.guild.get_role(team['role_id'])
        text: discord.TextChannel = interaction.guild.get_channel(team['text_id'])
        voice: discord.VoiceChannel = interaction.guild.get_channel(team['voice_id'])

        # Delete the team from the database...
        await self.bot.database.delete_team(team_id=team['team_id'])

        # Delete all associated channels and roles with the team...
        reason: str = f'CodeJam Team Deletion: ({interaction.user})'
        await role.delete(reason=reason)
        await text.delete(reason=reason)
        await voice.delete(reason=reason)

        # The team announcements channel...
        channel: discord.TextChannel = interaction.guild.get_channel(TEAM_ANNOUNCEMENTS_CHANNEL)
        mentions: str = ', '.join(m.mention for m in members)

        # Send an announcement to the team members...
        message: str = f'{mentions}\n\nYour team: **`{team["name"]}`** was deleted. You can now join another team.'
        await channel.send(message)

        try:
            message: str = f'Your team: **`{team["name"]}`** was deleted. You can now join another team.'
            await interaction.followup.send(message)
        except discord.NotFound:
            pass
    """

    """
    @group.command(name='name', description='Change your teams name')
    @app_commands.checks.dynamic_cooldown(factory=manager_cooldown_bypass, key=lambda i: i.user.id)
    @name_validator()
    @is_team_owner_or_manager()
    async def change_name(self, interaction: discord.Interaction, *, name: str) -> None:
        \"""Command for '/team name'

        Allows a team owner or CodeJam manager to change a teams name.
        \"""
        # This may take more than 3 seconds to complete since we need to
        # Edit role and channels and make a few database calls...
        # So we need to defer...
        await interaction.response.defer(ephemeral=True, thinking=True)

        # This bit is a little tricky...
        # Cause if a CodeJam manager uses this command we don't actually know the Team they are referring to...
        # So the ony way to validate this is if the manager uses the command in the channel of the team...
        team: list[asyncpg.Record] = await self.fetch_team_by_member_or_channel(interaction)

        if not team:
            message: str = 'Please use this command in the team channel that you want to change the name of.'
            await interaction.followup.send(message, ephemeral=True)

            return

        owner: discord.Member = interaction.guild.get_member(team[0]['owner'])

        await self.change_name_(interaction=interaction, name=name, owner=owner)
        await interaction.followup.send(f'Your team name was changed to `{name}` successfully.', ephemeral=True)
    """

    @app_commands.command(name='error', description='Fetch an error from the Error Log.')
    @is_manager()
    async def fetch_error(self, interaction: discord.Interaction, *, identifier: int) -> None:
        """Command for '/error'

        Allows a CodeJam manager to view an error that has occurred on the bot.
        """
        log: asyncpg.Record = await self.bot.database.fetch_log(identifier)

        if not log:
            await interaction.response.send_message(f'No error with id: `{identifier}` could be found.', ephemeral=True)
            return

        invoker: discord.Member = interaction.guild.get_member(log['invoker'])
        channel: discord.TextChannel | discord.VoiceChannel = interaction.guild.get_channel(log['channel'])
        tb: str = log['traceback'].replace('```', '')
        timestamp: str = discord.utils.format_dt(log['created'], style='F')

        embed: discord.Embed = discord.Embed(colour=0xDC3545)
        embed.title = f'{log["error"]} in {log["command"]}'
        embed.description = f'```ansi\n\u001b[0;31m{tb}\n```'

        if invoker:
            embed.set_author(name=str(invoker), icon_url=invoker.display_avatar.url)

        embed.add_field(name='Channel', value=channel.mention)
        embed.add_field(name='Timestamp', value=timestamp)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command()
    @commands.is_owner()
    async def send_signup(self, ctx: commands.Context) -> None:
        channel: discord.TextChannel = ctx.guild.get_channel(SIGNUP_CHANNEL)

        with open('./resources/signup_message.txt', 'r', encoding='UTF-8') as fp:
            desc: str = fp.read()

        embed = discord.Embed(colour=0xF0B7B1)
        embed.title = "TimeEnjoyed CodeJam!"
        embed.description = desc

        embed.add_field(name='Website', value='[Home](https://codejam.timeenjoyed.dev)\n'
                                              '[Live Member Feed](https://codejam.timeenjoyed.dev/participants)'
                        )

        embed.set_thumbnail(url=ctx.guild.icon.url)
        view = SignupView()

        message: discord.Message = await channel.send(embed=embed, view=view)

        self.bot.add_view(view, message_id=message.id)
        await ctx.send(f'Your message ID: `{message.id}`')


async def setup(bot: Bot) -> None:
    await bot.add_cog(Signup(bot=bot))
