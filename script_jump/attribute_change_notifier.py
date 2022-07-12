# This file is a part of renpy-gallery-inject. See __init__.py for more details.
# Copyright (C) 2022 Numerlor

from __future__ import unicode_literals

import typing as t

from script_jump.weakmethod import WeakMethod

if t.TYPE_CHECKING:
    import types

__all__ = [
    "AttributeChangeNotifier",
]


class AttributeChangeNotifier(object):
    """Descriptor for notifying about changes to the assigned attribute through callbacks."""
    def __init__(self, name):
        # type: (str) -> None
        self._name = name
        self._callbacks = set()  # type: set[WeakMethod]

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        return vars(instance)[self._name]

    def __set__(self, instance, value):
        for callback_ref in self._callbacks:
            method = callback_ref()
            if method:
                method(value)

        vars(instance)[self._name] = value

    def add_callback(self, callback):
        # type: (types.MethodType) -> None
        """
        Add `callback` to the callbacks called on changes.

        A weak reference to the callback is kept.
        """
        self._callbacks.add(WeakMethod(callback))

    def remove_callback(self, callback):
        # type: (types.MethodType) -> None
        """Remove `callback` from the change callbacks."""
        self._callbacks.remove(WeakMethod(callback))
