# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

import copy
from functools import partial

import renpy
import renpy.ast

from gallery.ast_utils import find_label, mark_node_patched


__all__ = [
    "executing_node",
    "patch_clear_after_node",
]


class _PythonCallback(renpy.ast.Node):
    """Directly execute the passed `callback`."""

    def __init__(self, loc, callback):
        super(_PythonCallback, self).__init__(loc)
        self.filename = "patched_" + self.filename
        self.callback = callback
        self.name = self.filename

    def execute(self):
        self.callback()
        renpy.ast.next_node(self.next)


_patch_label = None
_black_scene_start = None
_empty_say = None


def _load_patch_nodes():
    global _patch_label, _black_scene_start, _empty_say
    _patch_label = find_label(u"_jump_nodes")
    _black_scene_start = copy.copy(_patch_label.block[0])
    mark_node_patched(_black_scene_start)
    _empty_say = copy.copy(_patch_label.block[4])
    mark_node_patched(_empty_say)


def _get_scene_start_and_end():
    start = copy.copy(_black_scene_start)
    start.next = scene = copy.copy(start.next)
    mark_node_patched(scene)
    scene.next = end = copy.copy(scene.next)
    mark_node_patched(end)

    return start, end


def patch_clear_after_node(node):
    # type: (renpy.ast.Node) -> None
    """
    Patch in a scene and say clear after `node`.

    After the node is reached, its original next node is reattached.
    """

    original_next = node.next
    python_node = node.next = _PythonCallback((node.filename, node.linenumber), partial(_attach_node, node, node.next))
    if _black_scene_start is None or _empty_say is None:
        _load_patch_nodes()
    clear_start, clear_end = _get_scene_start_and_end()
    python_node.next = clear_start
    clear_end.next = say_node = copy.copy(_empty_say)
    say_node.next = original_next


def _attach_node(node, next_):
    node.next = next_


def executing_node():
    # type: () -> renpy.ast.Node | None
    """Get the node that's currently executing in the game."""
    if renpy.game.contexts[0].current is None:
        return None
    return renpy.game.script.namemap[renpy.game.contexts[0].current]
