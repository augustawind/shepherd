from uuid import UUID

from shepherd.entity.bases import Move
from shepherd.entity.core import Action, Organism, Size

PLAYER_ID = UUID('00000000-0000-0000-0000-000000000000')


class Player(Move, Organism):

    is_player = True
    name = 'shepherd'
    char = '@'

    def __init__(self, properties=None, ):
        super().__init__(
            properties=dict(
                size=Size.medium,
                mass=5,
                stamina=100,
                resistance=10,
                agility=10,

                metabolism=10,
                regeneration=10,

                move_cost=10,
                move_delay=10,
            ),
            categories=dict(
                organic=True,
                skin='fleshy',
            ),
            traversable=False,
        )
        self._id = PLAYER_ID

    def next_action(self, origin, world):
        return Action.empty()
