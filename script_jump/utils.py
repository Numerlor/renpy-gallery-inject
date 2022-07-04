# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

import re
import sys
import typing as t
from functools import partial

import renpy
from renpy.defaultstore import NoRollback

if t.TYPE_CHECKING:
    from .execution_tracing import NodePathLog

__all__ = [
    "NoRollbackValue",
    "LogWrapper",
    "dict_values",
    "removeprefix",
    "script_file_contents",
    "elide",
    "escape_renpy_formatting",
]

T = t.TypeVar("T")


class NoRollbackValue(NoRollback, t.Generic[T]):
    """Wrap `value` to not participate in rollback."""
    def __init__(self, value):
        # type: (T) -> None
        self.value = value


class LogWrapper:
    """Wrap a `NodePathLog` and the parent log it came from."""

    def __init__(self, parent, log):
        # type: (NodePathLog | None, NodePathLog) -> None
        self.parent = parent
        self.log = log


def dict_values(dict_):
    # type: (dict) -> t.ValuesView
    """Get the values view of `dict_`."""
    if sys.version_info.major == 3:
        return dict_.values()
    else:
        return dict_.viewvalues()


def removeprefix(__string, __prefix):
    # type: (t.Text, t.Text) -> t.Text
    """Remove prefix from the given string."""
    if __string.startswith(__prefix):
        return __string[len(__prefix):]

    return __string


_script_cache = {}


def script_file_contents(filename):
    # type: (t.Text) -> list[t.Text]
    """
    Get a list of all lines in `filename`.

    Return values are cached.
    """
    filename = removeprefix(filename, "game/")
    lines = _script_cache.get(filename)
    if lines is None:
        with renpy.exports.open_file(filename, encoding="utf8") as file:
            lines = _script_cache[filename] = file.readlines()

    return lines


def elide(string, length):
    # type: (t.Text, int) -> t.Text
    """Elide `string` to be `length` characters. An ellipsis is suffixed if the string is shortened."""
    if len(string) > length:
        return string[:length - 1] + u"\N{HORIZONTAL ELLIPSIS}"
    return string


def _sub_brackets_with_escaped(match):
    # type: (re.Match) -> t.Text
    """Double up every bracket/brace matched by `match`."""
    return match.group(0) * 2


escape_renpy_formatting = partial(re.compile(r"\{+|\[+").sub, _sub_brackets_with_escaped)