# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

import copy
import difflib
from collections import Callable, deque, Iterator, namedtuple

import renpy.ast
from renpy.sl2 import slast

ANY_LABEL = object()
_MISSING = object()


NodeWrapper = namedtuple("NodeWrapper", ["node", "parent", "pos_in_parent"])


def walk_sl_ast(wrapped_top_node):
    # type: (NodeWrapper) -> Iterator[NodeWrapper]
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


def _find_node(type_, predicate, start_nodes, return_previous):
    # type: (type, Callable, list[renpy.ast.Node], bool) -> renpy.ast.Node | None
    """
    Find the node of `type_` for which predicate returns True, if return_previous is true, return the node before.

    If nodes to try is ANY_LABEL, try to find the node under all labels.
    """
    if start_nodes is ANY_LABEL:
        nodes_to_try = [node for node in renpy.game.script.namemap.values() if isinstance(node, renpy.ast.Label)]
    else:
        nodes_to_try = start_nodes

    for start_node in nodes_to_try:
        node = start_node
        previous_node = None
        while True:
            if node is None:
                break
            node = node.next
            if isinstance(node, type_) and predicate(node):
                if return_previous:
                    return previous_node
                return node
            previous_node = node
    else:
        return None


def find_label(label_name):
    # type: (unicode) -> renpy.ast.Label
    """Return the label with the `label_name` name."""
    return renpy.game.script.lookup(label_name)


def find_say(query, start_nodes, return_previous=False):
    # type: (dict, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next say node matching `query` after any of `start_nodes`, the first matching node is returned.

    `query` should be a dict with the following structure {"who": sayer_name, "what": message},
    where either of the pairs is optional.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        who_match = "who" not in query or query["who"] == node.who
        what_match = (
                "what" not in query
                or difflib.SequenceMatcher(None, query["what"], node.what).ratio() > 0.7
        )
        return who_match and what_match

    return _find_node(renpy.ast.Say, predicate, start_nodes, return_previous)


def find_code(var_names, start_nodes, return_previous=False):
    # type: (set, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the code node with `var_names` after any of `start_nodes`, the first matching node is returned.

    `var_names` may contain names of variables and attributes any code constants,
    if any of them is in the code, the node is seen as equal to the search.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        code = node.code.bytecode
        return bool(var_names.intersection(code.co_varnames + code.co_names + code.co_consts))

    return _find_node(renpy.ast.Python, predicate, start_nodes, return_previous)


def find_jump(label_name, start_nodes, return_previous=False):
    # type: (unicode, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next jump node that jumps to `label_name` after any of `start_nodes`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return node.target == label_name

    return _find_node(renpy.ast.Jump, predicate, start_nodes, return_previous)


def find_scene(query, start_nodes, return_previous=False):
    # type: (dict, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next scene node after any of `start_nodes`, the first matching node is returned.

    `query` should be a dict with the following structure: {"layer": layer_name, "name": name},
    where either of the pairs is optional.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return (
                ("layer" not in query or node.layer == query["layer"])
                and ("name" not in query or (node.imspec is not None and u" ".join(node.imspec[0]) == query["name"]))
        )

    return _find_node(renpy.ast.Scene, predicate, start_nodes, return_previous)


def find_show(name, start_nodes, return_previous=False):
    # type: (unicode, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next show statement showing `name` after any of `start_nodes`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return node.imspec is not None and u" ".join(node.imspec[0]) == name

    return _find_node(renpy.ast.Show, predicate, start_nodes, return_previous)


def find_user_statement(name, params, start_nodes, return_previous=False):
    # type: (unicode, dict, list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next user statement executing `name` after any of `start_nodes`, the first matching node is returned.

    All keys from `params` must be present in the statement's params with equal values.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        statement_name = u" ".join(node.parsed[0])
        statement_params = node.parsed[1]
        return (
                statement_name == name and all(params[key] == statement_params.get(key, _MISSING) for key in params)
        )

    return _find_node(renpy.ast.UserStatement, predicate, start_nodes, return_previous)


def find_return(start_nodes):
    # type: (list[renpy.ast.Node]) -> renpy.ast.Node
    """
    Return the node before the return node found after any of `start_nodes`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.
    """

    def predicate(node):
        return True

    return _find_node(renpy.ast.Return, predicate, start_nodes, True)


def find_menu(start_nodes, return_previous=False):
    # type: (list[renpy.ast.Node], bool) -> renpy.ast.Node
    """
    Find the next menu node after any of `start_nodes`, the first matching node is returned.

    When the `ANY_LABEL` sentinel is passed to `start_nodes`, all labels are searched for the node.

    If return_previous is specified, return the node before the found node.
    """

    def predicate(node):
        return True

    return _find_node(renpy.ast.Menu, predicate, start_nodes, return_previous)


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


_replay_label_node = None
_stop_replay_node = None


def load_patch_nodes():
    """Load the nodes to patch with."""
    global _replay_label_node, _stop_replay_node
    _replay_label_node = find_label(u"_patch_with")
    _stop_replay_node = _replay_label_node.block[0]
    _replay_label_node.block = []


def create_replay_label(name):
    # type: (unicode) -> renpy.ast.Label
    """Create a new no-op label, load_patch_nodes must have been called beforehand."""
    assert _replay_label_node is not None, u"template node not loaded with load_patch_nodes."
    label = copy.copy(_replay_label_node)
    label.name = name
    renpy.game.script.namemap[name] = label
    return label


def create_end_replay_node():
    # type: () -> None
    """Create a new replay end node, load_patch_nodes must have been called beforehand."""
    assert _stop_replay_node is not None, u"template node not loaded with load_patch_nodes."
    return copy.copy(_stop_replay_node)


def get_nth_after(node, n):
    # type: (renpy.ast.Node, int) -> renpy.ast.Node | None
    """Get the `n`th node after `node`."""
    to_return = node
    for _ in range(n):
        to_return = to_return.next
    return to_return