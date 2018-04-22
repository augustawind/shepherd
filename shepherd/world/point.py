"""X, Y coordinates."""
import random

from shepherd import utils

__all__ = ['Point']


class Point:
    """A point in 2-dimensional space."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def random(cls, x0, x1, y0, y1):
        """Return a Point with random coordinates between the given limits."""
        return Point(random.randint(x0, y0), random.randint(y0, y1))

    def __str__(self):
        return f'Point({self.x}, {self.y})'

    def fmt_xy(self) -> str:
        """Return the Point as an (x, y) str."""
        return f'({self.x}, {self.x})'

    def __eq__(self, other):
        try:
            return self.x == other.x and self.y == other.y
        except AttributeError:
            raise TypeError(f'cannot compare {type(self)} with {type(other)}')

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)

    def in_radius(self, radius: int) -> ['Point']:
        """Return a list of Points in all directions within ``radius``."""
        points = []
        for y in range(self.y - radius, self.y + radius + 1):
            for x in range(self.x - radius, self.x + radius + 1):
                vec = Point(x, y)
                if vec != self:
                    points.append(vec)
        return points

    def to_dir(self) -> 'Point':
        """Return the Point where each coordinate represents a direction.

        The new Point takes the sign of this Point's x and y, respectively.
        """
        return Point(utils.sign_of(self.x), utils.sign_of(self.y))

    def is_adjacent(self, other: 'Point') -> bool:
        """Return True if the Points are adjacent to each other."""
        return (
            self != other
            and abs(self.x - other.x) <= 1
            and abs(self.y - other.y) <= 1
        )
