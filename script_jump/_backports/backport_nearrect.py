# This file is a part of renpy-gallery-inject. See __init__.py, and LICENSE_RENPY for more details.
# Copyright (C) 2022 Numerlor, Copyright 2004-2022 Tom Rothamel <pytom@bishoujo.us>

from __future__ import division, absolute_import, with_statement, print_function, unicode_literals

import operator

import pygame_sdl2 as pygame
import renpy
from renpy.display.behavior import alt, map_event, run


class DismissBehavior(renpy.display.core.Displayable):
    focusable = True

    def __init__(self, action=None, modal=True, **properties):
        super(DismissBehavior, self).__init__(**properties)

        if action is None:
            raise Exception("Dismiss requires an action.")

        self.action = action
        self.modal = modal

    def _tts(self):
        return ""

    def _tts_all(self):
        rv = self._tts_common(alt(self.action))
        return rv

    def find_focusable(self, callback, focus_name):
        if self.modal and not callable(self.modal):
            mark_modal()

        super(DismissBehavior, self).find_focusable(callback, focus_name)

    def render(self, width, height, st, at):
        rv = renpy.display.render.Render(0, 0)

        rv.add_focus(self, None, None, None, None, None)

        if self.modal and not callable(self.modal):
            rv.modal = True

        return rv

    def event(self, ev, x, y, st):

        if self.is_focused() and map_event(ev, "dismiss"):
            renpy.exports.play(self.style.activate_sound)
            rv = run(self.action)

            if rv is not None:
                return rv
            else:
                raise renpy.display.core.IgnoreEvent()

        if renpy.display.layout.check_modal(self.modal, ev, x, y, None, None):
            raise renpy.display.layout.IgnoreLayers()


class NearRect(renpy.display.layout.Container):

    def __init__(self, child=None, rect=None, focus=None, prefer_top=False, replaces=None, **properties):

        super(NearRect, self).__init__(**properties)

        if focus is not None:
            rect = get_focus_rect(focus)

        if (focus is None) and (rect is None):
            raise Exception("A NearRect requires either a focus or a rect parameter.")

        self.parent_rect = rect
        self.focus_rect = focus
        self.prefer_top = prefer_top

        if replaces is not None:
            self.hide_parent_rect = replaces.hide_parent_rect
        else:
            self.hide_parent_rect = None

        if child is not None:
            self.add(child)

    def per_interact(self):

        if self.focus_rect is None:
            return

        rect = get_focus_rect(self.focus_rect)

        if (rect is not None) and (self.parent_rect is None):
            self.child.set_transform_event("show")
        elif (rect is None) and (self.parent_rect is not None):
            self.child.set_transform_event("hide")
            self.hide_parent_rect = self.parent_rect

        if self.parent_rect != rect:
            self.parent_rect = rect
            renpy.display.render.redraw(self, 0)

    def render(self, width, height, st, at):

        rv = renpy.display.render.Render(width, height)

        rect = self.parent_rect or self.hide_parent_rect

        if rect is None:
            self.offsets = [(0, 0)]
            return rv

        px, py, pw, ph = rect

        avail_w = width
        avail_h = max(py, height - py - ph)

        cr = renpy.display.render.render(self.child, avail_w, avail_h, st, at)
        cw, ch = cr.get_size()

        if isinstance(self.child, renpy.display.motion.Transform):
            if self.child.hide_response:
                self.hide_parent_rect = None
        else:
            self.hide_parent_rect = None

        rect = self.parent_rect or self.hide_parent_rect

        if rect is None:
            self.offsets = [(0, 0)]
            return rv

        xpos, _ypos, xanchor, _yanchor, xoffset, yoffset, _subpixel = self.child.get_placement()

        if xpos is None:
            xpos = 0
        if xanchor is None:
            xanchor = 0
        if xoffset is None:
            xoffset = 0
        if yoffset is None:
            yoffset = 0

        if self.prefer_top and (ch < py):
            layout_y = py - ch
        elif ch < (height - pw - ph):
            layout_y = py + ph
        else:
            layout_y = py - ch

        if isinstance(xpos, float):
            xpos = xpos * pw

        if isinstance(xanchor, float):
            xanchor = xanchor * cw

        layout_x = px + xpos - xanchor

        if layout_x + cw > width:
            layout_x = width - cw

        if layout_x < 0:
            layout_x = 0

        layout_x += xoffset
        layout_y += yoffset

        rv.blit(cr, (layout_x, layout_y))
        self.offsets = [(layout_x, layout_y)]

        return rv

    def event(self, ev, x, y, st):
        if self.parent_rect is not None:
            return super(NearRect, self).event(ev, x, y, st)
        else:
            return None

    def _tts(self):
        if self.parent_rect is not None:
            return self._tts_common()
        else:
            return ""


focus_storage = {}


def capture_focus(name="default"):
    rect = focus_coordinates()
    if rect[0] is None:
        rect = None

    if rect is not None:
        focus_storage[name] = rect
    else:
        focus_storage.pop(name, None)


def clear_capture_focus(name="default"):
    focus_storage.pop(name, None)


def get_focus_rect(name="default"):
    return focus_storage.get(name, None)


class Focus(object):

    def __init__(self, widget, arg, x, y, w, h, screen):

        self.widget = widget
        self.arg = arg
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.screen = screen

    def copy(self):
        return Focus(
            self.widget,
            self.arg,
            self.x,
            self.y,
            self.w,
            self.h,
            self.screen)

    def __repr__(self):
        return "<Focus: %r %r (%r, %r, %r, %r) %r>" % (
            self.widget,
            self.arg,
            self.x,
            self.y,
            self.w,
            self.h,
            self.screen)

    def inside(self, rect):
        minx, miny, w, h = rect

        maxx = minx + w
        maxy = miny + h

        if self.x is None:
            return False

        if (minx <= self.x < maxx) and (miny <= self.y < maxy) and (minx <= self.x + self.w < maxx) and (
                miny <= self.y + self.h < maxy):
            return True

        return False


argument = None
screen_of_focused = None
screen_of_focused_names = set()
screen_of_last_focused_names = set()
grab = None
default_focus = None
focus_type = "mouse"
pending_focus_type = "mouse"
tooltip = None
last_tooltip = None
override = None


def set_focused(widget, arg, screen):
    global argument
    global screen_of_focused
    global screen_of_focused_names
    global tooltip
    global last_tooltip
    global screen_of_last_focused_names

    argument = arg
    screen_of_focused = screen

    if screen is not None:
        screen_of_focused_names = {screen.screen_name[0], screen.tag}
    else:
        screen_of_focused_names = set()

    renpy.game.context().scene_lists.focused = widget

    renpy.display.tts.displayable(widget)

    if widget is None:
        new_tooltip = None
    else:
        new_tooltip = widget._get_tooltip()

    if tooltip != new_tooltip:
        tooltip = new_tooltip
        capture_focus("tooltip")
        renpy.exports.restart_interaction()

        if tooltip is not None:
            last_tooltip = tooltip
            screen_of_last_focused_names = screen_of_focused_names


def get_focused():
    return renpy.game.context().scene_lists.focused


def get_mouse():
    focused = get_focused()
    if focused is None:
        return None
    else:
        return focused.style.mouse


def get_tooltip(screen=None, last=False):
    if screen is None:
        if last:
            return last_tooltip
        else:
            return tooltip

    if last:
        if screen in screen_of_last_focused_names:
            return last_tooltip

    else:
        if screen in screen_of_focused_names:
            return tooltip

    return None


def set_grab(widget):
    global grab
    grab = widget

    renpy.exports.cancel_gesture()


def get_grab():
    return grab


focus_list = []


def take_focuses():
    global focus_list
    focus_list = []

    renpy.display.render.take_focuses(focus_list)

    global default_focus
    default_focus = None

    global grab

    grab_found = False

    for f in focus_list:
        if f.x is None:
            default_focus = f

        if f.widget is grab:
            grab_found = True

    if not grab_found:
        grab = None

    if (default_focus is not None) and (get_focused() is None):
        change_focus(default_focus, True)


def focus_coordinates():
    current = get_focused()

    for i in focus_list:
        if i.widget == current and i.arg == argument:
            return i.x, i.y, i.w, i.h

    return None, None, None, None


replaced_by = {}

modal_generation = 0


def mark_modal():
    global modal_generation
    modal_generation += 1


def before_interact(roots):
    global override
    global grab
    global modal_generation

    modal_generation = 0

    fwn = []

    def callback(f, n):
        fwn.append((f, n, renpy.display.screen._current_screen, modal_generation))

    for root in roots:
        try:
            root.find_focusable(callback, None)
        except renpy.display.layout.IgnoreLayers:
            pass

    namecount = {}

    fwn2 = []

    for fwn_tuple in fwn:

        f, n, screen, gen = fwn_tuple

        serial = namecount.get(n, 0)
        namecount[n] = serial + 1

        if f is None:
            continue

        f.full_focus_name = n, serial

        replaced_by[id(f)] = f

        fwn2.append(fwn_tuple)

    fwn = fwn2

    default = True

    replaced_by.pop(None, None)

    current = get_focused()
    current = replaced_by.get(id(current), current)
    old_current = current

    grab = replaced_by.get(id(grab), None)

    if override is not None:
        d = renpy.exports.get_displayable(base=True, *override)

        if (d is not None) and (current is not d) and not grab:
            current = d
            default = False

    override = None

    if current is not None:
        current_name = current.full_focus_name

        for f, n, screen, gen in fwn:

            if gen != modal_generation:
                continue

            if f.full_focus_name == current_name:
                current = f
                set_focused(f, argument, screen)
                break
        else:
            current = None

    if grab is not None:
        current = grab

    if (current is None) and renpy.display.interface.start_interact:

        defaults = []

        for f, n, screen, gen in fwn:
            if gen != modal_generation:
                continue

            if f.default:
                defaults.append((f.default, f, screen))

        if defaults:
            if len(defaults) > 1:
                defaults.sort(key=operator.itemgetter(0))

            _, f, screen = defaults[-1]

            current = f
            set_focused(f, None, screen)

    if current is None:
        set_focused(None, None, None)

    for f, n, screen, modal in fwn:
        if f is not current:
            renpy.display.screen.push_current_screen(screen)
            try:
                if (f is old_current) and renpy.config.always_unfocus:
                    f.unfocus(default=False)
                else:
                    f.unfocus(default=default)

            finally:
                renpy.display.screen.pop_current_screen()

    if current:
        renpy.display.screen.push_current_screen(screen_of_focused)
        try:
            current.focus(default=default)
        finally:
            renpy.display.screen.pop_current_screen()

    replaced_by.clear()


def change_focus(newfocus, default=False):
    rv = None

    if grab:
        return

    if newfocus is None:
        widget = None
    else:
        widget = newfocus.widget

    current = get_focused()

    if current is widget and (newfocus is None or newfocus.arg == argument):
        return rv

    global focus_type
    focus_type = pending_focus_type

    if current is not None:
        try:
            renpy.display.screen.push_current_screen(screen_of_focused)
            current.unfocus(default=default)
        finally:
            renpy.display.screen.pop_current_screen()

    current = widget

    if newfocus is not None:
        set_focused(current, newfocus.arg, newfocus.screen)
    else:
        set_focused(None, None, None)

    if widget is not None:
        try:
            renpy.display.screen.push_current_screen(screen_of_focused)
            rv = widget.focus(default=default)
        finally:
            renpy.display.screen.pop_current_screen()

    return rv


def clear_focus():
    change_focus(None)


def mouse_handler(ev, x, y, default=False):
    global pending_focus_type

    if grab:
        return

    if ev is not None:
        if ev.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
            return
        else:
            pending_focus_type = "mouse"

    try:
        new_focus = renpy.display.render.focus_at_point(x, y)
    except renpy.display.layout.IgnoreLayers:
        new_focus = None

    if new_focus is None:
        new_focus = default_focus

    return change_focus(new_focus, default=default)


def focus_extreme(xmul, ymul, wmul, hmul):
    max_focus = None
    max_score = -(65536 ** 2)

    for f in focus_list:

        if not f.widget.style.keyboard_focus:
            continue

        if f.x is None:
            continue

        score = (f.x * xmul +
                 f.y * ymul +
                 f.w * wmul +
                 f.h * hmul)

        if score > max_score:
            max_score = score
            max_focus = f

    if max_focus:
        return change_focus(max_focus)


def points_dist(x0, y0, x1, y1, xfudge, yfudge):
    return ((x0 - x1) * xfudge) ** 2 + \
           ((y0 - y1) * yfudge) ** 2


def horiz_line_dist(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    if bx0 <= ax0 <= ax1 <= bx1 or \
            ax0 <= bx0 <= bx1 <= ax1 or \
            ax0 <= bx0 <= ax1 <= bx1 or \
            bx0 <= ax0 <= bx1 <= ax1:
        return (ay0 - by0) ** 2

    if ax0 <= ax1 <= bx0 <= bx1:
        return points_dist(ax1, ay1, bx0, by0, renpy.config.focus_crossrange_penalty, 1.0)
    else:
        return points_dist(ax0, ay0, bx1, by1, renpy.config.focus_crossrange_penalty, 1.0)


def verti_line_dist(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    if by0 <= ay0 <= ay1 <= by1 or \
            ay0 <= by0 <= by1 <= ay1 or \
            ay0 <= by0 <= ay1 <= by1 or \
            by0 <= ay0 <= by1 <= ay1:
        return (ax0 - bx0) ** 2

    if ay0 <= ay1 <= by0 <= by1:
        return points_dist(ax1, ay1, bx0, by0, 1.0, renpy.config.focus_crossrange_penalty)
    else:
        return points_dist(ax0, ay0, bx1, by1, 1.0, renpy.config.focus_crossrange_penalty)


def focus_nearest(from_x0, from_y0, from_x1, from_y1,
                  to_x0, to_y0, to_x1, to_y1,
                  line_dist,
                  condition,
                  xmul, ymul, wmul, hmul):
    global pending_focus_type
    pending_focus_type = "keyboard"

    if not focus_list:
        return

    current = get_focused()

    if not current:

        for f in focus_list:

            if not f.widget.style.keyboard_focus:
                continue

            change_focus(f)
            return

        return

    for f in focus_list:
        if f.widget is current and f.arg == argument:
            from_focus = f
            break
    else:
        change_focus(focus_list[0])
        return

    if from_focus.x is None:
        focus_extreme(xmul, ymul, wmul, hmul)
        return

    fx0 = from_focus.x + from_focus.w * from_x0
    fy0 = from_focus.y + from_focus.h * from_y0
    fx1 = from_focus.x + from_focus.w * from_x1
    fy1 = from_focus.y + from_focus.h * from_y1

    placeless = None
    new_focus = None

    # a really big number.
    new_focus_dist = (65536.0 * renpy.config.focus_crossrange_penalty) ** 2

    for f in focus_list:

        if f is from_focus:
            continue

        if not f.widget.style.keyboard_focus:
            continue

        if f.x is None:
            placeless = f
            continue

        if not condition(from_focus, f):
            continue

        tx0 = f.x + f.w * to_x0
        ty0 = f.y + f.h * to_y0
        tx1 = f.x + f.w * to_x1
        ty1 = f.y + f.h * to_y1

        dist = line_dist(fx0, fy0, fx1, fy1,
                         tx0, ty0, tx1, ty1)

        if dist < new_focus_dist:
            new_focus = f
            new_focus_dist = dist

    new_focus = new_focus or placeless

    if new_focus:
        return change_focus(new_focus)


def focus_ordered(delta):
    global pending_focus_type
    pending_focus_type = "keyboard"

    placeless = None

    candidates = []
    index = 0

    current = get_focused()
    current_index = None

    for f in focus_list:

        if f.x is None:
            placeless = f
            continue

        if f.arg is not None:
            continue

        if not f.widget.style.keyboard_focus:
            continue

        if f.widget is current:
            current_index = index

        candidates.append(f)
        index += 1

    new_focus = None

    if current_index is None:
        if candidates:
            if delta > 0:
                new_focus = candidates[delta - 1]
            else:
                new_focus = candidates[delta]
    else:
        new_index = current_index + delta

        if 0 <= new_index < len(candidates):
            new_focus = candidates[new_index]

    new_focus = new_focus or placeless

    return change_focus(new_focus)


def key_handler(ev):
    map_event = renpy.display.behavior.map_event

    if renpy.game.preferences.self_voicing:
        if map_event(ev, 'focus_right') or map_event(ev, 'focus_down'):
            return focus_ordered(1)

        if map_event(ev, 'focus_left') or map_event(ev, 'focus_up'):
            return focus_ordered(-1)

    else:

        if map_event(ev, 'focus_right'):
            return focus_nearest(0.9, 0.1, 0.9, 0.9,
                                 0.1, 0.1, 0.1, 0.9,
                                 verti_line_dist,
                                 lambda old, new: old.x + old.w <= new.x,
                                 -1, 0, 0, 0)

        if map_event(ev, 'focus_left'):
            return focus_nearest(0.1, 0.1, 0.1, 0.9,
                                 0.9, 0.1, 0.9, 0.9,
                                 verti_line_dist,
                                 lambda old, new: new.x + new.w <= old.x,
                                 1, 0, 1, 0)

        if map_event(ev, 'focus_up'):
            return focus_nearest(0.1, 0.1, 0.9, 0.1,
                                 0.1, 0.9, 0.9, 0.9,
                                 horiz_line_dist,
                                 lambda old, new: new.y + new.h <= old.y,
                                 0, 1, 0, 1)

        if map_event(ev, 'focus_down'):
            return focus_nearest(0.1, 0.9, 0.9, 0.9,
                                 0.1, 0.1, 0.9, 0.1,
                                 horiz_line_dist,
                                 lambda old, new: old.y + old.h <= new.y,
                                 0, -1, 0, 0)
