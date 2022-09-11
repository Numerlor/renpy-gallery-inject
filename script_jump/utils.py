# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

from __future__ import unicode_literals

import functools
import re
import sys
import typing as t
from functools import partial

import pygame.scrap
import renpy
from renpy.defaultstore import NoRollback

import script_jump

if t.TYPE_CHECKING:
    import collections.abc
    from typing_extensions import ParamSpec
    from .execution_tracing import NodePathLog

    P = ParamSpec("P")

__all__ = [
    "NodeWrapper",
    "NoRollbackValue",
    "LogWrapper",
    "cache",
    "dict_values",
    "removeprefix",
    "script_file_contents",
    "elide",
    "escape_renpy_formatting",
    "get_node_find_string",
    "set_clipboard",
]

T = t.TypeVar("T")


class NoRollbackValue(NoRollback, t.Generic[T]):
    """Wrap `value` to not participate in rollback."""
    def __init__(self, value):
        # type: (T) -> None
        self.value = value


_NodeT = t.TypeVar("_NodeT", bound=renpy.ast.Node)


class NodeWrapper(t.Generic[_NodeT]):
    """
    Wrap a renpy ast node.

    The wrapper allows NodePathLogs to be created from its children,
    and provides a string representation with its line from the file.
    """
    __slots__ = ("node", "_line", "label_name", "previous_wrapper")

    def __init__(self, node, previous_wrapper, label_name):
        # type: (_NodeT, "NodeWrapper | None", t.Text | None) -> None
        self.node = node
        self.label_name = label_name
        self.previous_wrapper = previous_wrapper
        self._line = None

    def __str__(self):
        return "{:<15} {}".format(type(self.node).__name__, self.line_string)

    def __repr__(self):
        return "<NodeWrapper type(node)={} node.filename={!r} node.linenumber={!r} label={!r}>".format(
            type(self.node).__qualname__,
            self.node.filename,
            self.node.linenumber,
            self.label_name,
        )

    @property
    def line_string(self):
        """The first line of code necessary to create the node this wraps."""
        if self._line is None:
            if self.node.filename.endswith(".rpyc"):
                line_text = script_jump.ast_unparse.node_text(self)
            else:
                line_text = script_file_contents(self.node.filename)[self.node.linenumber - 1].strip()
            self._line = elide(line_text, 25)
        return self._line


class LogWrapper(object):
    """Wrap a `NodePathLog` and the parent log it came from."""

    def __init__(self, parent, log):
        # type: (NodePathLog | None, NodePathLog) -> None
        self.parent = parent
        self.log = log
        self.page_index = 0

    @property
    def current_page(self):
        # type: () -> tuple[NodeWrapper, ...]
        """Get the tuple of the current page."""
        return self.log.paged_nodes[self.page_index]


_KEYWORD_SEP_SENTINEL = object()


def cache(func):
    # type: (collections.abc.Callable[P, T]) -> collections.abc.Callable[P, T]
    """Cache results of `func`."""
    cache_dict = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # type: (P.args, P.kwargs) -> T
        cache_key = (args, _KEYWORD_SEP_SENTINEL, *kwargs.items())
        try:
            return cache_dict[cache_key]
        except KeyError:
            cache_dict[cache_key] = ret_val = func(*args, **kwargs)
            return ret_val

    return wrapper


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


@cache
def script_file_contents(filename):
    # type: (t.Text) -> list[t.Text]
    """
    Get a list of all lines in `filename`.

    Return values are cached.
    """
    filename = removeprefix(filename, "game/")
    with renpy.loader.load(filename) as file:
        return file.read().decode(errors="surrogateescape").splitlines(True)


def elide(string, length):
    # type: (t.Text, int) -> t.Text
    """Elide `string` to be `length` characters. An ellipsis is suffixed if the string is shortened."""
    if len(string) > length:
        return string[:length - 1] + u"\N{HORIZONTAL ELLIPSIS}"
    return string


def set_clipboard(text):
    # type: (t.Text) -> None
    """Copy `text` into the clipboard."""
    pygame.scrap.put(pygame.scrap.SCRAP_TEXT, text.encode())


def _sub_brackets_with_escaped(match):
    # type: (re.Match) -> t.Text
    """Double up every bracket/brace matched by `match`."""
    return match.group(0) * 2


escape_renpy_formatting = partial(re.compile(r"\{+|\[+").sub, _sub_brackets_with_escaped)


def _scene_template(__wrapped_node):
    # type: (NodeWrapper[renpy.ast.Scene]) -> t.Text
    return (
        "find_scene(find_label({wrapped_node.label_name!r}), name={joined_name!r}, layer={wrapped_node.node.layer!r})"
    ).format(
        joined_name=" ".join(__wrapped_node.node.imspec[0]),
        wrapped_node=__wrapped_node,
    )


def _show_template(__wrapped_node):
    # type: (NodeWrapper[renpy.ast.Show]) -> t.Text
    return "find_show(find_label({wrapped_node.label_name!r}), {joined_name!r})".format(
        joined_name=" ".join(__wrapped_node.node.imspec[0]),
        wrapped_node=__wrapped_node,
    )


def _user_statement_template(__wrapped_node):
    # type: (NodeWrapper[renpy.ast.UserStatement]) -> t.Text
    return (
        "find_user_statement(find_label({wrapped_node.label_name!r}), {joined_name!r}, {wrapped_node.node.parsed})"
    ).format(
        joined_name=" ".join(__wrapped_node.node.parsed[0]),
        wrapped_node=__wrapped_node,
    )


def get_node_find_string(wrapped_node):
    # type: (NodeWrapper) -> t.Text | None
    """Get the string to find node in `wrapped_node`."""
    template = _node_find_templates.get(type(wrapped_node.node))
    if template is None:
        return None
    return template(wrapped_node)


# dict[type[T], t.Callable[[NodeWrapper[T]], t.Text]]
_node_find_templates = {
    renpy.ast.Say: "find_say(find_label({0.label_name!r}), what={0.node.what!r}, who={0.node.who!r})".format,
    renpy.ast.Label: "find_label({0.node.name!r})".format,
    renpy.ast.Jump: "find_jump(find_label({0.label_name!r}), {0.node.target!r})".format,
    renpy.ast.Return: "find_return(find_label({0.label_name!r}))".format,
    renpy.ast.Menu: "find_menu(find_label({0.label_name!r}))".format,
    renpy.ast.Python: "find_code(find_label({0.label_name!r}), {{}})".format,
    renpy.ast.Call: "find_call(find_label({0.label_name!r}), {0.node.label!r})".format,
    renpy.ast.Scene: _scene_template,
    renpy.ast.Show: _show_template,
    renpy.ast.UserStatement: _user_statement_template,
}
