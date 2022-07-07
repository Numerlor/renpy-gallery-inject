# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

default persistent.mod_gallery_names_ = {}

init 1 python:
    from math import ceil as __ceil
    from itertools import product as __product

    # default_names_ defined in the config

    # do not include removed names, but keep them in persistent in case they're re-added
    __characters = list(default_names_)
    __grouped_characters = [[] for __i in range(NAME_CHANGE_NAME_COLS_)]
    for __col, __row in __product(
        range(__ceil(float(len(__characters)) / NAME_CHANGE_NAME_COLS_)),
        range(NAME_CHANGE_NAME_COLS_),
    ):
        try:
            __grouped_characters[__row].append(__characters[__col * NAME_CHANGE_NAME_COLS_ + __row])
        except IndexError:
            break
    __grouped_characters = list(filter(None, __grouped_characters))

    default_names_.update(persistent.mod_gallery_names_)
    persistent.mod_gallery_names_ = default_names_

define __reset_selection = SetScreenVariable("active_field_name", None)

screen name_change_screen_(return_menu, *return_args):
    default active_field_name = None
    key "K_RETURN" action __reset_selection
    key "K_KP_ENTER" action __reset_selection
    key "mouseup_1" action __reset_selection

    tag menu
    use game_menu(_("Gallery")):
        vpgrid:
            ymaximum .9
            xfill True
            cols NAME_CHANGE_NAME_COLS_
            xspacing NAME_CHANGE_X_SPACING_
            mousewheel True

            for character_group in __grouped_characters:
                    frame:
                        grid 1 len(character_group):
                            yspacing NAME_CHANGE_Y_SPACING_
                            for character in character_group:
                                hbox xfill True:
                                    text character size NAME_CHANGE_TEXT_SIZE_
                                    fixed:
                                        ysize 1  # do not let the input flow out of the box
                                        if character == active_field_name:
                                            input:
                                                xalign 1.0
                                                value DictInputValue(persistent.mod_gallery_names_, character)
                                                size NAME_CHANGE_TEXT_SIZE_
                                        else:
                                            textbutton persistent.mod_gallery_names_[character]:
                                                xalign 1.0
                                                padding (0, 0, 0, 0)
                                                action SetScreenVariable("active_field_name", character)
                                                text_size NAME_CHANGE_TEXT_SIZE_

        textbutton "Back" xalign 0.5 yalign 0.999 action ShowMenu(return_menu, *return_args) text_size BOTTOM_TEXT_SIZE_
