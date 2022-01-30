# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

define BOTTOM_TEXT_SIZE_ = 30  # text at the bottom of the screen, e.g. 'Change name' or 'Return'

screen menu_gallery_button_():
    if not _in_replay:
        textbutton _("Gallery") action ShowMenu("gallery_screen_", replay_defs_)

screen menu_gallery_button_fallback_():
    if not _in_replay:
        textbutton _("Gallery") xalign 0.99 yalign 0 text_size 25 action ShowMenu("gallery_screen_", replay_defs_)

label patch_with_:
    $ renpy.end_replay()
