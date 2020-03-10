from __future__ import annotations

from functools import total_ordering
from itertools import product
from typing import Hashable, FrozenSet, Union

import attr


def _instances_of(kind, *args):
    return all(isinstance(x, kind) for x in args)


def _lt_alphabet(left: Alphabet, right: Alphabet) -> bool:
    """Return if left is a strict subset of right."""
    if isinstance(left, SupAlphabet):
        return False
    elif isinstance(right, SupAlphabet):
        return True
    elif _instances_of(ProductAlphabet, left, right):
        return (left.left < right.left) and (left.right < right.right)
    elif _instances_of(ExponentialAlphabet, left, right):
        return left.dim == right.dim and left.base < right.base

    return set(left) < set(right)


def _freeze(alphabet):
    if alphabet is None or isinstance(alphabet, SupAlphabet):
        return SupAlphabet()
    elif isinstance(alphabet, Alphabet.__args__):
        return alphabet
    return ExplicitAlphabet(alphabet)


Letter = Hashable


@attr.s(frozen=True, auto_attribs=True, eq=False, repr=False)
@total_ordering
class ExplicitAlphabet:
    """Alphabet defined by a set."""
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

    def __repr__(self):
        return repr(set(self.chars))


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


@attr.s(frozen=True, auto_attribs=True, eq=False, repr=False)
@total_ordering
class ExponentialAlphabet:
    """Product of base alphabet with itself dim times."""
    base: Alphabet = attr.ib(converter=_freeze)
    dim: int = attr.ib(default=1)

    @dim.validator
    def positive(self, _, value):
        assert value >= 0

    __lt__ = _lt_alphabet

    def __hash__(self):
        return hash((self.base, self.dim))

    def __contains__(self, elem):
        for i, e in enumerate(elem):         # Allowing elem to be a generator.
            if (i >= self.dim) or (e not in self.base):
                return False
        return i + 1 == self.dim

    def __repr__(self):
        return f"{self.base}^{self.dim}"

    def __len__(self):
        return self.dim * len(self.base)

    def __iter__(self):
        return product(*(self.dim*[self.base]))


Alphabet = Union[
    ExplicitAlphabet,
    ExponentialAlphabet,
    ProductAlphabet,
    SupAlphabet,
]
