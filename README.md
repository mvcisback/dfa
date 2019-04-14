# DFA

[![Build Status](https://travis-ci.com/mvcisback/dfa.svg?branch=master)](https://travis-ci.com/mvcisback/dfa)
[![codecov](https://codecov.io/gh/mvcisback/DiscreteSignals/branch/master/graph/badge.svg)](https://codecov.io/gh/mvcisback/dfa)


[![PyPI version](https://badge.fury.io/py/dfa.svg)](https://badge.fury.io/py/dfa)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple python implementation of a DFA. Features:

1. State can be any Hashable object.
2. Alphabet can be any finite sequence of Hashable objects.
3. Designed to be immutable and hashable (assuming components are
   immutable and hashable).


# Usage

```python
from dfa import DFA

dfa1 = DFA(
 start=0,
 alphabet={0, 1},
 accept=lambda s: (s % 4) == 3,
 transition=lambda s, c: (s + c) % 4,
)

assert dfa1.accepts([1, 1, 1, 1])
assert not dfa1.accepts([1, 0])


dfa2 = DFA(
 start="left",
 alphabet={"move right", "move left"},
 accept=lambda s: s == "left",
 transition=lambda s, c: "left" if c == "move left" else "right",
)

assert dfa2.accepts(["move right"]*100 + ["move left"])
assert not dfa2.accepts(["move left", "move right"])
```
