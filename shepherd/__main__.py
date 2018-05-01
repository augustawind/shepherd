"""Run the app."""
import curses
import sys

from shepherd.app import App
from shepherd.entities import (
    LargeRock,
    Grass,
    Sheep,
    Wolf,
)
from shepherd.player import Player
from shepherd.world.world import World

LEGEND = {
    'O': LargeRock,
    '"': Grass,
    'h': Sheep,
    '}': Wolf,
    '@': Player,
}

LAYERS = [[
    'OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO',
    'O""                                    O',
    'O""""                                  O',
    'O"""  h                                O',
    'O"  "             @                    O',
    'O   h }                                O',
    'O     " "                              O',
    'O  """ ""                              O',
    'O     """                              O',
    'O     """          "                   O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'O     """                              O',
    'OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO',
]]


def main(stdscr):
    world = World.from_legend(LEGEND, *LAYERS)
    app = App(stdscr, world)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)
    sys.exit(0)
