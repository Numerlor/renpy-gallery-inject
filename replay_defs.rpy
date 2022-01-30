# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init python:
    def __default_scope():
        return {"player": Character(persistent.mod_gallery_names_["Player"])}

define replay_defs_ = [
    ("images/test.png", "replay1", __default_scope),
    ("images/test.png", "replay2", __default_scope),
    ("images/test.png", "test_label", __default_scope),
]*8
