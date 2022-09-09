# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

from __future__ import unicode_literals

import functools
import typing as t
from collections import OrderedDict

import renpy

from gallery import grouper
from script_jump.utils import dict_values, NodeWrapper
from script_jump.attribute_change_notifier import AttributeChangeNotifier

if t.TYPE_CHECKING:
    import collections.abc
    from typing_extensions import ParamSpec
    T = t.TypeVar("T")
    P = ParamSpec("P")

__all__ = [
    "patch_context_notifier",
    "NodeWrapper",
    "NodePathLog",
]

_new_node_notifier = None  # type: AttributeChangeNotifier | None

NODE_PAGE_SIZE = 500


def _cache(func):
    # type: (collections.abc.Callable[P, T]) -> collections.abc.Callable[P, T]
    """
    Cache results of `func` with the passed positional arguments.

    kwargs are ignored.
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # type: (P.args, P.kwargs) -> T
        try:
            return cache[args]
        except KeyError:
            cache[args] = ret_val = func(*args)
            return ret_val

    return wrapper


def patch_context_notifier():
    # type: () -> None
    """Patch in Context's current variable to the ChangeNotify descriptor."""
    global _new_node_notifier
    renpy.execution.Context.current = _new_node_notifier = AttributeChangeNotifier("current")


def node_forkable(wrapped_node):
    # type: (NodeWrapper) -> bool
    """True if the wrapped node can be forked into child logs, False otherwise."""
    return isinstance(wrapped_node.node, (renpy.ast.Menu, renpy.ast.If, renpy.ast.While))


@_cache
def forked_child_logs(wrapped_node):
    # type: (NodeWrapper) -> list[NodePathLog]
    """
    The child logs under this node.

    The logs are cached after the first access.
    """
    if isinstance(wrapped_node.node, renpy.ast.Menu):
        return [
            NodePathLog(branch_nodes[0])
            for (_, _, branch_nodes) in wrapped_node.node.items if branch_nodes is not None
        ]
    elif isinstance(wrapped_node.node, renpy.ast.If):
        return [
            NodePathLog(branch_nodes[0])
            for (_, branch_nodes) in wrapped_node.node.entries if branch_nodes is not None
        ]
    elif isinstance(wrapped_node.node, renpy.ast.While):
        # not a fork but creates a child
        return [NodePathLog(wrapped_node.node.block[0])]
    else:
        raise RuntimeError("Node of type {!r} has no children.", type(wrapped_node.node).__name__)


class NodePathLog(object):
    """
    Keeps track of execution starting from `node`.

    Static jumps and calls are resolved and seen as a part of its execution path.
    """

    def __init__(self, start_node):
        # type: (renpy.ast.Node) -> None
        assert _new_node_notifier is not None
        _new_node_notifier.add_callback(self.update_from_new_node)

        self._nodes = OrderedDict()
        self._paged_nodes = None
        self.current_node = None
        self._populate_nodes(start_node)

    @property
    def nodes(self):
        # type: () -> t.ValuesView[NodeWrapper]
        """Get a dict view of the wrapped nodes in this log."""
        return dict_values(self._nodes)

    @property
    def paged_nodes(self):
        # type: () -> tuple[tuple[NodeWrapper, ...], ...]
        """Nodes paged into tuples of `NODE_PAGE_SIZE` elements, last tuple may be smaller."""
        if self._paged_nodes is None:
            self._paged_nodes = grouper(self.nodes, NODE_PAGE_SIZE)
        return self._paged_nodes

    def update_from_new_node(self, node_name):
        # type: (t.Text) -> None
        """Change the current index to point to the node with the name `node_name`, if it is in this execution path."""
        renpy_node = renpy.game.script.namemap.get(node_name)
        if renpy_node is not None and not renpy_node.filename.startswith("patched"):
            wrapped_node = self._nodes.get(renpy_node)
            if wrapped_node is not None:
                self.current_node = wrapped_node

    def has_node(self, node):
        # type: (renpy.ast.Node) -> bool
        """Return True if the passed in node is a node in this path, False otherwise."""
        return node in self._nodes

    def _populate_nodes(self, start_node):
        # type: (renpy.ast.Node) -> None
        """Populate `self._nodes` with all the nodes directly reachable from `start_node`."""
        node = start_node
        call_stack = []
        current_label_name = None
        previous_wrapper = None

        while True:
            if (
                isinstance(node, (renpy.ast.Translate, renpy.ast.EndTranslate, renpy.ast.Init))
                or node.filename.startswith("patched")
            ):
                node = node.next
                continue

            if isinstance(node, renpy.ast.Label):
                current_label_name = node.name

            self._nodes[node] = previous_wrapper = NodeWrapper(node, previous_wrapper, current_label_name)

            if isinstance(node, renpy.ast.Call) and not node.expression:
                call_stack.append((node, current_label_name))
                node = renpy.game.script.lookup(node.label)

            elif node.next is not None:
                node = node.next

            elif isinstance(node, renpy.ast.Jump) and not node.expression:
                node = renpy.game.script.lookup(node.target)

            elif call_stack:
                saved_node, current_label_name = call_stack.pop()
                node = saved_node.next

            else:
                break
