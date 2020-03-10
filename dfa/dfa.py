from __future__ import annotations

from typing import Callable, Hashable

import attr
import funcy as fn

from dfa.alphabet import Letter, Alphabet, ProductAlphabet, SupAlphabet
from dfa.alphabet import _freeze


State = Hashable


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

    def run(self, *, start=None, label=False):
        """Creates a co-routine that simulates the automata:
            - Takes in characters from the input alphabet.
            - Yields states.
        """
        state = self.start if start is None else start
        labeler = self._label if label else lambda x: x

        while True:
            char = yield labeler(state)
            assert (self.inputs is None) or (char in self.inputs)
            state = self._transition(state, char)

    def trace(self, word, *, start=None, label=False):
        """Creates a generator that yields the sequence of states that
        results from reading the word.
        """
        machine = self.run(start=start, label=label)

        for char in fn.concat([None], word):
            yield machine.send(char)

    def transition(self, word, *, start=None):
        """Returns the state the input word accesses."""
        return fn.last(self.trace(word, start=start))

    def label(self, word, *, start=None):
        """Returns the label of the input word."""
        output = fn.last(self.trace(word, start=start, label=True))
        assert (self.outputs is None) or (output in self.outputs)
        return output

    def transduce(self, word, *, start=None):
        """Returns the labels of the states traced by the input word."""
        return tuple(self.trace(word, start=start, label=True))[:-1]

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
