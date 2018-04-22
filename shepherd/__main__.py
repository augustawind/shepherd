"""Run the app."""
import curses
import sys

from shepherd.app import App
from shepherd.entities import (
    StonePillar,
    Grass,
    WanderingShrub,
    GluttonousShambler,
)
from shepherd.player import Player
from shepherd.world.world import World

LEGEND = {
    'I': StonePillar,
    '"': Grass,
    'h': WanderingShrub,
    'M': GluttonousShambler,
    '@': Player,
}

LAYERS = [[
    'IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII',
    'I""                                    I',
    'I""""                                  I',
    'I"""  h                                I',
    'I"  "             @                    I',
    'I   h M                                I',
    'I     " "                              I',
    'I  """ ""                              I',
    'I     """                              I',
    'I     """          "                   I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'I     """                              I',
    'IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII',
]]


def main(stdscr):
    world = World.from_legend(LEGEND, *LAYERS)
    app = App(stdscr, world)
    app.run()


if __name__ == '__main__':
    curses.wrapper(main)
    sys.exit(0)
