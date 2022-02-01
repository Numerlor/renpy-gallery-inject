# This file is a part of renpy-gallery-inject, see __init__.py for more details.
# Copyright (C) 2022 Numerlor

init 999 python hide:
    from gallery import (
        load_patch_nodes,
        find_label,
        find_say,
        find_scene,
        find_jump,
        patch_after_node,
        create_replay_label,
        create_end_replay_node,
        ANY_LABEL,
    )
    load_patch_nodes()  # initialize nodes to patch with, required call
    # The usual statements to hook into are shows/scenes for the starts and jumps for the end
    # so that the replay stats with an image shown,
    # but our script doesn't have those so we use the say statements

    # find a say that says "5" in any label, says are wrapped in translations so get the node after that
    replay1_star_node = find_say({"what": u"5"}, ANY_LABEL).next
    # create a replay1 label after the found say from above
    patch_after_node(replay1_star_node, create_replay_label(u"replay1"))

    start_label = find_label(u"start")  # find the start label
    # find a say that says "8" after the start label, and get the end translation node from after it
    replay1_end_node = find_say({"what": u"8"}, [start_label]).next
    # patch in an end replay statement after the found say
    replay1_end_replay_node = create_end_replay_node()
    patch_after_node(replay1_end_node, replay1_end_replay_node)

    # place replay2 label immediately after the previous end node, let it continue until a return
    patch_after_node(replay1_end_replay_node, create_replay_label(u"replay2"))
