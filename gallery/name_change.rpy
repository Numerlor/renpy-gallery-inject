# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

define __TEXT_SIZE = 22
define __NAME_COLS = 3
define __Y_SPACING = 5
define __X_SPACING = 10

default persistent.mod_gallery_names_ = {}

init 1 python:
    from math import ceil as __ceil
    from itertools import product as __product

    # __default_names defined at the end

    # do not include removed names, but keep them in persistent in case they're re-added
    __characters = list(__default_names)
    __grouped_characters = [[] for __i in range(__NAME_COLS)]
    for __col, __row in __product(
        range(__ceil(float(len(__characters)) / __NAME_COLS)),
        range(__NAME_COLS),
    ):
        try:
            __grouped_characters[__row].append(__characters[__col * __NAME_COLS + __row])
        except IndexError:
            break
    __grouped_characters = list(filter(None, __grouped_characters))

    __default_names.update(persistent.mod_gallery_names_)
    persistent.mod_gallery_names_ = __default_names

define __reset_selection = SetScreenVariable(u"active_field_name", None)

screen name_change_screen_(return_menu, return_menu_arg):
    default active_field_name = None
    key "K_RETURN" action __reset_selection
    key "K_KP_ENTER" action __reset_selection
    key "mouseup_1" action __reset_selection

    tag menu
    use game_menu(_(u"Gallery")):
        vpgrid:
            ymaximum .9
            xfill True
            cols __NAME_COLS
            xspacing __X_SPACING
            mousewheel True

            for character_group in __grouped_characters:
                    frame:
                        grid 1 len(character_group):
                            yspacing __Y_SPACING
                            for character in character_group:
                                hbox xfill True:
                                    text character size __TEXT_SIZE
                                    fixed:
                                        ysize 1  # do not let the input flow out of the box
                                        if character == active_field_name:
                                            input:
                                                xalign 1.0
                                                value DictInputValue(persistent.mod_gallery_names_, character)
                                                size __TEXT_SIZE
                                        else:
                                            textbutton persistent.mod_gallery_names_[character]:
                                                xalign 1.0
                                                padding (0, 0, 0, 0)
                                                action SetScreenVariable(u"active_field_name", character)
                                                text_size __TEXT_SIZE

        textbutton u"Return" xalign 0.5 yalign 0.999 action ShowMenu(return_menu, return_menu_arg) text_size BOTTOM_TEXT_SIZE_

init python:
     from collections import OrderedDict as __OrderedDict
     # Names configurable by the user, stored in the persistent.mod_gallery_names_ dict
     __default_names = __OrderedDict(("test{}".format(i), "default" * 2) for i in range(10))
     __default_names["Player"] = "name"
