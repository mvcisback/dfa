from __future__ import annotations

from functools import total_ordering
from itertools import product
from typing import Hashable, FrozenSet, Union

import attr

Letter = Hashable


def _freeze(alphabet):
    if alphabet is None or isinstance(alphabet, SupAlphabet):
        return SupAlphabet()
    elif isinstance(alphabet, ProductAlphabet):
        return alphabet
    return frozenset(alphabet)


@attr.s(frozen=True, auto_attribs=True, eq=False)
@total_ordering
class SupAlphabet:
    """Alphabet containing all other alphabets."""
    def __hash__(self):
        return hash(id(self))

    def __contains__(self, _):
        return True

    def __lt__(self, other):
        return False

    def __eq__(self, other):
        return isinstance(other, SupAlphabet)


@attr.s(frozen=True, auto_attribs=True, repr=False, eq=False)
@total_ordering
class ProductAlphabet:
    """Implicit encoding of product alphabet."""
    left: Alphabet = attr.ib(converter=_freeze)
    right: Alphabet = attr.ib(converter=_freeze)

    def __hash__(self):
        return hash((self.left, self.right))

    def __eq__(self, other):
        return (self.left == other.left) and (self.right == other.right)

    def __lt__(self, other):
        return (self.left < other.left) and (self.right < other.right)

    def __contains__(self, elem):
        assert len(elem) == 2
        return (elem[0] in self.left) and (elem[1] in self.right)

    def __iter__(self):
        return product(self.left, self.right)

    def __repr__(self):
        left, right = map(
            lambda x: x if isinstance(x, SupAlphabet) else set(x),
            [self.left, self.right]
        )
        return f"{left} x {right}"

    def __len__(self):
        return len(self.left) * len(self.right)


Alphabet = Union[FrozenSet[Letter], ProductAlphabet, SupAlphabet]
