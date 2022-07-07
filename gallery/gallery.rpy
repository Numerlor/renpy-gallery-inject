# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    def __create_gallery_select_show_action(item):
        return ShowMenu("replay_gallery_screen_", item.replay_item_list)

    def __create_gallery_replay_action(item):
        return ReplayExisting(item.label, scope=item.scope_func())

screen replay_gallery_screen_(replay_items):
    tag menu
    use gallery_screen_(replay_items, __create_gallery_replay_action):
        if USE_GALLERY_SELECTION_SCREEN_:
            textbutton "Back":
                action ShowMenu("gallery_select_screen_")
                xalign 0.5
                yalign 0.999
                text_size BOTTOM_TEXT_SIZE_
        else:
            textbutton "Change names":
                action ShowMenu("name_change_screen_", "replay_gallery_screen_", replay_items)
                xalign 0.5
                yalign 0.999
                text_size BOTTOM_TEXT_SIZE_


screen gallery_select_screen_():
    tag menu
    use gallery_screen_(GALLERIES_, __create_gallery_select_show_action):
        textbutton "Change names":
            action ShowMenu("name_change_screen_", "gallery_select_screen_")
            xalign 0.5
            yalign 0.999
            text_size BOTTOM_TEXT_SIZE_


# Gallery template screen with a grid of image buttons created from paged_items, clicking on a button
# triggers the action returned by the call action_function(item),
# where item is one of the items from the paged_items param.
# Transclude is at the end after defining the grid and navigation buttons.
screen gallery_screen_(paged_items, action_function):
    default page_index = 0

    use game_menu(_("Gallery")):
        vpgrid:
            ymaximum .9
            xfill True
            yfill True
            cols GALLERY_COLS_
            rows GALLERY_ROWS_
            xspacing GALLERY_X_SPACING_
            yspacing GALLERY_Y_SPACING_

            for item in paged_items[page_index]:
                imagebutton:
                    idle item.image
                    hover item.hover_image
                    action action_function(item)
                    at grid_scale_

            for i in range(GALLERY_ITEM_COUNT_ - len(paged_items[page_index])):
                null

        textbutton ">":
            action SetLocalVariable("page_index", (page_index + 1) % len(paged_items))
            xalign 0.9
            yalign 0.999
            text_size GALLERY_NAVIGATION_TEXT_SIZE_

        textbutton "<":
            action SetLocalVariable("page_index", (page_index - 1) % len(paged_items))
            xalign 0.1
            yalign 0.999
            text_size GALLERY_NAVIGATION_TEXT_SIZE_

        transclude

init 999 python:
    import gallery as __gallery
    __gallery.add_button(USE_GALLERY_SELECTION_SCREEN_, FORCE_FALLBACK_BUTTON_)
