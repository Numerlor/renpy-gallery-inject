# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

define BOTTOM_TEXT_SIZE_ = 30

screen _menu_gallery_button():
    if not _in_replay:
        textbutton _("Gallery") action ShowMenu("gallery_screen")

screen _menu_gallery_button_fallback():
    if not _in_replay:
        textbutton _("Gallery") xalign 0.99 yalign 0 text_size 25 action ShowMenu("gallery_screen")

label _patch_with:
    $ renpy.end_replay()
