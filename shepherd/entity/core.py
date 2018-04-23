"""Core logic for all Entities in the world."""
import abc
import enum
import pprint
import uuid
import warnings
from typing import Callable, TypeVar

import cerberus

from shepherd import utils
from shepherd.world.point import Point

__all__ = ['Size', 'Action', 'DoesNotExistError', 'Entity', 'InanimateObject',
           'Organism']

World = TypeVar('W')

ENTITY_ATTRS = ('properties', 'schema', 'state', 'categories', 'traversable')


class Size(enum.IntEnum):
    tiny = 1
    small = 2
    medium = 3
    large = 4
    giant = 5


class Action:

    def __init__(self, delay: int, func: Callable[[Point, World], int]):
        self.delay = delay
        self.func = func
        self._ticks = 0

    @staticmethod
    def empty():
        return Action(0, lambda origin, world: 0)

    def tick(self, origin, entity, world):
        self._ticks += 1
        if self._ticks >= self.delay:
            cost = self.func(origin, world)
            entity.mod_energy(-cost)
            return True
        return False


class EntityError(Exception):
    """Entity-related Exception."""

    def __init__(self, entity):
        super().__init__()
        self.entity = entity


class DoesNotExistError(EntityError):

    def __init__(self, entity, field_name, attr):
        super().__init__(entity)
        self.field_name = field_name
        self.attr = attr

    def __str__(self):
        return f'{self.entity} has no {self.field_name} "{self.attr}"'


class PropertyValidationError(EntityError):

    def __init__(self, entity, errors):
        super().__init__(entity)
        self.errors = errors

    def __str__(self):
        return '\n'.join((
            f'Property validation failed for {self.entity}:',
            pprint.pformat(self.errors, indent=2),
        ))


class Entity(metaclass=abc.ABCMeta):
    player_controlled = False

    def __init__(self, properties, schema=None, state=None, categories=None,
                 traversable=False):
        self._id = uuid.uuid4()
        self._ticks = 0
        self._action = None

        self._categories = self._mk_categories(categories)
        self._traversable = traversable

        self._schema = dict(
            size={
                'type': 'integer',
                'required': True,
                'min': 1,
                'max': 5,
            },
            mass={
                'type': 'integer',
                'required': True,
                'min': 1,
                'max': 20,
            },
            stamina={
                'type': 'integer',
                'min': 1,
                'max': 100,
                'default': 20,
            },
            resistance={
                'type': 'integer',
                'min': 0,
                'max': 100,
                'default': 1,
            },
            agility={
                'type': 'integer',
                'min': 0,
                'max': 30,
                'default': 0,
            },
        )
        self._schema.update(schema or {})
        self.validator = cerberus.Validator(self._schema)

        properties = self.validate(properties)
        self._properties = self._mk_properties(properties)

        self._state = dict(
            health=self.p.stamina,
            intact=True,
        )
        self._state.update(state or {})

    @utils.classproperty
    @abc.abstractmethod
    def name(cls) -> str:
        """Entity's name."""

    @utils.classproperty
    @abc.abstractmethod
    def char(cls) -> str:
        """Entity's display char."""

    @abc.abstractmethod
    def next_action(self, origin: Point, world: World) -> Action:
        """Return the next Action this Entity will take."""

    def validate(self, properties):
        properties = self.validator.normalized(properties)
        if properties is None or not self.validator.validate(properties):
            raise PropertyValidationError(
                entity=self, errors=self.validator.errors)
        return properties

    def _mk_properties(self, properties):
        def error(_, attr):
            return DoesNotExistError(self, 'Property', attr)
        cls = type('Properties', (utils.FixedNamespace,), dict(error=error))
        return cls(properties or ())

    def _mk_categories(self, categories):
        def error(_, attr):
            return DoesNotExistError(self, 'Category', attr)
        cls = type('Categories', (utils.FixedNamespace,), dict(error=error))
        return cls(categories or ())

    def __hash__(self):
        return hash(self._id)

    def __str__(self):
        return f'Entity(name={self.name})'

    @property
    def id(self):
        return self._id

    @property
    def properties(self):
        return self._properties
    p = properties

    @property
    def categories(self):
        return self._categories

    @property
    def traversable(self):
        return self._traversable

    def get_state(self):
        return self._state.copy()

    def get_state_val(self, key):
        return self._state[key]

    def tick(self, origin, world):
        self._ticks += 1
        if not self._action:
            self._action = self.next_action(origin, world)

        done = self._action.tick(origin, self, world)
        if done:
            self._action = None
        return done

    def is_intact(self) -> bool:
        return self._state['intact']

    def mod_health(self, amount: int) -> bool:
        if not self.is_intact():
            warnings.warn("attempted to mod health on non-intact entity")
            return None

        amount = amount * ((100 - self.p.resistance) / 100)
        target = self._state['health'] + amount
        health = utils.bounded(target, 0, self.p.stamina)
        self._state['health'] = health

        if health == 0:
            self._state['intact'] = False
            return False
        return True

    def mod_energy(self, amount: int) -> bool:
        return True


class InanimateObject(Entity):
    """An inanimate object."""


class Organism(Entity):

    def __init__(self, properties, schema=None, state=None, *args, **kwargs):
        schema = utils.merge(
            schema,
            metabolism={
                'type': 'integer',
                'min': 0,
                'max': 30,
                'default': 10,
            },
            regeneration={
                'type': 'integer',
                'min': 0,
                'max': 30,
                'default': 10,
            },
        )

        state = utils.merge(
            state,
            energy=100,
            conscious=True,
        )

        super().__init__(properties, schema, state, *args, **kwargs)

    def tick(self, origin, world):
        super().tick(origin, world)
        if self._ticks % 10 == 0:
            self.mod_energy(-self.p.metabolism / 10)
            self.mod_health(self.p.regeneration / 10)

    def is_conscious(self) -> bool:
        return self._state['conscious']

    def mod_energy(self, amount: int) -> bool:
        if not self.is_conscious():
            # TODO: regain consciousness attempts (a la D&D death saves)
            return None

        energy = utils.bounded(self._state['energy'] + amount, 0, 100)
        self._state['energy'] = energy
        if energy == 0:
            self._state['conscious'] = False
            return False
        return True


class Final:
    """Make this the first superclass of concrete, instantiatable Entities."""

    properties = None
    schema = None
    state = None
    categories = None
    traversable = False

    def __init__(self, **kwargs):
        for attr in ENTITY_ATTRS:
            default = getattr(self, attr)
            kwargs[attr] = utils.merge(default, kwargs[attr])
        super().__init__(**kwargs)
