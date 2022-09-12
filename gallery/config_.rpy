# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

# should the gallery selection screen be used for multiple galleries
define USE_GALLERY_SELECTION_SCREEN_ = False

# size of the change name/back text at the bottom
define BOTTOM_TEXT_SIZE_ = 30

# size of text in name changer
define NAME_CHANGE_TEXT_SIZE_ = 22
# number of columns in name changer
define NAME_CHANGE_NAME_COLS_ = 3
# spacing between columns in name changer
define NAME_CHANGE_Y_SPACING_ = 5
# spacing between items in columns in name changer
define NAME_CHANGE_X_SPACING_ = 10

# size of gallery navigation arrows
define GALLERY_NAVIGATION_TEXT_SIZE_ = 50
define GALLERY_X_SPACING_ = 10
define GALLERY_Y_SPACING_ = 15

# Amount of columns in galleries
define GALLERY_COLS_ = 3
# Amount of rows in galleries
define GALLERY_ROWS_ = 3
define GALLERY_ITEM_COUNT_ = GALLERY_COLS_ * GALLERY_ROWS_

# Force use of the fallback button if the position in the menu is undesirable
define FORCE_FALLBACK_BUTTON_ = False
# Properties applied to the fallback gallery button which is used if a position in the menu can't be found.
define FALLBACK_BUTTON_X_ALIGN_ = 0.99
define FALLBACK_BUTTON_Y_ALIGN_ = 0.0
define FALLBACK_BUTTON_SIZE_ = 35

init python:
    from collections import OrderedDict as __OrderedDict
    from gallery import grouper as __grouper

    def __default_scope():
        return {"player": Character(persistent.mod_gallery_names_["Player"])}

# Items are grouped into pages by the grouper function
# List of replay items used by galleries, MAIN_GALLERY_REPLAY_ITEMS_ is used when USE_GALLERY_SELECTION_SCREEN_ is False
define MAIN_GALLERY_REPLAY_ITEMS_ = __grouper(
    [
        ReplayItem_("test.png", "replay1", __default_scope),
        ReplayItem_("test.png", "replay2", __default_scope),
    ]*10,
    GALLERY_ITEM_COUNT_,
)

# List of galleries and their replay items if the gallery selection is enabled
define GALLERIES_ = __grouper(
    [
        GalleryItem_("test.png", MAIN_GALLERY_REPLAY_ITEMS_),
    ]*10,
    GALLERY_ITEM_COUNT_,
)

# Names configurable by the user and their defaults, stored in persistent.mod_gallery_names_,
# to use in the scopes passed to replay items
init python:
    default_names_ = __OrderedDict(
        (
            ("Player", "name"),
        )
    )
    default_names_.update(("test{}".format(i), "default" * 2) for i in range(10))
