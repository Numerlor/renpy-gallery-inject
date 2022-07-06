# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

from __future__ import unicode_literals

import copy
import difflib
from collections import deque, namedtuple
import typing as t

import renpy.ast
import renpy.game
from renpy.sl2 import slast

if t.TYPE_CHECKING:
    import typing_extensions as te
    P = te.ParamSpec("P")
    T = t.TypeVar("T")

ANY_LABEL = object()
_MISSING = object()

NodeWrapper = namedtuple("NodeWrapper", ["node", "parent", "pos_in_parent"])

__all__ = [
    "ANY_LABEL",
    "NodeWrapper",
    "walk_sl_ast",
    "walk_ast",
    "find_call",
    "find_say",
    "find_label",
    "find_code",
    "find_jump",
    "find_scene",
    "find_show",
    "find_user_statement",
    "find_return",
    "find_menu",
    "patch_after_node",
    "mark_node_patched",
    "create_artificial_label",
    "create_end_replay_node",
    "get_nth_after",
]


def walk_sl_ast(wrapped_top_node):
    # type: (NodeWrapper) -> t.Iterator[NodeWrapper]
    """
    Yield all the child block nodes from the node in `wrapped_top_node`.

    In case an SLIf or SLShowIf node is found, their parent is the if's parent instead of the if itself.
    """
    todo = deque([wrapped_top_node])

    while todo:
        wrapped_node = todo.popleft()
        if isinstance(wrapped_node.node, (slast.SLIf, slast.SLShowIf)):
            # for ifs, yield the if node, but directly attribute its branch blocks to the parent node
            for _, block in wrapped_node.node.entries:
                wrapped_block = NodeWrapper(
                    block, wrapped_node.parent, wrapped_node.pos_in_parent
                )
                todo.extend(
                    NodeWrapper(child, wrapped_block, pos)
                    for pos, child in enumerate(block.children)
                )
            yield wrapped_node

        elif isinstance(wrapped_node.node, slast.SLBlock):
            todo.extend(
                NodeWrapper(child, wrapped_node, pos)
                for pos, child in enumerate(wrapped_node.node.children)
            )
            yield wrapped_node


def walk_ast(node):
    # type: (renpy.ast.Node) -> list[renpy.ast.Node]
    """Return list containing all nodes after `node`."""
    flattened_tree = []
    seen = set()

    def add_node(node):
        flattened_tree.append(node)
        seen.add(node)

    # Jumping into the middle of the ast, and our patches that don't go into blocks properly
    # requires us to keep track of all the nodes to prevent duplicates and going over each node individually.
    while node is not None:
        node.get_children(add_node)
        while node in seen:
            node = node.next
    return flattened_tree


def _find_node(type_, predicate, start_node, return_previous):
    # type: (type[T], t.Callable, renpy.ast.Node, bool) -> T | None
    """
    Find the node of `type_` for which predicate returns True, if return_previous is true, return the node before.

    If nodes to try is ANY_LABEL, try to find the node under all labels.
    """
    if start_node is ANY_LABEL:
        nodes_to_try = [node for node in renpy.game.script.namemap.values() if isinstance(node, renpy.ast.Label)]
    else:
        nodes_to_try = [start_node]

    for start_node in nodes_to_try:
        previous_node = None
        for node in walk_ast(start_node):
            if isinstance(node, type_) and predicate(node):
                if return_previous:
                    return previous_node
                return node
            previous_node = node
    else:
        return None


def _cache_node_find(
        func  # type: t.Callable[te.Concatenate[renpy.ast.Node | object, P], T]
):  # type: (...) -> t.Callable[te.Concatenate[renpy.ast.Node | object, P], T]
    """Cache a find function's result in persistent."""
    def wrapper(start_node, *args, **kwargs):
        # type: (renpy.ast.Node | object, P.args, P.kwargs) -> T

        hashable_args = _transform_args_to_hashable(args)
        hashable_kwargs = _transform_kwargs_to_hashable(kwargs)
        cache = renpy.game.persistent.node_cache_
        start_node_name = start_node.name if start_node is not ANY_LABEL else None

        if cache is None:
            renpy.game.persistent.node_cache_ = cache = {}
        else:
            cached_name = cache.get((start_node_name, hashable_args, hashable_kwargs))
            if cached_name is not None:
                cached_node = renpy.game.script.namemap.get(cached_name)
                if cached_node is not None:
                    return cached_node

        found_node = func(start_node, *args, **kwargs)
        if found_node is not None:
            cache[(start_node_name, hashable_args, hashable_kwargs)] = found_node.name
        return found_node

    return wrapper


def find_label(label_name):
    # type: (t.Text) -> renpy.ast.Label
    """Return the label with the `label_name` name."""
    return renpy.game.script.lookup(label_name)


@_cache_node_find
def find_call(start_node, target, return_previous=False):
    # type: (renpy.ast.Node, t.Text, bool) -> renpy.ast.Call | None
    """Return the label with the `label_name` name."""

    def predicate(node):
        return node.label == target

    return _find_node(renpy.ast.Call, predicate, start_node, return_previous)


@_cache_node_find
def find_say(start_node, what=None, who=None, return_previous=False):
    # type: (renpy.ast.Node, t.Text | None, t.Text | None, bool) -> renpy.ast.Say | None
    """
    Find the next say node where the sayer `who` says `what`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        who_match = who is None or who == node.who
        what_match = (
                what is None
                or difflib.SequenceMatcher(None, what, node.what).ratio() > 0.7
        )
        return who_match and what_match

    return _find_node(renpy.ast.Say, predicate, start_node, return_previous)


@_cache_node_find
def find_code(start_node, var_names, return_previous=False):
    # type: (renpy.ast.Node, set, bool) -> renpy.ast.Python | None
    """
    Find the code node with `var_names` after `start_node`, the first matching node is returned.

    `var_names` may contain names of variables and attributes any code constants,
    if any of them is in the code, the node is seen as equal to the search.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        code = node.code.bytecode
        return bool(var_names.intersection(code.co_varnames + code.co_names + code.co_consts))

    return _find_node(renpy.ast.Python, predicate, start_node, return_previous)


@_cache_node_find
def find_jump(start_node, label_name, return_previous=False):
    # type: (renpy.ast.Node, t.Text, bool) -> renpy.ast.Jump | None
    """
    Find the next jump node that jumps to `label_name` after `start_node`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return node.target == label_name

    return _find_node(renpy.ast.Jump, predicate, start_node, return_previous)


@_cache_node_find
def find_scene(start_node, name=None, layer=None, return_previous=False):
    # type: (renpy.ast.Node, t.Text | None, t.Text | None, bool) -> renpy.ast.Scene | None
    """
    Find the next scene node showing `name` at `layer` after `start_node`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return (
                (layer is None or node.layer == layer)
                and (name is None or (node.imspec is not None and " ".join(node.imspec[0]) == name))
        )

    return _find_node(renpy.ast.Scene, predicate, start_node, return_previous)


@_cache_node_find
def find_show(start_node, name, return_previous=False):
    # type: (renpy.ast.Node, t.Text, bool) -> renpy.ast.Show | None
    """
    Find the next show statement showing `name` after `start_node`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return node.imspec is not None and " ".join(node.imspec[0]) == name

    return _find_node(renpy.ast.Show, predicate, start_node, return_previous)


@_cache_node_find
def find_user_statement(start_node, name, params, return_previous=False):
    # type: (renpy.ast.Node, t.Text, dict, bool) -> renpy.ast.UserStatement | None
    """
    Find the next user statement executing `name` after `start_node`, the first matching node is returned.

    All keys from `params` must be present in the statement's params with equal values.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        statement_name = " ".join(node.parsed[0])
        statement_params = node.parsed[1]
        return (
                statement_name == name and all(params[key] == statement_params.get(key, _MISSING) for key in params)
        )

    return _find_node(renpy.ast.UserStatement, predicate, start_node, return_previous)


@_cache_node_find
def find_return(start_node):
    # type: (renpy.ast.Node) -> renpy.ast.Return | None
    """
    Return the node before the return node found after `start_node`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.
    """

    def predicate(node):
        return True

    return _find_node(renpy.ast.Return, predicate, start_node, True)


@_cache_node_find
def find_menu(start_node, return_previous=False):
    # type: (renpy.ast.Node, bool) -> renpy.ast.Menu | None
    """
    Find the next menu node after `start_node`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_node`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return True

    return _find_node(renpy.ast.Menu, predicate, start_node, return_previous)


def mark_node_patched(node):
    # type: (renpy.ast.Node) -> None
    """Mark the `node` as patched by prepending "patched_" to its filename."""
    node.filename = "patched_" + node.filename


def patch_after_node(node, new_node, set_name=False):
    # type: (renpy.ast.Node, renpy.ast.Node, bool) -> None
    """
    Patch `new_node` to come after `node`.

    If `set_name` is set to True, the new node will be assigned the name from the original next node,
    this is necessary for rollback to not raise an error on nodes that had no name before.
    """
    original_next = node.next
    node.next = new_node
    if set_name:
        new_node.name = original_next.name
    new_node.chain(original_next)


_stop_replay_node = None


def _load_patch_nodes():
    # type: () -> None
    """Load the nodes to patch with."""
    global _stop_replay_node
    patch_label = find_label("patch_with_")
    _stop_replay_node = copy.copy(patch_label.block[0])
    mark_node_patched(_stop_replay_node)


def create_artificial_label(node, name):
    # type: (renpy.ast.Node, t.Text) -> None
    """Make `node` a "label" with `name`."""
    renpy.game.script.namemap[name] = copy.copy(node)


def create_end_replay_node():
    # type: () -> None
    """Create a new replay end node, load_patch_nodes must have been called beforehand."""
    if _stop_replay_node is None:
        _load_patch_nodes()
    return copy.copy(_stop_replay_node)


def get_nth_after(node, n):
    # type: (renpy.ast.Node, int) -> renpy.ast.Node | None
    """Get the `n`th node after `node`."""
    to_return = node
    for _ in range(n):
        to_return = to_return.next
    return to_return


def _transform_args_to_hashable(args):
    # type: (tuple[object, ...]) -> tuple[t.Hashable, ...]
    """
    Turn `args` tuple into a hashable tuple.

    Dicts are turned into tuples of their items, sets into frozensets, lists into tuples.
    Recursive checks aren't done.
    """
    val = []
    for element in args:
        if isinstance(element, set):
            element = frozenset(element)
        elif isinstance(element, dict):
            element = tuple(element.items())
        elif isinstance(element, list):
            element = tuple(element)

        val.append(element)
    val = tuple(val)
    hash(val)
    return t.cast("tuple[t.Hashable, ...]", val)


def _transform_kwargs_to_hashable(kwargs):
    # type: (dict[str, object]) -> tuple[t.Hashable, ...]
    """
    Turn a `kwargs` dictionary in to a hashable tuple.

    Dicts are turned into tuples of their items, sets into frozensets, lists into tuples.
    Recursive checks aren't done.
    """
    val = []
    for key, element in kwargs.items():
        if isinstance(element, set):
            element = frozenset(element)
        elif isinstance(element, dict):
            element = tuple(element.items())
        elif isinstance(element, list):
            element = tuple(element)

        val.append((key, element))
    val = tuple(val)
    hash(val)
    return t.cast("tuple[t.Hashable, ...]", val)
