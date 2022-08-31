# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

init 999 python hide:
    from gallery.ast_utils import (
        ANY_LABEL,
        WrappedSlNode,
        walk_sl_ast,
        walk_ast,
        find_say,
        find_label,
        find_code,
        find_jump,
        find_scene,
        find_show,
        find_user_statement,
        find_return,
        find_menu,
        patch_after_node,
        create_artificial_label,
        create_end_replay_node,
        get_nth_after,
    )
    from gallery import suppress
    # The usual statements to hook into are shows/scenes for the starts and jumps for the end
    # so that the replay stats with an image shown,
    # but our script doesn't have those so we use the say statements

    # Suppress attribute error from accessing next from None when node is not found.
    # This would be more properly done with if checks but those would be a bit more verbose to get the same
    # behaviour, and only the next error should occur for attribute errors.
    with suppress(AttributeError):
        # find a say that says "5" in any label, says are wrapped in translations so get the node after that
        replay1_start_node = find_say(ANY_LABEL, what="5").next
        # create a replay1 label after the found say from above
        create_artificial_label(replay1_start_node, "replay1")

    with suppress(AttributeError):
        start_label = find_label("example_label")  # find the start label
        # find a say that says "8" after the start label, and get the end translation node from after it
        replay1_end_node = find_say(start_label, what="8").next
        # patch in an end replay statement after the found say
        replay1_end_replay_node = create_end_replay_node()
        patch_after_node(replay1_end_node, replay1_end_replay_node)

        # place replay2 label immediately after the previous end node, let it continue until a return
        create_artificial_label(replay1_end_replay_node.next, "replay2")
