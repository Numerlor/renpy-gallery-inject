# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    from math import ceil as __ceil

init offset = 10

define __NAVIGATION_TEXT_SIZE = 50
define __X_SPACING = 10
define __Y_SPACING = 15
define __COLS = 3
define __ROWS = 3
define __ITEM_COUNT = __COLS * __ROWS
define __MAX_PAGE_COUNT = int(__ceil(float(len(replay_defs_)) / __ITEM_COUNT))

init offset = 0

screen gallery_screen_():
    default page_index = 0
    tag menu
    use game_menu(_(u"Gallery")):
        grid __COLS __ROWS:
            xfill True
            xspacing __X_SPACING
            yspacing __Y_SPACING

            $ list_offset = __ROWS * __COLS * page_index
            $ active_button_count = __ITEM_COUNT - (__ITEM_COUNT - min(__ITEM_COUNT, len(replay_defs_) - list_offset))

            for i in range(active_button_count):
                $ item = replay_defs_[list_offset + i]
                imagebutton:
                    idle item[0]
                    action Replay(item[1], scope=item[2](), locked=False)
                    at __grid_scale

            for i in range(__ITEM_COUNT - active_button_count):
                null

        textbutton u">":
            action SetScreenVariable(u"page_index", (page_index + 1) % __MAX_PAGE_COUNT)
            xalign 0.9
            yalign 0.999
            text_size __NAVIGATION_TEXT_SIZE

        textbutton u"<":
            action SetScreenVariable(u"page_index", (page_index - 1) % __MAX_PAGE_COUNT)
            xalign 0.1
            yalign 0.999
            text_size __NAVIGATION_TEXT_SIZE

        textbutton u"Change names":
            action ShowMenu(u"name_change_screen_")
            xalign 0.5
            yalign 0.999
            text_size BOTTOM_TEXT_SIZE_

transform __grid_scale:
    fit "contain"
    xysize (0.9, 0.9)

init 999 python:
    import gallery as __gallery
    __gallery.add_button()