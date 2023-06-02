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
from typing import Any


__all__ = ('languages', 'timezones', 'preferences')


languages: dict[int, dict[str, Any]] = {
    0: {'name': 'No Preference', 'emoji': '<:greentick:1113364121317023744>', 'value': 0},
    1: {'name': 'Python', 'emoji': '<:python:1113257855370403940>', 'value': 1},
    2: {'name': 'JavaScript', 'emoji': '<:js:1113256440036085770>', 'value': 2},
    3: {'name': 'TypeScript', 'emoji': '<:ts:1113322608352559134>', 'value': 3},
    4: {'name': 'Java', 'emoji': '<:java:1113322368996233256>', 'value': 4},
    5: {'name': 'Kotlin', 'emoji': '<:kotlin:1113259409641050264>', 'value': 5},
    6: {'name': 'C++', 'emoji': '<:cpp:1113256431844610078>', 'value': 6},
    7: {'name': 'C', 'emoji': '<:clang:1113256428879224852>', 'value': 7},
    8: {'name': 'C#', 'emoji': '<:csharp:1113256434973556789>', 'value': 8},
    9: {'name': 'Rust', 'emoji': '<:rust:1113259416511316078>', 'value': 9},
    10: {'name': 'Go', 'emoji': '<:go:1113266355190382614>', 'value': 10},
    11: {'name': 'Swift', 'emoji': '<:swift:1113256442024173649>', 'value': 11},
    12: {'name': 'Bash/Shell', 'emoji': '<:bash:1113256426341670954>', 'value': 12},
    13: {'name': 'Lua', 'emoji': '<:lua:1113259412853895179>', 'value': 13},
    14: {'name': 'VisualBasic', 'emoji': '<:visualbasic:1113257858168008714>', 'value': 14},
    15: {'name': 'Haskell', 'emoji': '<:haskell:1113257852996419695>', 'value': 15},
    16: {'name': 'Dart', 'emoji': '<:dart:1113259404326883429>', 'value': 16},
    17: {'name': 'PHP', 'emoji': '<:php:1113322436193157130>', 'value': 17},
    18: {'name': 'Other...', 'emoji': '<:greentick:1113364121317023744>', 'value': 18},
}

timezones: dict[int, dict[str, Any]] = {
    0: {'name': 'UTC-12', 'delta': datetime.timedelta(hours=-12), 'emoji': None, 'value': 0},
    1: {'name': 'UTC-11', 'delta': datetime.timedelta(hours=-11), 'emoji': None, 'value': 1},
    2: {'name': 'UTC-10', 'delta': datetime.timedelta(hours=-10), 'emoji': None, 'value': 2},
    3: {'name': 'UTC-9', 'delta': datetime.timedelta(hours=-9), 'emoji': None, 'value': 3},
    4: {'name': 'UTC-8', 'delta': datetime.timedelta(hours=-8), 'emoji': None, 'value': 4},
    5: {'name': 'UTC-7', 'delta': datetime.timedelta(hours=-7), 'emoji': None, 'value': 5},
    6: {'name': 'UTC-6', 'delta': datetime.timedelta(hours=-6), 'emoji': None, 'value': 6},
    7: {'name': 'UTC-5', 'delta': datetime.timedelta(hours=-5), 'emoji': None, 'value': 7},
    8: {'name': 'UTC-4', 'delta': datetime.timedelta(hours=-4), 'emoji': None, 'value': 8},
    9: {'name': 'UTC-3', 'delta': datetime.timedelta(hours=-3), 'emoji': None, 'value': 9},
    10: {'name': 'UTC-2', 'delta': datetime.timedelta(hours=-2), 'emoji': None, 'value': 10},
    11: {'name': 'UTC-1', 'delta': datetime.timedelta(hours=-1), 'emoji': None, 'value': 11},
    12: {'name': 'UTC+0', 'delta': datetime.timedelta(hours=0), 'emoji': None, 'value': 12},
    13: {'name': 'UTC+1', 'delta': datetime.timedelta(hours=1), 'emoji': None, 'value': 13},
    14: {'name': 'UTC+2', 'delta': datetime.timedelta(hours=2), 'emoji': None, 'value': 14},
    15: {'name': 'UTC+3', 'delta': datetime.timedelta(hours=3), 'emoji': None, 'value': 15},
    16: {'name': 'UTC+4', 'delta': datetime.timedelta(hours=4), 'emoji': None, 'value': 16},
    17: {'name': 'UTC+5', 'delta': datetime.timedelta(hours=5), 'emoji': None, 'value': 17},
    18: {'name': 'UTC+6', 'delta': datetime.timedelta(hours=6), 'emoji': None, 'value': 18},
    19: {'name': 'UTC+7', 'delta': datetime.timedelta(hours=7), 'emoji': None, 'value': 19},
    20: {'name': 'UTC+8', 'delta': datetime.timedelta(hours=8), 'emoji': None, 'value': 20},
    21: {'name': 'UTC+9', 'delta': datetime.timedelta(hours=9), 'emoji': None, 'value': 21},
    22: {'name': 'UTC+10', 'delta': datetime.timedelta(hours=10), 'emoji': None, 'value': 22},
    23: {'name': 'UTC+11', 'delta': datetime.timedelta(hours=11), 'emoji': None, 'value': 23},
    24: {'name': 'UTC+12', 'delta': datetime.timedelta(hours=12), 'emoji': None, 'value': 24},
}


preferences: dict[int, dict[str, Any]] = {
    0: {'name': 'Solo', 'bool': True, 'emoji': None, 'value': 0},
    1: {'name': 'Open to Teams', 'bool': False, 'emoji': None, 'value': 1}
}
