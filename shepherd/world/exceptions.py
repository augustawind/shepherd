from uuid import UUID

from shepherd.world.point import Point

__all__ = ['WorldError', 'EntityNotFoundError', 'OutOfBoundsError',
           'CellIndexError', 'CellIsOccupiedError']


class WorldError(Exception):
    """Raised when something goes wrong performing a World operation."""

    def __init__(self, point: Point):
        super().__init__()
        self.point = point

    def fmt_cell(self) -> str:
        return f'Cell{self.point.fmt_xy()}'


class EntityNotFoundError(WorldError):
    """Raised when an Entity is not found at specific Point."""

    def __init__(self, point: Point, entity_id: UUID):
        super().__init__(point)
        self.entity_id = entity_id

    def __str__(self):
        return f'Entity with id "{self.entity_id}" not found at {self.point}'


class OutOfBoundsError(WorldError):
    """Raised when a World is queried for an out-of-bounds Point."""

    def __str__(self):
        return f'{self.point} is out of bounds'


class CellIndexError(WorldError):
    """Raised when a Cell is queried for an out-of-bounds z-level."""

    def __init__(self, point: Point, z: int):
        super().__init__(point)
        self.depth = z

    def __str__(self):
        return f'{self.fmt_cell()} has no index "{self.depth}"'


class CellIsOccupiedError(WorldError):
    """Raised when placing a non-traversable Entity in an occupied Cell."""

    def __init__(self, point: Point, entity):
        super().__init__(point)
        self.entity = entity

    def __str__(self):
        return f'cannot add {self.entity}:' \
               f' {self.fmt_cell()} is already occupied'
