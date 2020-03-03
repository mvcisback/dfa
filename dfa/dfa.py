from __future__ import annotations

from functools import total_ordering
from itertools import product
from typing import Hashable, FrozenSet, Callable, Union

import attr
import funcy as fn


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


State = Hashable
Letter = Hashable
Alphabet = Union[FrozenSet[Letter], ProductAlphabet, SupAlphabet]


@attr.s(frozen=True, auto_attribs=True)
class DFA:
    """Represents a Discrete Finite Automaton or Moore Machine."""

    start: State
    _label: Callable[[State], Letter] = attr.ib(
        converter=fn.memoize
    )
    _transition: Callable[[State, Letter], State] = attr.ib(
        converter=fn.memoize
    )
    inputs: Alphabet = attr.ib(converter=_freeze, default=SupAlphabet())
    outputs: Alphabet = attr.ib(converter=_freeze, default={True, False})

    def run(self, *, start=None):
        """Creates a co-routine that simulates the automata:
            - Takes in characters from the input alphabet.
            - Yields states.
        """
        state = self.start if start is None else start

        while True:
            char = yield state
            assert (self.inputs is None) or (char in self.inputs)
            state = self._transition(state, char)

    def trace(self, word, *, start=None):
        """Creates a generator that yields the sequence of states that
        results from reading the word.
        """
        machine = self.run(start=start)

        for char in fn.concat([None], word):
            state = machine.send(char)
            yield state

    def transition(self, word, *, start=None):
        """Returns the state the input word accesses."""
        return fn.last(self.trace(word, start=start))

    def label(self, word, *, start=None):
        """Returns the label of the input word."""
        output = self._label(self.transition(word, start=start))
        assert (self.outputs is None) or (output in self.outputs)
        return output

    def transduce(self, word, *, start=None):
        """Returns the labels of the states traced by the input word."""
        return tuple(map(self._label, self.trace(word, start=start)))[:-1]

    @fn.memoize()
    def states(self):
        """Returns set of states in this automaton."""
        assert self.inputs is not None, "Need to specify inputs field for DFA!"

        visited = set()
        stack = [self.start]
        while stack:
            curr = stack.pop()
            if curr in visited:
                continue
            else:
                visited.add(curr)

            successors = [self._transition(curr, a) for a in self.inputs]
            stack.extend(successors)

        return visited

    def __or__(self, other: DFA) -> DFA:
        """Perform the synchronous parallel composition of automata."""
        return DFA(
            start=(self.start, other.start),
            label=lambda s: (self._label(s[0]), other._label(s[1])),
            transition=lambda s, c: (
                self._transition(s[0], c[0]),
                other._transition(s[1], c[1]),
            ),
            inputs=ProductAlphabet(self.inputs, other.inputs),
            outputs=ProductAlphabet(self.outputs, other.outputs),
        )

    def __rshift__(self, other: DFA) -> DFA:
        """Cascading composition where self's outputs are others's inputs."""
        assert self.outputs <= other.inputs

        def transition(composite_state, left_input):
            left, right = composite_state
            right_input = self._label(left)

            left2 = self._transition(left, left_input)
            right2 = other._transition(right, right_input)
            return (left2, right2)

        return DFA(
            start=(self.start, other.start),
            inputs=self.inputs, outputs=other.outputs,
            label=lambda s: other._label(s[1]),
            transition=transition,
        )

    def __lshift__(self, other: DFA) -> DFA:
        """Cascading composition where other's outputs are self's inputs."""
        return other >> self
