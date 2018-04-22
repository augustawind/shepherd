from shepherd.entity.bases import (
    AutoMove,
    Hunt,
    Move,
)
from shepherd.entity.core import (
    Action,
    InanimateObject,
    Organism,
    Size,
)


class StonePillar(InanimateObject):

    name = 'stone pillar'
    char = 'I'

    def __init__(self):
        super().__init__(
            properties=dict(
                size=Size.giant,
                mass=20,
                stamina=100,
                resistance=100,
            ),
            categories={
                'organic': False,
                'exterior': 'hard',
            },
            traversable=False,
        )

    def next_action(self, origin, world):
        return Action.empty()


class Grass(Organism):

    name = 'grass'
    char = '"'

    def __init__(self):
        super().__init__(
            properties=dict(
                size=Size.tiny,
                mass=2,
                stamina=10,
                resistance=0,

                metabolism=0,
                regeneration=0,
            ),
            categories={
                'organic': True,
                'exterior': 'fibrous',
            },
            traversable=True,
        )

    def next_action(self, origin, world):
        return Action.empty()


class WanderingShrub(AutoMove, Organism):

    name = 'wandering shrub'
    char = 'h'

    def __init__(self):
        super().__init__(
            properties=dict(
                size=Size.medium,
                mass=4,
                stamina=100,
                resistance=20,
                agility=1,
                metabolism=0,
                regeneration=3,
                move_delay=10,
                move_cost=10,
                move_prob=85,
                pivot_prob=50,
            ),
            categories={
                'organic': True,
                'exterior': 'fibrous',
            },
            traversable=False,
        )

    def next_action(self, origin, world):
        return self.move()


class GluttonousShambler(Hunt, AutoMove, Organism):

    name = 'gluttonous shambler'
    char = 'M'

    def __init__(self):
        super().__init__(
            properties=dict(
                size=Size.large,
                mass=4,
                stamina=85,
                resistance=35,
                agility=10,

                metabolism=20,
                regeneration=5,

                move_delay=10,
                move_cost=5,
                tracking={
                    'hunt': {
                        'organic': True,
                        'exterior': 'fleshy',
                    },
                },
                sensitivity=8,
                rescan_prob=5,

                attack_name='slam',
                attack_skill=10,
                attack_strength=18,
                attack_delay=15,
                attack_cost=5,
            ),
            categories={
                'organic': True,
                'exterior': 'fleshy',
            },
            traversable=False,
        )

    def next_action(self, origin, world):
        return self.hunt(origin, world)
