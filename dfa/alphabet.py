from __future__ import annotations

from functools import total_ordering
from itertools import product
from typing import Hashable, FrozenSet, Union

import attr

Letter = Hashable


def _freeze(alphabet):
    if alphabet is None or isinstance(alphabet, SupAlphabet):
        return SupAlphabet()
    elif isinstance(alphabet, (ProductAlphabet, ExplicitAlphabet)):
        return alphabet
    return ExplicitAlphabet(alphabet)


def _lt_alphabet(left: Alphabet, right: Alphabet) -> bool:
    """Return if left is a strict subset of right."""
    if isinstance(left, SupAlphabet):
        return False
    elif isinstance(right, SupAlphabet):
        return True
    elif all(isinstance(x, ProductAlphabet) for x in [left, right]):
        return (left.left < right.left) and (left.right < right.right)
    return set(left) < set(right)


@attr.s(frozen=True, auto_attribs=True, order=False)
@total_ordering
class SupAlphabet:
    """Alphabet containing all other alphabets."""
    __lt__ = _lt_alphabet

    def __hash__(self):
        return hash(id(self))

    def __contains__(self, _):
        return True


@attr.s(frozen=True, auto_attribs=True, repr=False, order=False)
@total_ordering
class ProductAlphabet:
    """Implicit encoding of product alphabet."""
    left: Alphabet = attr.ib(converter=_freeze)
    right: Alphabet = attr.ib(converter=_freeze)

    __lt__ = _lt_alphabet

    def __hash__(self):
        return hash((self.left, self.right))

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


@attr.s(frozen=True, auto_attribs=True, eq=False)
@total_ordering
class ExplicitAlphabet:
    chars: FrozenSet[Letter] = attr.ib(converter=frozenset)

    __lt__ = _lt_alphabet

    def __hash__(self):
        return hash(self.chars)

    def __eq__(self, other):
        if isinstance(other, ExplicitAlphabet):
            return self.chars == other.chars
        return set(self) == set(other)

    def __iter__(self):
        return iter(self.chars)

    def __len__(self):
        return len(self.chars)

    def __contains__(self, elem):
        return elem in self.chars


Alphabet = Union[ExplicitAlphabet, ProductAlphabet, SupAlphabet]
