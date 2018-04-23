"""Core spatial logic."""
from collections import OrderedDict, defaultdict
from typing import Iterable, Iterator, NamedTuple
from uuid import UUID

from shepherd import utils
from shepherd.entity.core import Entity
from shepherd.player import Player
from shepherd.world.exceptions import (
    EntityNotFoundError,
    OutOfBoundsError,
    CellIsOccupiedError,
)
from shepherd.world.point import Point

__all__ = ['Cell', 'World']


class EntityInfo(NamedTuple):
    point: Point
    entity: Entity


class Cell:
    """The physical space at a specific Point in the World."""

    def __init__(self, point: Point, entities: Iterable[Entity] = ()):
        self.point = point
        self._floor = OrderedDict()
        self.occupant = None
        for entity in entities:
            self.add(entity)

    def __len__(self):
        return len(self._floor) + bool(self.occupant)

    def __iter__(self) -> Iterator[Entity]:
        yield from iter(self._floor.values())
        if self.occupant:
            yield self.occupant

    def __getitem__(self, i: int) -> Entity:
        return tuple(self)[i]

    def get(self, entity_id: str) -> Entity:
        if self.occupant and id == self.occupant.id:
            return self.occupant
        return self._floor[entity_id]

    def find(self, **properties) -> Entity:
        for entity in self:
            if utils.dict_subset(properties, entity.properties):
                return entity
        return None

    def add(self, entity: Entity):
        if not entity.traversable:
            if self.occupant:
                raise CellIsOccupiedError(self.point, entity)
            else:
                self.occupant = entity
        else:
            self._floor[entity.id] = entity

    def pop(self, entity_id: str) -> Entity:
        if self.occupant and entity_id == self.occupant.id:
            entity = self.occupant
            self.occupant = None
        else:
            try:
                entity = self._floor.pop(entity_id)
            except KeyError:
                raise EntityNotFoundError(self.point, entity_id)
        return entity


class World:
    """A container for Cells and Entities."""

    EMPTY_CHAR = ' '

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = []
        for y in range(height):
            self.grid.append([])
            for x in range(width):
                self.grid[y].append(Cell(Point(x, y)))

        # name -> set[id]
        self.entity_name_map = defaultdict(set)
        # id -> EntityInfo
        self.entity_id_map = dict()

        self.player = None
        self.player_pos = None

        self.messages = []

    @staticmethod
    def from_legend(legend: dict, *layers: list):
        """Construct a world from a grid and a legend.

        Args:
            grid (Sequence): A 2-D sequence of chars, like a list of strings.
                This represents the physical layout of the World.
            legend (dict): A mapping of chars to Entity names.
                Each char in the grid will be looked up here.
            entities (dict, optional): A mapping of Entity names to classes.
                If not given, ``definitions.ENTITY_MAP`` will be used.

        Returns:
            World: The newly constructed World.
        """
        assert len(layers) >= 1, (
            'grid must have at least one layer'
        )
        world = World(len(layers[0][0]), len(layers[0]))
        for point, cell in world.iter_cells():
            for layer in layers:
                assert len(layer) >= 1, (
                    'layer must have at least one row'
                )
                char = layer[point.y][point.x]
                if char == World.EMPTY_CHAR:
                    continue

                entity = legend.get(char)
                assert entity, (
                    'char "%s" missing from legend' % char
                )
                world.add(point, entity())
        return world

    def tick(self):
        """Move the clock forward by one tick, updating all Entities."""
        for point, cell in self.iter_cells():
            for entity in cell:
                entity.tick(point, self)

    # Logging things

    def log(self, message: str):
        """Append a message to the World logs."""
        self.messages.append(message)

    def flush_messages(self) -> list:
        """Flush all messages from the World logs, returning them."""
        messages = self.messages.copy()
        self.messages.clear()
        return messages

    # Displaying things

    def display_rows(self) -> list:
        """Return a str representation of each row of the World."""
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                entity = self.get_entity(Point(x, y))
                if entity:
                    char = entity.char
                else:
                    char = self.EMPTY_CHAR
                row.append(char)
            rows.append(''.join(row))
        return rows

    # Querying things

    def in_bounds(self, point: Point) -> bool:
        """Return whether the given point is in bounds."""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def traversable(self, point: Point) -> bool:
        """Return whether the Cell at the given point is traversable."""
        if not self.in_bounds(point):
            return False
        for entity in self.get_cell(point):
            if not entity.traversable:
                return False
        return True

    # Retrieving things

    def get_cell(self, point: Point) -> Cell:
        """Get the Cell at the given Point."""
        try:
            return self.grid[point.y][point.x]
        except IndexError:
            raise OutOfBoundsError(point)

    def get_entity(self, point: Point, z: int=-1) -> Entity:
        """Get the Entity at the given Point and z-index."""
        try:
            return self.get_cell(point)[z]
        except IndexError:
            return None

    def iter_cells(self) -> Iterator:
        """Yield (Point, Cell) pairs for every Cell in the world."""
        for y in range(self.height):
            for x in range(self.width):
                yield Point(x, y), self.grid[y][x]

    def view(self, origin: Point, radius: int) -> [Point]:
        """Return all Points within some radius of an origin."""
        points = origin.in_radius(radius)
        return tuple(v for v in points if self.in_bounds(v))

    def view_traversable(self, origin: Point, radius: int) -> [Point]:
        """Like ``view``, but only returns Points which are traversable."""
        points = origin.in_radius(radius)
        return tuple(v for v in points if self.traversable(v))

    def get_entity_by_id(self, entity_id: UUID) -> EntityInfo:
        """Return the (Vector, Entity) of the given UUID."""
        return self.entity_id_map[entity_id]

    def get_entities_by_name(self, name: str) -> {EntityInfo}:
        """Return a set of (Vector, Entity) for all Entities named ``name``."""
        return {self.get_entity_by_id(id) for id in self.entity_name_map[name]}

    # Updating things

    def add(self, point: Point, entity: Entity):
        """Add the given Entity to the Cell at the given Point."""
        if entity.is_player:
            self.player = entity
            self.player_pos = point
        else:
            self.entity_name_map[entity.name].add(entity.id)
        self.entity_id_map[entity.id] = EntityInfo(point, entity)
        self.get_cell(point).add(entity)

    def remove(self, point: Point, entity_id: UUID) -> Entity:
        """Remove and return the specified Entity at the given Point."""
        info = self.entity_id_map.pop(entity_id)
        if info.entity.is_player:
            self.entity_name_map[info.entity.name].remove(entity_id)
        return self.get_cell(point).pop(entity_id)

    def move(self, entity_id: UUID, src: Point, dest: Point) -> Entity:
        """Move the specified Entity from ``src`` to ``dest`` and return it."""
        entity = self.remove(src, entity_id)
        self.add(dest, entity)
        if entity.is_player:
            self.player_pos = dest
        return entity
