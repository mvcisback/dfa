from typing import Hashable, FrozenSet, Callable

import attr
import funcy as fn


State = Hashable
Letter = Hashable
Alphabet = FrozenSet[Letter]


@attr.s(frozen=True, auto_attribs=True)
class DFA:
    start: State
    inputs: Alphabet = attr.ib(converter=frozenset)
    _label: Callable[[State], Letter] = attr.ib(
        converter=fn.memoize
    )
    _transition: Callable[[State, Letter], State] = attr.ib(
        converter=fn.memoize
    )
    outputs: Alphabet = attr.ib(converter=frozenset, default={True, False})

    def trace(self, word):
        state = self.start
        yield state

        for char in word:
            assert char in self.inputs
            state = self._transition(state, char)
            yield state

    def transition(self, word):
        return fn.last(self.trace(word))

    def label(self, word):
        output = self._label(self.transition(word))
        assert (self.outputs is None) or (output in self.outputs)
        return output

    def transduce(self, word):
        return tuple(map(self._label, self.trace(word)))[:-1]

    @fn.memoize()
    def states(self):
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
