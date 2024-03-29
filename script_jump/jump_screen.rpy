# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

define config.search_prefixes += ["renpy-gallery-inject-resources/"]
define config.always_shown_screens += ["ScriptLog"]

init python:
    import operator as __operator

    from script_jump.ast_manipulation import (
        executing_node as __executing_node,
        create_clear_label_to_node as __create_clear_label_to_node,
    )
    from script_jump.execution_tracing import (
        forked_child_logs as __forked_child_logs,
        node_forkable as __node_forkable,
        NodePathLog as __NodePathLog,
        patch_context_notifier as __patch_context_notifier,
    )
    from script_jump.utils import (
        escape_renpy_formatting as __escape_renpy_formatting,
        LogWrapper as __LogWrapper,
        NoRollbackValue as __NoRollbackValue,
        get_node_find_string as __get_node_find_string,
        set_clipboard as __set_clipboard,
    )

    __patch_context_notifier()


    @renpy.pure
    class __SetFieldFromCallable(Function):
        def __init__(self, object, name, callable, *args, **kwargs):
            super(__SetFieldFromCallable, self).__init__(callable, *args, **kwargs)
            self.name = name
            self.obj = object

        def __call__(self):
            setattr(self.obj, self.name, super(__SetFieldFromCallable, self).__call__())

        def __eq__(self, other):
            return (
                self.name == other.name
                and self.obj is other.obj
                and super(__SetFieldFromCallable, self).__eq__(other)
            )

        __ne__ = lambda self, other: not __eq__(self, other)


    __SetValField = lambda obj, val: SetField(obj, "value", val)
    __SetValFieldFromCallable = lambda obj, callable, *args, **kwargs: __SetFieldFromCallable(obj, "value", callable, *args, **kwargs)

    logs = []  # type: list[__LogWrapper]


    def __log_from_executing_node():
        """
        Get the log from the currently executing node.

        If a log with the executing node was already created, return it instead of creating a new one.
        """
        node = __executing_node()
        if node is None:
            return None
        for wrapped_log in logs:
            if wrapped_log.log.has_node(node):
                return wrapped_log
        new_log = __LogWrapper(None, __NodePathLog(node))
        logs.append(new_log)
        return new_log


    def __patch_label_and_jump(node):
        jump_name = __create_clear_label_to_node(node)
        renpy.jump(jump_name)

    def __copy_find_string(wrapped_node):
        to_copy = __get_node_find_string(wrapped_node)
        if to_copy is not None:
            print(to_copy)
            __set_clipboard(to_copy)


screen ScriptLog():
    zorder 50
    default active_log = __NoRollbackValue(None)
    default visible = __NoRollbackValue(True)
    default forking_node = __NoRollbackValue(None)
    default show_logs = __NoRollbackValue(False)

    imagebutton:
        if visible.value:
            idle "visible.png"
            hover "hidden.png"
        else:
            idle "hidden.png"
            hover "visible.png"
        yalign 0.5
        yoffset -250 - 20
        xalign 1.0
        action __SetValField(visible, not visible.value)

    if visible.value:
        if not show_logs.value:
            if active_log.value is not None:
                use main_list_view(len(active_log.value.current_page)):
                    for wrapped_node in active_log.value.current_page:
                        vbox:
                            hbox ysize 20 xsize 250:
                                textbutton __escape_renpy_formatting(str(wrapped_node)):
                                    padding (0, 0, 0, 0)
                                    yalign 0.5
                                    text_size 10
                                    action Function(__patch_label_and_jump, wrapped_node.node)
                                    alternate Function(__copy_find_string, wrapped_node)
                                    text_font "JetBrainsMono-SemiBold.ttf"
                                    text_layout "nobreak"
                                    if wrapped_node is active_log.value.log.current_node:
                                        text_color "#ffeb5c"

                                if __node_forkable(wrapped_node):
                                    imagebutton:
                                        idle "fork.png"
                                        padding (0, 0, 0, 0)
                                        xalign 1.0
                                        xoffset -2
                                        yalign 0.5
                                        action [
                                            __SetValField(forking_node, wrapped_node),
                                            CaptureFocus("fork_dropdown"),
                                       ]
                            bar ysize 1 xsize 250
            else:
                use main_list_view(0)

        else:
            use main_list_view(len(logs)):
                for wrapped_log in logs:
                    vbox:
                        hbox xfill True ysize 20 xsize 250:
                            textbutton __escape_renpy_formatting(str(next(iter(wrapped_log.log.nodes)))):
                                padding (0, 0, 0, 0)
                                yalign 0.5
                                text_size 10
                                action [
                                    __SetValField(active_log, wrapped_log),
                                    __SetValField(show_logs, not show_logs.value),
                                ]
                                text_font "JetBrainsMono-SemiBold.ttf"
                                text_layout "nobreak"

                        bar ysize 1 xsize 250

        use navigation_buttons

        if GetFocusRect("fork_dropdown"):
            use fork_dropdown_list


screen fork_dropdown_list:
    if forking_node.value is None:  # rollback/rollforward messes with the variable
        $ renpy.clear_capture_focus("fork_dropdown")
    else:
        dismiss action [ClearFocus("fork_dropdown"), __SetValField(forking_node, None)]
        nearrect:
            focus "fork_dropdown"
            frame:
                vpgrid:
                    cols 1
                    rows len(__forked_child_logs(forking_node.value))
                    yspacing 0
                    for log in __forked_child_logs(forking_node.value):
                        vbox:
                            hbox ysize 20 xsize 250:
                                textbutton __escape_renpy_formatting(str(next(iter(log.nodes)))):
                                    padding (0, 0, 0, 0)
                                    yalign 0.5
                                    text_size 10
                                    action [
                                        Function(logs.append, __LogWrapper(active_log.value, log)),
                                        __SetValFieldFromCallable(active_log, __operator.itemgetter(-1), logs),
                                        ClearFocus("fork_dropdown"),
                                    ]
                                    text_font "JetBrainsMono-SemiBold.ttf"
                                    text_layout "nobreak"
                            bar ysize 1 xsize 250


screen navigation_buttons:
    frame:
        xalign 1.0
        ysize 32 + 7
        yalign 0.5
        yoffset 250 + 17
        xsize 250 + 7
        hbox:
            imagebutton:
                idle "start_arrow.png"
                yalign 0.5
                action __SetValFieldFromCallable(active_log, __log_from_executing_node)

            vbar xsize 2 ysize 32

            imagebutton:
                idle "left_arrow.png"
                if active_log.value is not None:
                    action SetField(
                        active_log,
                        "value.page_index",
                        (active_log.value.page_index - 1) % len(active_log.value.log.paged_nodes)
                    )

            vbar xsize 2 ysize 32

            imagebutton:
                idle "right_arrow.png"
                if active_log.value is not None:
                    action SetField(
                        active_log,
                        "value.page_index",
                        (active_log.value.page_index + 1) % len(active_log.value.log.paged_nodes)
                    )
            vbar xsize 2 ysize 32

            imagebutton:
                idle "back.png"
                insensitive Transform("back.png", matrixcolor=BrightnessMatrix(-0.6))
                yalign 0.5
                if active_log.value is not None and active_log.value.parent is not None:
                    action __SetValField(active_log, active_log.value.parent)
                elif show_logs.value:
                    action __SetValField(show_logs, not show_logs.value)

            vbar xsize 2 ysize 32

            imagebutton:
                idle "menu.png"
                action __SetValField(show_logs, not show_logs.value)

            vbar xsize 2 ysize 32


screen main_list_view(length):
    frame:
        xalign 1.0
        ysize 500
        yalign 0.5
        xsize 250 + 7
        if length:
            vpgrid id "vp":
                cols 1
                rows length
                yspacing 0
                xsize 250
                mousewheel True
                transclude

            vbar value YScrollValue("vp") xalign 1.0 xsize 3 xoffset 4


label _jump_nodes:
    window show
    scene black
    window auto
