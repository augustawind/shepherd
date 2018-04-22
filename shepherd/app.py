"""High-level application and UI logic."""
import curses
import sys
import textwrap
from collections import deque
from typing import NamedTuple

from shepherd import utils
from shepherd.world.point import Point

TURN_TICKS = 10


class Coordinates(NamedTuple):
    x: int
    y: int


class Rect(NamedTuple):
    origin: Coordinates
    width: int
    height: int


class Margins(NamedTuple):
    inner: Coordinates
    outer: Coordinates


class Spacing(NamedTuple):
    left: int
    right: int
    top: int
    bottom: int


class Dimensions(NamedTuple):
    rect: Rect
    padding: Spacing


class X:
    margin = Margins(
        inner=Coordinates(2, 1),
        outer=Coordinates(2, 0),
    )

    _row1_height = 25

    world = Dimensions(
        rect=Rect(
            origin=Coordinates(
                x=margin.outer.x,
                y=margin.outer.y,
            ),
            width=40,
            height=_row1_height,
        ),
        padding=Spacing(2, 2, 1, 1),
    )

    menu = Dimensions(
        Rect(
            origin=Coordinates(
                x=margin.outer.x + world.rect.width - 1 + margin.inner.x,
                y=margin.outer.y,
            ),
            width=40,
            height=_row1_height,
        ),
        padding=Spacing(2, 2, 1, 1),
    )

    width = world.rect.width + menu.rect.width + margin.inner.x - 1

    log = Dimensions(
        Rect(
            origin=Coordinates(
                x=margin.outer.x,
                y=margin.outer.y + _row1_height - 1 + margin.inner.y,
            ),
            width=width,
            height=10,
        ),
        padding=Spacing(1, 1, 1, 1),
    )

    height = _row1_height + log.rect.height + margin.inner.y


class App:

    def __init__(self, stdscr, world, focus=None):
        self.world = world
        self.player = world.player
        self.focus = focus or self.player.id

        self.ticks = 0

        self.stdscr = stdscr
        self.panels = utils.Namespace(
            world=WorldPanel(X.world),
            menu=MenuPanel(X.menu),
            log=LogPanel(X.log),
        )
        for panel in self.panels.values():
            panel.initscr()

        self.cmd = {
            b's': self.skip,
            b'^X': self.quit,
            b'h': self.move_player(Point(-1, 0)),
            b'j': self.move_player(Point(0, 1)),
            b'k': self.move_player(Point(0, -1)),
            b'l': self.move_player(Point(1, 0)),
        }

    def run(self):
        self.update()
        while True:
            try:
                self.handle_input()
                self.update_panel('log')
            except KeyboardInterrupt:
                pass

    def update(self):
        focus_info = self.world.get_entity_by_id(self.focus)
        for key in self.panels:
            self.update_panel(key, focus_info)
        curses.doupdate()

    def update_panel(self, panel_name, focus_info=None):
        focus_info = focus_info or self.world.get_entity_by_id(self.focus)
        self.panels[panel_name].update(self.world, focus_info)

    def handle_input(self):
        c = self.stdscr.getch()
        try:
            key = curses.keyname(c)
        except ValueError:
            key = c
        handler = self.cmd.get(key)
        if handler:
            handler()
            self.tick()

    def move_player(self, delta):
        def cmd():
            self.world.move_player(delta)
        return cmd

    def skip(self):
        pass

    def tick(self):
        self._tick()
        while self.ticks % TURN_TICKS != 0:
            self._tick()
        self.update()

    def quit(self):
        curses.endwin()
        print('Bye!')
        sys.exit(1)

    def _tick(self):
        self.world.tick()
        self.ticks += 1


class Panel:
    """A panel in the UI."""

    indent_level = 2

    def __init__(self, dimensions: Dimensions, has_border=True):
        self._win = None
        self._rect = dimensions.rect
        self._padding = dimensions.padding
        self._inner = Rect(
            origin=Coordinates(
                x=1 + self._padding.left,
                y=1 + self._padding.top,
            ),
            width=(self._rect.width - 2
                   - self._padding.left - self._padding.right),
            height=(self._rect.height - 2
                    - self._padding.top - self._padding.bottom),
        )

        self._has_border = has_border
        self._cursor = Coordinates(0, 0)

        self._textwrap = textwrap.TextWrapper(
            width=self._inner.width, replace_whitespace=False,
            break_long_words=True, break_on_hyphens=True,
            subsequent_indent=' ' * self.indent_level)

    def initscr(self):
        self._win = curses.newwin(self._rect.height, self._rect.width,
                                  self._rect.origin.y, self._rect.origin.x)

    def update(self, world, focus):
        """Draw the panel. Subclasses should override this."""
        if self._has_border:
            self._win.box()
        self._win.noutrefresh()


class WorldPanel(Panel):
    """The panel that displays the world."""

    def __init__(self, dimensions):
        super().__init__(dimensions, has_border=True)
        left, right = utils.halves(self._inner.width)
        top, bottom = utils.halves(self._inner.height)
        self._halves = Spacing(left, right, top, bottom)
        self._center = Coordinates(left, top)
        self._cursor = Coordinates(20, 10)

    def update(self, world, focus):
        """Draw the world."""
        self._win.clear()
        self.update_cursor(focus)
        lines = world.display_rows()
        self.draw_lines(lines)
        super().update(world, focus)

    def update_cursor(self, focus):
        self._cursor = Coordinates(focus.point.x, focus.point.y)

    def draw_lines(self, lines):
        base, width, height = self._inner
        world_origin = self.get_world_origin()
        drawing_origin = self.get_drawing_origin()
        lines = lines[world_origin.y:]
        lines = lines[:height - base.y - drawing_origin.y]
        for y, line in enumerate(lines):
            line = line[world_origin.x:]
            line = line[:width - base.x - drawing_origin.x]
            self._win.addstr(
                base.y + y + drawing_origin.y,
                base.x + drawing_origin.x,
                line,
            )

    def get_world_origin(self):
        return Coordinates(
            x=max(0, self._cursor.x - self._halves.left),
            y=max(0, self._cursor.y - self._halves.top),
        )

    def get_drawing_origin(self):
        return Coordinates(
            x=max(0, self._halves.left - self._cursor.x),
            y=max(0, self._halves.top - self._cursor.y)
        )


class TextPanel(Panel):

    smooth_truncate = True

    def draw_lines(self, lines, wrap=False):
        """Update a series of lines cut to fit the panel."""
        origin, width, height = self._inner
        lines = lines[self._cursor.y:]
        lines = lines[:height]

        y = 0
        for line in lines:
            line = line[self._cursor.x:]
            if wrap:
                for wrapped_line in self._textwrap.wrap(line):
                    y = self.draw_line(wrapped_line, y)
                    if y == height:
                        return
            else:
                if self.smooth_truncate:
                    line = textwrap.shorten(line, self._inner.width)
                else:
                    line = line[:self._inner.width]
                y = self.draw_line(line, y)
                if y == height:
                    return

    def draw_line(self, line, y):
        if y + 1 == self._inner.height:
            line = '...'
        self._win.addstr(y + self._inner.origin.y, self._inner.origin.x, line)
        return y + 1


class MenuPanel(TextPanel):
    """The panel that displays the side menu."""

    def update(self, world, focus):
        """Draw the focused entity's state and position."""
        self._win.clear()
        if focus:
            point, entity = focus
            lines = [
                self.mk_header(point, entity),
                '-' * self._inner.width,
            ]
            state_str = utils.linefmt(entity.get_state(), self.indent_level)
            lines.extend(state_str.splitlines())
            self.draw_lines(lines, wrap=True)
        else:
            self._win.addstr('n/a'.center(self._rect.width - 2))
        super().update(world, focus)

    def mk_header(self, point, entity):
        name = f'{entity.name} '
        xy = str(point)
        name = textwrap.shorten(name, self._inner.width - len(xy))
        return f'{name}{xy!s:>{self._inner.width - len(name)}}'


class LogPanel(TextPanel):
    """The panel that displays game logs."""

    smooth_truncate = False

    def __init__(self, dimensions):
        super().__init__(dimensions)
        self._messages = deque(maxlen=100)
        self._messages.appendleft('Welcome to Worldbuilder.')

    def update(self, world, focus):
        # self._messages.extendleft(world.flush_messages())
        self.draw_lines(list(self._messages))
        super().update(world, focus)

    def draw_line(self, line, y):
        line = line[:self._inner.width]
        self._win.addstr(y + self._inner.origin.y, self._inner.origin.x, line)
        return y + 1
