from uuid import UUID

from shepherd.entity.bases import Move
from shepherd.entity.core import Action, Final, Organism, Size

PLAYER_ID = UUID('00000000-0000-0000-0000-000000000000')


class Player(Final, Move, Organism):

    player_controlled = True
    name = 'shepherd'
    char = '@'

    properties = dict(
        size=Size.medium,
        mass=5,
        stamina=100,
        resistance=10,
        agility=10,

        metabolism=10,
        regeneration=10,

        move_cost=10,
        move_delay=10,
    )

    categories = dict(
        organic=True,
        skin='fleshy',
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._id = PLAYER_ID

    def next_action(self, origin, world):
        return Action.empty()
