"""Entity base classes that provide common functionality."""
import math
import random
import warnings

from shepherd import utils
from shepherd.entity.core import Action, Entity
from shepherd.world.point import Point


class Move:

    def __init__(self, properties, schema=None, state=None, *args, **kwargs):
        schema = utils.merge(
            schema,
            move_delay={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 10,
            },
            move_cost={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 10,
            },
        )

        state = utils.merge(
            state,
            dir=Point.random(-1, 1, -1, 1),
        )

        super().__init__(properties, schema, state, *args, **kwargs)

    def move(self) -> Action:
        return Action(self.p.move_delay, self.execute_move)

    def change_dir(self, dir_: Point):
        """Manually change the direction of motion on the Entity."""
        self.state['dir'] = dir_.to_dir()

    def execute_move(self, origin, world) -> int:
        """Move in the set direction. If a cell is occupied, just give up."""
        dest = origin + self.state['dir']
        if world.get_cell(dest).occupant:
            return 0
        world.move(self.id, origin, dest)
        return self.p.move_cost


class AutoMove(Move):

    def __init__(self, properties, schema=None, state=None, *args, **kwargs):
        schema = utils.merge(
            schema,
            move_prob={
                'type': 'integer',
                'min': 0,
                'max': 100,
                'default': 100,
            },
            pivot_prob={
                'type': 'integer',
                'min': 0,
                'max': 100,
                'default': 0,
            },
        )

        super().__init__(properties, schema, state, *args, **kwargs)

    def execute_move(self, origin, world):
        if self.p.move_prob <= random.random() * 100:
            return 0

        dest = self.choose_dest(origin, world)
        if not dest:
            return 0

        self.state['dir'] = dest - origin
        world.move(self.id, origin, dest)
        return self.p.move_cost

    def choose_dest(self, origin: Point, world) -> Point:
        traversable_points = world.view_traversable(origin, 1)
        if not traversable_points:
            warnings.warn("no adjacent tiles are traversable")
            return None

        if self.p.pivot_prob > random.random() * 100:
            dest = random.choice(traversable_points)
        else:
            dest = origin + self.state['dir']
            if dest not in traversable_points:
                dest = random.choice(traversable_points)

        return dest


class Sense:

    def __init__(self, properties, schema=None, state=None, *args, **kwargs):
        properties.update(
            move_prob=100,
            pivot_prob=0,
        )

        schema = utils.merge(
            schema,
            tracking={
                'type': 'dict',
                'required': True,
                'empty': False,
                'keyschema': {
                    'type': 'string',
                    'empty': False,
                },
                'valueschema': {
                    'type': 'dict',
                    'keyschema': {
                        'type': 'string',
                        'empty': False,
                    },
                },
            },
            sensitivity={
                'type': 'integer',
                'required': True,
                'min': 1,
            },
            rescan_prob={
                'type': 'integer',
                'min': 0,
                'max': 100,
                'default': 0,
            }
        )

        state = utils.merge(
            state,
            sensing=dict(
                point=None,
                entity=None,
                priority=0,
            )
        )

        super().__init__(properties, schema, state, *args, **kwargs)

    def sense(self, task: str, origin: Point, world) -> bool:
        if self.p.rescan_prob <= random.random() * 100:
            return self.scan(task, origin, world)

    def scan(self, task: str, origin: Point, world) -> bool:
        changed = False

        for point in world.view(origin, self.p.sensitivity):
            cell = world.get_cell(point)
            for entity in cell:
                if self.evaluate_entity(task, point, entity):
                    changed = True

        return changed

    def evaluate_entity(self, task: str, point: Point, entity: Entity) -> bool:
        targets = self.matching_categories(task, entity)

        if targets:
            sense_priority = self.state['sensing']['priority']
            priority = len(targets)
            if utils.gt_or_random_eq(priority, sense_priority):
                self.state['sensing'].update(
                    point=point,
                    entity=entity,
                    priority=priority,
                )
                return True

        return False

    def matching_categories(self, task: str, entity: Entity) -> dict:
        return utils.dict_subset(entity.categories, self.p.tracking[task])

    def get_focus(self) -> (Point, Entity):
        sensing = self.state['sensing']
        return sensing['point'], sensing['entity']


class Seek(Sense, Move):

    def seek(self, task: str, origin: Point, world) -> Action:
        changed = self.sense(task, origin, world)
        if changed:
            point, entity = self.get_focus()
        else:
            # TODO: log this somewhere (stdlib logging?)
            return Action.empty()

        self.state['dir'] = (point - origin).to_dir()
        return self.move()


class Attack:

    def __init__(self, properties, schema=None, state=None, *args, **kwargs):
        schema = utils.merge(
            schema,
            attack_name={
                'type': 'string',
                'required': True,
                'empty': False,
            },
            attack_strength={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 1,
            },
            attack_skill={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 1,
            },
            attack_delay={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 10,
            },
            attack_cost={
                'type': 'integer',
                'min': 1,
                'max': 30,
                'default': 10,
            },
        )

        super().__init__(properties, schema, state, *args, **kwargs)

    def attack(self, dest: Point, target: Entity) -> Action:

        def execute(origin, world):
            evasion = target.p.agility
            hit_chance = (
                min(0, (evasion - self.p.attack_skill) * 3)
                + random.randint(0, 5)
            )

            if not utils.roll(hit_chance):
                warnings.warn("miss!")
                return self.p.attack_cost

            maxv = math.floor(self.p.attack_strength / 8)
            minv = maxv - math.ceil(maxv / 2)
            power = self.p.attack_strength + random.randint(-minv, maxv)
            power = max(1, power)
            defense = (100 - target.p.resistance) / 100
            damage = power * defense

            target.mod_health(-damage)
            return self.p.attack_cost

        return Action(self.p.attack_delay, execute)


class Hunt(Attack, Seek):

    def hunt(self, origin: Point, world) -> Action:
        self.scan('hunt', origin, world)
        point, entity = self.get_focus()
        if point and origin.is_adjacent(point):
            return self.attack(point, entity)
        else:
            return self.move()
