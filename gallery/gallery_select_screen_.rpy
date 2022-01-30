# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    from math import ceil as __ceil


screen gallery_select_screen_():
    default page_index = 0
    default max_page_count = int(__ceil(float(len(GALLERIES_)) / GALLERY_ITEM_COUNT_))
    tag menu
    use game_menu(_(u"Gallery")):
        grid GALLERY_COLS_ GALLERY_ROWS_:
            xfill True
            xspacing GALLERY_X_SPACING_
            yspacing NAME_CHANGE_Y_SPACING_

            $ list_offset = GALLERY_ROWS_ * GALLERY_COLS_ * page_index
            $ active_button_count = GALLERY_ITEM_COUNT_ - (GALLERY_ITEM_COUNT_ - min(GALLERY_ITEM_COUNT_, len(GALLERIES_) - list_offset))

            for i in range(active_button_count):
                $ item = GALLERIES_[list_offset + i]
                imagebutton:
                    idle item.image
                    hover im.MatrixColor(item.image, im.matrix.brightness(0.1))
                    action ShowMenu("gallery_screen_", item.replay_item_list)
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

        textbutton u"Change names":
            action ShowMenu(u"name_change_screen_", u"gallery_select_screen_")
            xalign 0.5
            yalign 0.999
            text_size BOTTOM_TEXT_SIZE_