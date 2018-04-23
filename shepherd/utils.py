"""Miscellaneous utilities."""
import itertools
import math
import random
from collections import (
    Iterable,
    Mapping,
    MutableSequence,
    Set,
)
from functools import partial


class classproperty:
    """Like the @property decorator, but for class methods."""

    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self


class Namespace(dict):
    """A dict that supports dot-access on its items."""

    def __getstate__(self):
        return self.copy()

    def __setstate__(self, state):
        self.update(state)

    def __getattr__(self, attr):
        return self.__getitem__(attr)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)


class FixedNamespace(Namespace):
    """Locked Namespace with customizable error handling.

    Attrs cannot be added or deleted, but attrs defined on init can be updated.
    """

    error = AttributeError

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            raise self.error(item)

    def __setitem__(self, key, value):
        self.__getitem__(key)
        return super().__setitem__(key, value)

    def __delitem__(self, key):
        raise self.error(key)


def bounded(value, min_bound, max_bound):
    """Return the given value, or the closest value within the given bounds."""
    return max(min_bound, min(max_bound, value))


def gt_or_random_eq(x0, x1):
    """Return whether x0 > x1, returning a random boolean if they're equal."""
    if x0 > x1:
        return True
    if x0 == x1:
        return bool(random.randint(0, 1))
    return False


def dict_subset(d0: dict, d1: dict) -> dict:
    """Return a dict of all items in ``d0`` that are also in ``d1``."""
    return dict(item for item in d0.items() if item in d1.items())


def merge(base, *args, _depth=0, **kwargs):
    """Compose one or more mappings with kwargs.

    Args are merged into ``base`` sequentially, each overriding previous keys.
    kwargs are merged in last. If ``base`` is None, a new dict is created. The
    result is returned whether a new mapping was created or not.

    Args:
        base (Mapping): The base mapping.
        *args: Additional mappings.
        _depth (int): The depth to merge nested dicts.
        **kwargs: Key/value pairs.

    Returns:
        The ``base`` mapping. If it was None, the newly created mapping is
        returned. Otherwise it's the same mapping that was passed in.
    """
    if base is None:
        base = {}
    for arg in itertools.chain(args, (kwargs,)):
        if not arg:
            continue
        for key, val in arg.items():
            if _depth != 0 and isinstance(val, Mapping):
                base_val = base.get(key)
                if isinstance(base_val, Mapping):
                    base[key] = merge(base_val, val, _depth=_depth - 1)
                    continue
            base[key] = val
    return base


def setdefault(value, default, cls=None, merge_lists=False, merge_sets=False,
               merge_dicts=False, depth=1):
    """Transform ``value`` by applying some rules with ``default``.

    The following rules are applied:
        1. If ``value`` is None, return ``default``.
        2. If ``default`` is None, return ``value``.
        3. If ``merge_dicts`` is True, merge mapping types.
        4. If ``merge_lists`` is True, merge mutable sequence types.
        R. If ``merge_sets`` is True, merge set types.

    Args:
        value: The value to be transformed.
        default: The default value.
        cls (type): Desired return type. If possible, the transformed value
            will be returned as an instance of ``cls``. If is omitted or None,
            the return type will be the same as ``value``.
        merge_lists (bool): If ``value`` is a mutable sequence, concatenate
            and return ``default`` + ``value``.
        merge_sets (bool): If ``value`` is a set type, return its union with
            ``default``.
        merge_dicts (bool): If ``value`` is a mapping type, return ``value``
            plus any items from ``default`` whose keys are not in ``value``.
        depth (int): If ``merge_dicts`` is enabled, this sets the max depth
            of nested mappings that will be merged. If -1, no limit will be
            enforced.

    Attributes:
        setdefault.merge_all (function): Run with all merge flags enabled.
        setdefault.merge_dicts (function): Run with `merge_dicts` enabled.
        setdefault.merge_lists (function): Run with `merge_lists` enabled.
        setdefault.merge_sets (function): Run with `merge_sets` enabled.
    """
    value_cls = None

    if value is not None and default is not None:
        value_cls = type(value)
        if merge_dicts:
            value = _setdefault_dict(value, default, depth)
        if merge_lists:
            value = _setdefault_list(value, default)
        if merge_sets:
            value = _setdefault_set(value, default)
        value = value_cls(value)

    elif value is None:
        if default is None:
            return None
        value = default

    if cls:
        return cls(value)
    elif value_cls:
        return value_cls(value)
    return value


def _setdefault_dict(value, default, depth):
    if isinstance(value, Mapping):
        return merge(None, default, value, _depth=depth)
    return value


def _setdefault_set(value, default):
    if isinstance(value, Set):
        return value | default
    return value


def _setdefault_list(value, default):
    if isinstance(value, MutableSequence):
        return [*default, *value]
    return value


def _setdefault_all(value, default, cls=None):
    """Call ``setdefault`` but transform set types and mutable sequences.

    Additional transformations:
    """
    return setdefault(value, default, cls, merge_dicts=True, merge_sets=True,
                      merge_lists=True)


setdefault.merge_all = _setdefault_all
setdefault.merge_dicts = partial(setdefault, merge_dicts=True)
setdefault.merge_lists = partial(setdefault, merge_lists=True)
setdefault.merge_sets = partial(setdefault, merge_sets=True)


def sign_of(n):
    """Return the sign of ``n`` as one of -1, 0, or 1."""
    if n < 0:
        return -1
    if n > 0:
        return 1
    return 0


def roll(p: int, limit: int = 100) -> bool:
    """Check ``p`` against a random number."""
    return p > random.random() * limit


def linefmt(v, indent=2, level=0):
    """Format the given value.

    This applies the given ``indent``, and formats compound types by placing
    each entry on a separate line.
    """
    tab = ' ' * indent * level
    if isinstance(v, Mapping):
        lines = []
        for key, val in v.items():
            if is_compound(val):
                lines.append(f'{tab}{key}:')
                lines.append(linefmt(val, indent, level + 1))
            else:
                lines.append(f'{tab}{key}: {val}')
        return '\n'.join(lines)
    if isinstance(v, Iterable) and not isinstance(v, str):
        return '\n'.join(f'{tab}{x}' for x in v)
    return f'{tab}{v}'


def is_compound(v):
    """Return whether the given value is a compound type."""
    return isinstance(v, Iterable) and not isinstance(v, str)


def halves(n: int) -> (int, int):
    """Divide ``n`` into 2 integers as close to equal as possible."""
    x = math.floor(n / 2)
    y = x + (n - (x * 2))
    return x, y


def expandkeys(d: Mapping) -> Mapping:
    """Expand a mapping with iterable keys to have entry per item."""
    return {k: val for keys, val in d.items() for k in keys}
