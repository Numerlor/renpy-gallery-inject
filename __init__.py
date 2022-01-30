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

import renpy
import renpy.display.screen
from renpy.sl2 import slast

from .ast_utils import *


def add_button():
    # type: () -> None
    """Add a gallery button before the replay button, or at the top right if the button is not found."""
    screens = renpy.display.screen.screens_by_name
    patch_screen = screens[u"menu_gallery_button_"][None].function
    fallback_patch_screen = screens[u"menu_gallery_button_fallback_"][None].function
    screen_to_patch = screens[u"navigation"][None].function

    for wrapped_node in walk_sl_ast(NodeWrapper(screen_to_patch, None, 0)):
        if isinstance(wrapped_node.node, (slast.SLIf, slast.SLShowIf)):
            if any(u"_in_replay" in entry for entry in wrapped_node.node.entries):
                wrapped_node.parent.parent.node.children.insert(
                    wrapped_node.parent.pos_in_parent - 1, patch_screen
                )
                break
    else:
        screen_to_patch.children.append(fallback_patch_screen)
