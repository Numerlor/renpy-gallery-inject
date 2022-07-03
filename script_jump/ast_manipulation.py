# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

import copy
import time

import renpy
import renpy.ast

from gallery.ast_utils import find_label, mark_node_patched


__all__ = [
    "executing_node",
    "create_clear_label_to_node",
]


_patch_label = None
_black_scene_start = None


def _load_patch_nodes():
    global _patch_label, _black_scene_start
    _patch_label = copy.copy(find_label(u"_jump_nodes"))
    mark_node_patched(_patch_label)
    _black_scene_start = copy.copy(_patch_label.block[0])
    mark_node_patched(_black_scene_start)


def _get_scene_start_and_end():
    start = copy.copy(_black_scene_start)
    start.next = scene = copy.copy(start.next)
    mark_node_patched(scene)
    scene.next = end = copy.copy(scene.next)
    mark_node_patched(end)

    return start, end


def create_clear_label_to_node(node):
    # type: (renpy.ast.Node) -> str
    """Patch in a label that clears the scene and continues at `node`. The name of the label is returned."""
    if _black_scene_start is None or _patch_label is None:
        _load_patch_nodes()

    label_name = str(time.time())
    start = copy.copy(_patch_label)
    start.name = label_name
    renpy.game.script.namemap[label_name] = start

    clear_start, clear_end = _get_scene_start_and_end()
    start.next = clear_start
    clear_end.next = node
    return label_name


def _attach_node(node, next_):
    node.next = next_


def executing_node():
    # type: () -> renpy.ast.Node | None
    """Get the node that's currently executing in the game."""
    if renpy.game.contexts[0].current is None:
        return None
    return renpy.game.script.namemap[renpy.game.contexts[0].current]
