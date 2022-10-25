from __future__ import annotations

import operator
from functools import cache, wraps
from typing import Hashable, FrozenSet, Callable, Optional, Sequence, Iterable

import attr
import funcy as fn

State = Hashable
Letter = Hashable
Alphabet = FrozenSet[Letter]
OrderedAlphabet = Sequence[Letter]
Word = Sequence[Alphabet]


def boolean_only(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        if not (self.outputs <= {True, False}):
            raise ValueError(f'{method} only defined for Boolean output DFAs.')
        return method(self, *args, **kwargs)
    return wrapped


def bits_needed(n: int) -> int:
    return 0 if n < 2 else len(bin(n - 1)) - 2


@attr.frozen(auto_detect=True)
class DFA:
    start: State
    _label: Callable[[State], Letter] = attr.ib(
        converter=cache
    )
    _transition: Callable[[State, Letter], State] = attr.ib(
        converter=cache
    )
    inputs: Optional[Alphabet] = attr.ib(
        converter=lambda x: x if x is None else frozenset(x), default=None
    )
    outputs: Alphabet = attr.ib(converter=frozenset, default={True, False})
    _states: Optional[Sequence[State]] = None
    _hash: Optional[int] = None

    def __repr__(self) -> int:
        from dfa.utils import dfa2dict
        import pprint

        if self.inputs is not None:
            return 'DFA' + pprint.pformat(dfa2dict(self))
        else:
            start, inputs, outputs = self.start, self.inputs, self.outputs
            return f'DFA({start=},{inputs=},{outputs=})'

    def normalize(self) -> DFA:
        """Normalizes the state indexing and memoizes transitions/labels."""
        from dfa.utils import dfa2dict
        from dfa.utils import dict2dfa
        return dict2dfa(*dfa2dict(self, reindex=True))

    def minimize(self) -> DFA:
        from dfa.utils import minimize
        return minimize(self)

    @boolean_only
    def to_int(self, input_order: OrderedAlphabet | None = None) -> int:
        from dfa.utils import dfa2dict, minimize
        from bitarray import bitarray
        from bitarray.util import int2ba, ba2int

        if input_order is None:
            input_order = sorted(self.inputs)
        elif not (set(input_order) < self.inputs):
            raise ValueError('Some inputs missing from input order.')
        graph, start = dfa2dict(minimize(self), reindex=True)
        accepting = {s for s, (label, _) in graph.items() if label}

        state_bits = bits_needed(len(graph))
        input_bits = bits_needed(len(input_order))

        encoding = bitarray([1])  # Start with 1 for int conversion.
        # Specify number of states and inputs.
        # Format:
        # 1. zero delimited unary encoding of number of bits needed.
        # 2. binary encoding of |states| and |inputs|.
        if state_bits:
            encoding.extend(int2ba((1 << state_bits) - 1, state_bits))
        encoding.append(0)
        if state_bits:
            encoding.extend(int2ba(len(graph) - 1, state_bits))
        encoding.extend(int2ba((1 << input_bits) - 1, input_bits))
        encoding.append(0)
        encoding.extend(int2ba(len(self.inputs) - 1, input_bits))

        # Specify accepting (or rejecting set).
        specify_rejecting = len(accepting) * 2 >= len(graph) + 1
        indicies = set(graph) - accepting if specify_rejecting else accepting

        encoding.append(specify_rejecting)
        if state_bits:
            encoding.extend(int2ba(len(indicies) - 1, state_bits))

        for idx in indicies:
            encoding.extend(int2ba(idx, state_bits))

        for start in range(len(graph)):
            transitions = graph[start][1]
            for i, sym in enumerate(input_order):
                end = transitions[sym]
                if start == end:
                    continue
                encoding.extend(int2ba(start, state_bits))
                encoding.extend(int2ba(i, input_bits))
                encoding.extend(int2ba(end, state_bits))
        return ba2int(encoding)

    @staticmethod
    def from_int(encoding: int, inputs: OrderedAlphabet | None = None) -> DFA:
        from bitarray.util import int2ba, ba2int
        encoding = int2ba(encoding)[1:]  # Ignore leading 1.

        # Parse state bits info.
        idx = encoding.find(0)
        state_bits = idx
        encoding = encoding[idx+1:]
        if idx > 0:
            n_states = ba2int(encoding[:state_bits]) + 1
            encoding = encoding[state_bits:]
        else:
            n_states = 1

        # Parse input bits info.
        idx = encoding.find(0)
        input_bits = idx
        encoding = encoding[idx+1:]
        n_inputs = ba2int(encoding[:input_bits]) + 1
        if inputs is not None:
            assert n_inputs == len(inputs)
        else:
            inputs = range(n_inputs)
        encoding = encoding[input_bits:]

        # Specify accepting or rejecting set convention.
        specify_rejecting = bool(encoding[0])
        encoding = encoding[1:]

        if len(encoding) == 0:  # Must be a single state DFA.
            assert n_states == 1
            return DFA(
                start=specify_rejecting,
                inputs=inputs,
                transition=lambda *_: specify_rejecting,
                label=lambda _: specify_rejecting,
            )
        n_accepting = ba2int(encoding[:state_bits]) + 1
        encoding = encoding[state_bits:]
        accepting = set()
        for _ in range(n_accepting):
            idx = ba2int(encoding[:state_bits])
            accepting.add(idx)
            encoding = encoding[state_bits:]

        # Remaining bits are non-stuttering transitions.
        transitions = {}
        while len(encoding) != 0:
            start = ba2int(encoding[:state_bits])
            encoding = encoding[state_bits:]

            sym = ba2int(encoding[:input_bits])
            sym = inputs[sym]
            encoding = encoding[input_bits:]

            end = ba2int(encoding[:state_bits])
            encoding = encoding[state_bits:]

            transitions[start, sym] = end

        return DFA(
            start=0,
            inputs=inputs,
            label=lambda s: (s in accepting) ^ specify_rejecting,
            transition=lambda s, c: transitions.get((s, c), s),
        )

    def __hash__(self) -> int:
        if self._hash is None:
            try:  # First try to use integer encoding.
                _hash = self.to_int()
            except (TypeError, ValueError):
                _hash = hash(repr(self.normalize()))

            object.__setattr__(self, "_hash", _hash)  # Cache hash.
        return self._hash

    def __eq__(self, other: DFA) -> bool:
        from dfa.utils import find_equiv_counterexample as test_equiv
        from dfa.utils import dfa2dict

        if not isinstance(other, DFA):
            return False

        bool_ = {True, False}
        if (self.outputs <= bool_) and (other.outputs <= bool_):
            return test_equiv(self, other) is None
        else:
            return dfa2dict(self, reindex=True) \
                    == dfa2dict(other, reindex=True)

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

    def advance(self, word, *, start=None):
        return attr.evolve(self, start=self.transition(word, start=start))

    def label(self, word, *, start=None):
        output = self._label(self.transition(word, start=start))
        assert (self.outputs is None) or (output in self.outputs)
        return output

    def transduce(self, word, *, start=None):
        return tuple(map(self._label, self.trace(word, start=start)))[:-1]

    def walk(self) -> Iterable[State, Word]:
        """Performs DFS through DFA yields states and their access strings."""
        assert self.inputs is not None, "Need to specify inputs field!"

        # Make search deterministic.
        try:
            inputs = sorted(self.inputs)  # Try to respect inherent order.
        except TypeError:
            inputs = sorted(self.inputs, key=id)  # Fall back on object ids.

        visited = set()
        stack = [((self.start, ()), 0)]
        access_string = []
        while stack:
            (curr, suffix), depth = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)

            del access_string[depth:]     # Remove previous path suffix.
            access_string.extend(suffix)  # Add new path suffix.

            yield (curr, access_string)

            successors = ((self._transition(curr, a), (a,)) for a in inputs)
            stack.extend((state, depth + 1) for state in successors)

    def states(self) -> frozenset[State]:
        if self._states is None:
            states = tuple(s for s, _ in self.walk())
            object.__setattr__(self, "_states", states)  # Cache states.
        return frozenset(self._states)

    def find_word(self, label=True) -> Optional[Word]:
        """DFS for word that accesses a state labeled `label`.

        Returns shortest word if one exists. Otherwise None.
        """
        return fn.first(w for s, w in self.walk() if self._label(s) == label)

    @boolean_only
    def __invert__(self):
        return attr.evolve(self, label=lambda s: not self._label(s))

    def _bin_op(self, other, op):
        if self.inputs != other.inputs:
            raise ValueError(f"{op} requires shared inputs.")
        return DFA(
            start=(self.start, other.start),
            inputs=self.inputs,  # Assumed shared alphabet
            transition=lambda s, c: (
                self._transition(s[0], c),
                other._transition(s[1], c)
            ),
            outputs=self.outputs | other.outputs,
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
