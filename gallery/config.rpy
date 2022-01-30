# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init offset = -5

init python:
    from collections import namedtuple as __namedtuple
    ReplayItem_ = __namedtuple("ReplayItem_", ["image", "label", "scope_func"])
    GalleryItem_ = __namedtuple("GalleryItem_", ["image", "replay_item_list"])

    def __default_scope():
        return {"player": Character(persistent.mod_gallery_names_["Player"])}

define USE_GALLERY_SELECTION_SCREEN_ = True

define replay_defs_ = [
    ReplayItem_("test.png", "replay1", __default_scope),
    ReplayItem_("test.png", "replay2", __default_scope),
]

define GALLERIES_ = [
   GalleryItem_("test.png", replay_defs_)
]
