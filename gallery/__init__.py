# renpy-gallery-inject
# Copyright (C) 2022 Numerlor
#
# renpy-gallery-inject is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# renpy-gallery-inject is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with renpy-gallery-inject.  If not, see <https://www.gnu.org/licenses/>.

# Parts of this file are Copyright © 2001-2022 Python Software Foundation; All Rights Reserved,
# see LICENSE_PYTHON.md for more details.

from __future__ import unicode_literals

from itertools import islice
import typing as t

import renpy
import renpy.display.screen
from renpy.sl2 import slast

from .ast_utils import NodeWrapper, walk_sl_ast

T = t.TypeVar("T")


def add_button(use_selection_screen, force_fallback_button):
    # type: (bool, bool) -> None
    """Add a gallery button before the replay button, or at the top right if the button is not found."""
    if use_selection_screen:
        patch_screen = renpy.display.screen.get_screen_variant("menu_gallery_select_button_").function
        fallback_patch_screen = renpy.display.screen.get_screen_variant("menu_gallery_select_button_fallback_").function
    else:
        patch_screen = renpy.display.screen.get_screen_variant("menu_gallery_button_").function
        fallback_patch_screen = renpy.display.screen.get_screen_variant("menu_gallery_button_fallback_").function
    screen_to_patch = renpy.display.screen.get_screen_variant("navigation").function

    if not force_fallback_button:
        for wrapped_node in walk_sl_ast(NodeWrapper(screen_to_patch, None, 0)):
            if isinstance(wrapped_node.node, (slast.SLIf, slast.SLShowIf)):
                if any("_in_replay" in entry for entry in wrapped_node.node.entries):
                    wrapped_node.parent.node.children.insert(
                        wrapped_node.pos_in_parent - 1, patch_screen
                    )
                    return

    screen_to_patch.children.append(fallback_patch_screen)


class suppress(object):
    """Context manager to suppress specified exceptions

    After the exception is suppressed, execution proceeds with the next
    statement following the with statement.

         with suppress(FileNotFoundError):
             os.remove(somefile)
         # Execution still resumes here if the file was already removed
    """

    def __init__(self, *exceptions):
        self._exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exctype, excinst, exctb):
        return exctype is not None and issubclass(exctype, self._exceptions)


def grouper(iterable, n):
    # type: (t.Iterable[T], int) -> tuple[tuple[T, ...], ...]
    """Group items from iterable into `n` sized chunks, the last chunk may be smaller than n."""
    it = iter(iterable)
    return tuple(iter(lambda: tuple(islice(it, n)), ()))
