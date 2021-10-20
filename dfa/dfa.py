from __future__ import annotations

import operator
from functools import wraps
from typing import Hashable, FrozenSet, Callable, Optional

import attr
import funcy as fn


State = Hashable
Letter = Hashable
Alphabet = FrozenSet[Letter]


def boolean_only(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        if self.outputs != {True, False}:
            raise ValueError(f'{method} only defined for Boolean output DFAs.')
        return method(self, *args, **kwargs)
    return wrapped


@attr.frozen
class DFA:
    start: State
    _label: Callable[[State], Letter] = attr.ib(
        converter=fn.memoize
    )
    _transition: Callable[[State, Letter], State] = attr.ib(
        converter=fn.memoize
    )
    inputs: Optional[Alphabet] = attr.ib(
        converter=lambda x: x if x is None else frozenset(x), default=None
    )
    outputs: Alphabet = attr.ib(converter=frozenset, default={True, False})
    _states: Optional[FrozenSet[State]] = None

    def __repr__(self) -> int:
        from dfa.utils import dfa2dict
        import pprint

        if self.inputs is not None:
            return pprint.pformat(dfa2dict(self))
        else:
            start, inputs, outputs = self.start, self.inputs, self.outputs
            return f'DFA({start=},{inputs=},{outputs=})'

    def __hash__(self) -> int:
        return hash(repr(self))

    def __eq__(self, other: DFA) -> bool:
        return isinstance(other, DFA) and (repr(self) == repr(other))

    def run(self, *, start=None, label=False):
        """Co-routine interface for simulating runs of the automaton.

        - Users can send system actions (elements of self.inputs).
        - Co-routine yields the current state.

        If label is True, then state labels are returned instead
        of states.
        """
        labeler = self.dfa._label if label else lambda x: x

        state = self.start if start is None else start
        while True:
            letter = yield labeler(state)
            state = self.transition((letter,), start=state)

    def trace(self, word, *, start=None):
        state = self.start if start is None else start
        yield state

        for char in word:
            assert (self.inputs is None) or (char in self.inputs)
            state = self._transition(state, char)
            yield state

    def transition(self, word, *, start=None):
        return fn.last(self.trace(word, start=start))

    def label(self, word, *, start=None):
        output = self._label(self.transition(word, start=start))
        assert (self.outputs is None) or (output in self.outputs)
        return output

    def transduce(self, word, *, start=None):
        return tuple(map(self._label, self.trace(word, start=start)))[:-1]

    def states(self):
        if self._states is not None:
            return self._states

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

        # Cache _states. Note: Safely violates frozen.
        object.__setattr__(self, "_states", visited)
        return visited

    @boolean_only
    def __invert__(self):
        return attr.evolve(self, label=lambda s: not self._label(s))

    def _bin_op(self, other, op):
        if (self.outputs != other.outputs) or (self.inputs != other.inputs):
            raise ValueError(f"{op} requires common i/o interface.")
        return DFA(
            start=(self.start, other.start),
            inputs=self.inputs,  # Assumed shared alphabet
            transition=lambda s, c: (
                self._transition(s[0], c),
                other._transition(s[1], c)
            ),
            label=lambda s: op(self._label(s[0]), other._label(s[1])))

    @boolean_only
    def __xor__(self, other: DFA) -> DFA:
        return self._bin_op(other, operator.xor)

    @boolean_only
    def __or__(self, other: DFA) -> DFA:
        return self._bin_op(other, operator.or_)

    @boolean_only
    def __and__(self, other: DFA) -> DFA:
        return self._bin_op(other, operator.and_)
