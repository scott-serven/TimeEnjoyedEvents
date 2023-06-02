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
from discord.app_commands import CheckFailure


__all__ = (
    'NotRegisteredError',
    'NotManagerError',
    'NotTeamOwnerError',
    'AlreadyRegisteredError',
    'NameViolationError'
)


class NotRegisteredError(CheckFailure):
    """Exception raised when a user tries to use a CodeJam command when not registered."""
    pass


class NotManagerError(CheckFailure):
    """Exception raised when a user tries to use a CodeJam command that is Manager restricted."""
    pass


class NotTeamOwnerError(CheckFailure):
    """Exception raised when a user tries to use a CodeJam command that is Team Owner restricted."""
    pass


class AlreadyRegisteredError(CheckFailure):
    """Exception raised when a user tires to register when already registered."""
    pass


class NameViolationError(CheckFailure):
    """Exception raised when team name validation fails."""

    def __init__(self, message: str):
        self.message = message
