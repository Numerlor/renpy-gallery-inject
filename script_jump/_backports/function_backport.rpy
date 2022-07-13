# This file is a part of renpy-gallery-inject. See __init__.py, and LICENSE_RENPY for more details.
# Copyright (C) 2022 Numerlor, Copyright 2004-2022 Tom Rothamel <pytom@bishoujo.us>

init -500 python:
    if (
        renpy.version_tuple[0] == 7 and renpy.version_tuple < (7, 5, 1)
        or renpy.version_tuple[0] == 8 and renpy.version_tuple < (8, 0, 1)
    ):
        def function_action_equality(self, other):
            if type(self) is not type(other):
                return False

            if PY2:
                if self.callable is not other.callable:
                    return False
            else:
                if self.callable != other.callable:
                    return False

            if self.args != other.args:
                return False

            if self.kwargs != other.kwargs:
                return False

            for a, b in zip(self.args, other.args):
                if a is not b:
                    return False

            for k in self.kwargs:
                if self.kwargs[k] is not other.kwargs[k]:
                    return False

            if self.update_screens != other.update_screens:
                return False

            return True

        Function.__eq__ = function_action_equality
        Function.__ne__ = lambda self, other: not function_action_equality(self, other)
