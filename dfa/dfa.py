from typing import Hashable, FrozenSet, Callable

import attr
import funcy as fn


State = Hashable
Letter = Hashable


@attr.s(frozen=True, auto_attribs=True)
class DFA:
    start: State
    alphabet: FrozenSet[Letter] = attr.ib(converter=frozenset)
    _accept: Callable[[State], bool] = attr.ib(
        converter=fn.memoize
    )
    _transition: Callable[[State, Letter], State] = attr.ib(
        converter=fn.memoize
    )

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

            successors = [self._transition(curr, a) for a in self.alphabet]
            stack.extend(successors)

        return visited
