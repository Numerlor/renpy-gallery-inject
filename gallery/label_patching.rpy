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
    __load_patch_nodes()  # initialize nodes to patch with, require call

    # find a say that says "5" in any label, says are wrapped in translations so get the node after that
    __replay1_star_node = __find_say({"what": u"5"}, __ANY_LABEL).next
    # create a replay1 label after the found say from above
    __patch_after_node(__replay1_star_node, __create_replay_label(u"replay1"))

    __start_label = __find_label(u"start")  # find the start label
    # find a say that says "8" after the start label, and get the end translation node from after it
    __replay1_end_node = __find_say({"what": u"8"}, [__start_label]).next
    # patch in an end replay statement after the found say
    __replay1_end_replay_node = __create_end_replay_node()
    __patch_after_node(__replay1_end_node, __replay1_end_replay_node)

    # place replay2 label immediately after the previous end node, let it continue until a return
    __patch_after_node(__replay1_end_replay_node, __create_replay_label(u"replay2"))
