# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    from math import ceil as __ceil


screen gallery_screen_(replay_items):
    default page_index = 0
    default max_page_count = int(__ceil(float(len(replay_items)) / GALLERY_ITEM_COUNT_))
    tag menu
    use game_menu(_(u"Gallery")):
        grid GALLERY_COLS_ GALLERY_ROWS_:
            xfill True
            xspacing GALLERY_X_SPACING_
            yspacing GALLERY_Y_SPACING_

            $ list_offset = GALLERY_ROWS_ * GALLERY_COLS_ * page_index
            $ active_button_count = GALLERY_ITEM_COUNT_ - (GALLERY_ITEM_COUNT_ - min(GALLERY_ITEM_COUNT_, len(replay_items) - list_offset))

            for i in range(active_button_count):
                $ item = replay_items[list_offset + i]
                imagebutton:
                    idle item.image
                    hover im.MatrixColor(item.image, im.matrix.brightness(0.1))
                    action Replay(item.label, scope=item.scope_func(), locked=False)
                    at grid_scale_

            for i in range(GALLERY_ITEM_COUNT_ - active_button_count):
                null

        textbutton u">":
            action SetScreenVariable(u"page_index", (page_index + 1) % max_page_count)
            xalign 0.9
            yalign 0.999
            text_size GALLERY_NAVIGATION_TEXT_SIZE_

        textbutton u"<":
            action SetScreenVariable(u"page_index", (page_index - 1) % max_page_count)
            xalign 0.1
            yalign 0.999
            text_size GALLERY_NAVIGATION_TEXT_SIZE_

        if USE_GALLERY_SELECTION_SCREEN_:
            textbutton u"Back":
                action ShowMenu(u"gallery_select_screen_")
                xalign 0.5
                yalign 0.999
                text_size BOTTOM_TEXT_SIZE_
        else:
            textbutton u"Change names":
                action ShowMenu(u"name_change_screen_", u"gallery_screen_", replay_items)
                xalign 0.5
                yalign 0.999
                text_size BOTTOM_TEXT_SIZE_


init 999 python:
    import gallery as __gallery
    __gallery.add_button(USE_GALLERY_SELECTION_SCREEN_)
