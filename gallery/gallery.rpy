# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    from math import ceil as __ceil

init offset = 10

define __NAVIGATION_TEXT_SIZE = 50  # size of navigation arrows
define __X_SPACING = 10
define __Y_SPACING = 15
define __COLS = 3
define __ROWS = 3
define __ITEM_COUNT = __COLS * __ROWS

init offset = 0

screen gallery_screen_(replay_items):
    default page_index = 0
    default max_page_count = int(__ceil(float(len(replay_items)) / __ITEM_COUNT))
    tag menu
    use game_menu(_(u"Gallery")):
        grid __COLS __ROWS:
            xfill True
            xspacing __X_SPACING
            yspacing __Y_SPACING

            $ list_offset = __ROWS * __COLS * page_index
            $ active_button_count = __ITEM_COUNT - (__ITEM_COUNT - min(__ITEM_COUNT, len(replay_items) - list_offset))

            for i in range(active_button_count):
                $ item = replay_items[list_offset + i]
                imagebutton:
                    idle item.image
                    hover im.MatrixColor(item.image, im.matrix.brightness(0.1))
                    action Replay(item.label, scope=item.scope_func(), locked=False)
                    at grid_scale_

            for i in range(__ITEM_COUNT - active_button_count):
                null

        textbutton u">":
            action SetScreenVariable(u"page_index", (page_index + 1) % max_page_count)
            xalign 0.9
            yalign 0.999
            text_size __NAVIGATION_TEXT_SIZE

        textbutton u"<":
            action SetScreenVariable(u"page_index", (page_index - 1) % max_page_count)
            xalign 0.1
            yalign 0.999
            text_size __NAVIGATION_TEXT_SIZE

        textbutton u"Change names":
            action ShowMenu(u"name_change_screen_", u"gallery_screen", replay_items)
            xalign 0.5
            yalign 0.999
            text_size BOTTOM_TEXT_SIZE_


init 999 python:
    import gallery as __gallery
    __gallery.add_button()
