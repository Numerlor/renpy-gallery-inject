# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

# buttons used to jump straight to a replay gallery

screen menu_gallery_button_():
    if not _in_replay:
        textbutton _("Gallery") action ShowMenu("replay_gallery_screen_", main_gallery_replay_items)

screen menu_gallery_button_fallback_():
    if not _in_replay:
        textbutton _("Gallery"):
            xalign FALLBACK_BUTTON_X_ALIGN_
            yalign FALLBACK_BUTTON_Y_ALIGN_
            text_size FALLBACK_BUTTON_SIZE_
            action ShowMenu("replay_gallery_screen_", main_gallery_replay_items)

# buttons used to jump to a gallery selection screen

screen menu_gallery_select_button_():
    if not _in_replay:
        textbutton _("Gallery") action ShowMenu("gallery_select_screen_")

screen menu_gallery_select_button_fallback_():
    if not _in_replay:
        textbutton _("Gallery"):
            xalign FALLBACK_BUTTON_X_ALIGN_
            yalign FALLBACK_BUTTON_Y_ALIGN_
            text_size FALLBACK_BUTTON_SIZE_
            action ShowMenu("gallery_select_screen_")

transform grid_scale_:
    fit "contain"
    xysize (1.0, 1.0)

label patch_with_:
    $ renpy.end_replay()
