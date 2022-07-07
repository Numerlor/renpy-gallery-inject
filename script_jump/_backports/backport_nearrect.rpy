# This file is a part of renpy-gallery-inject, see __init__.py, and LICENSE_RENPY for more details.
# Copyright (C) 2022 Numerlor, Copyright 2004-2022 Tom Rothamel <pytom@bishoujo.us>

init -1000 python early hide:
    import renpy.display.layout
    if not hasattr(renpy.display.layout, "NearRect"):
        store.__patched = True
        import renpy
        from script_jump._backports.backport_nearrect import NearRect, DismissBehavior

        nearrect_parser = renpy.sl2.slparser.DisplayableParser("nearrect", NearRect, "default", 1, replaces=True)
        renpy.sl2.slparser.Keyword("rect")
        renpy.sl2.slparser.Keyword("focus")
        renpy.sl2.slparser.Keyword("prefer_top")
        renpy.sl2.slparser.add(renpy.sl2.slproperties.position_properties)

        dismiss_parser = renpy.sl2.slparser.DisplayableParser("dismiss", DismissBehavior , "default", 0)
        renpy.sl2.slparser.Keyword("action")
        renpy.sl2.slparser.Keyword("modal")
        renpy.sl2.slparser.Style("alt")
        renpy.sl2.slparser.Style("sound")
        renpy.sl2.slparser.Style("debug")
        renpy.sl2.slparser.screen_parser.add([nearrect_parser, dismiss_parser])
        nearrect_parser.add(renpy.sl2.slparser.all_statements)
        dismiss_parser.add(renpy.sl2.slparser.if_statement)
        dismiss_parser.add(renpy.sl2.slparser.pass_statement)

        # Ensure that Parsers are no longer added automatically.
        renpy.sl2.slparser.parser = None
    else:
        store.__patched = True

init -500 python:
    if __patched:
        from script_jump._backports.backport_nearrect import (
            capture_focus as __capture_focus,
            clear_capture_focus as __clear_capture_focus,
            get_focus_rect as __get_focus_rect,
            take_focuses as __take_focuses,
        )
        @renpy.pure
        class CaptureFocus(Action, DictEquality):
            def __init__(self, name="default"):
                self.name = name

            def __call__(self):
                __capture_focus(self.name)
                renpy.restart_interaction()


        @renpy.pure
        class ToggleFocus(Action, DictEquality):
            def __init__(self, name="default"):
                self.name = name

            def __call__(self):
                name = self.name

                if __get_focus_rect(name) is not None:
                    __clear_capture_focus(name)
                else:
                    __capture_focus(name)

                renpy.restart_interaction()


        @renpy.pure
        class ClearFocus(Action, DictEquality):
            def __init__(self, name="default"):
                self.name = name

            def __call__(self):
                __clear_capture_focus(self.name)
                renpy.restart_interaction()

        def GetFocusRect(name="default"):
            return __get_focus_rect(name)

        __original = renpy.display.core.Interface.draw_screen
        def __with_focus(*args, **kwargs):
            __original(*args, **kwargs)
            __take_focuses()

        renpy.display.core.Interface.draw_screen = __with_focus