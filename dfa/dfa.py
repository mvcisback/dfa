from typing import Hashable, FrozenSet, Callable

import attr
import funcy as fn


State = Hashable
Letter = Hashable


@attr.s(frozen=True, auto_attribs=True)
class DFA:
    start: State
    alphabet: FrozenSet[State] = attr.ib(converter=frozenset)
    _accept: Callable[[State], bool]
    _transition: Callable[[State, Letter], State]

    def trace(self, word):
        state = self.start
        yield state

        for char in word:
            assert char in self.alphabet
            state = self._transition(state, char)
            yield state

    def transition(self, word):
        return fn.last(self.trace(word))

    def accepts(self, word):
        return self._accept(self.transition(word))
