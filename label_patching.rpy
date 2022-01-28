# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init 999 python:
    from gallery import (
        load_patch_nodes as __load_patch_nodes,
        find_label as __find_label,
        find_say as __find_say,
        find_scene as __find_scene,
        find_jump as __find_jump,
        patch_after_node as __patch_after_node,
        create_replay_label as __create_replay_label,
        create_end_replay_node as __create_end_replay_node,
        ANY_LABEL as __ANY_LABEL,
    )
    __load_patch_nodes()

    __label = __find_label(u"start")
    __to_replace = __find_say({"what": u"5"}, __ANY_LABEL)

    __patch_after_node(__to_replace, __create_replay_label(u"replay1"), set_name=False)

    __label = __find_label(u"start")
    __to_replace = __find_say({"what": u"8"}, __ANY_LABEL)

    __patch_after_node(__to_replace, __create_replay_label(u"replay2"), set_name=False)
