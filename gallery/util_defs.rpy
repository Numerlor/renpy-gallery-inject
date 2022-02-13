# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

# buttons used to jump straight to a replay gallery

screen menu_gallery_button_():
    if not _in_replay:
        textbutton _("Gallery") action ShowMenu("replay_gallery_screen_", MAIN_GALLERY_REPLAY_ITEMS_)

screen menu_gallery_button_fallback_():
    if not _in_replay:
        textbutton _("Gallery"):
            xalign FALLBACK_BUTTON_X_ALIGN_
            yalign FALLBACK_BUTTON_Y_ALIGN_
            text_size FALLBACK_BUTTON_SIZE_
            action ShowMenu("replay_gallery_screen_", MAIN_GALLERY_REPLAY_ITEMS_)

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

label patch_with_:
    $ renpy.end_replay()

init -1 python:
    from collections import namedtuple as __namedtuple

    class ReplayItem_:
        def __init__(self, image, label, scope_func):
            self.image = renpy.easy.displayable(image)
            self.label = label
            self.scope_func = scope_func
            self._hover_image = None

        @property
        def hover_image(self):
            if self._hover_image is None:
                self._hover_image = Transform(self.image, matrixcolor=BrightnessMatrix(0.1))
            return self._hover_image

    GalleryItem_ = __namedtuple("GalleryItem_", ["image", "replay_item_list"])