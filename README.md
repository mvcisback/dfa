# DFA

[![Build Status](https://travis-ci.com/mvcisback/dfa.svg?branch=master)](https://travis-ci.com/mvcisback/dfa)
[![codecov](https://codecov.io/gh/mvcisback/DiscreteSignals/branch/master/graph/badge.svg)](https://codecov.io/gh/mvcisback/dfa)
[![PyPI version](https://badge.fury.io/py/dfa.svg)](https://badge.fury.io/py/dfa)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple python implementation of a DFA. 

**Features:**

1. State can be any Hashable object.
2. Alphabet can be any finite sequence of Hashable objects.
3. Designed to be immutable and hashable (assuming components are
   immutable and hashable).
4. Design choice to allow transition map and accepting set to be
   given as functions rather than an explicit `dict` or `set`.

# Installation

If you just need to use `dfa`, you can just run:

`$ pip install dfa`

For developers, note that this project uses the
[poetry](https://poetry.eustace.io/) python package/dependency
management tool. Please familarize yourself with it and then
run:

`$ poetry install`

# Usage

The `dfa` api is centered around the `DFA` object. 

By default, the `DFA` object models a `Deterministic Finite Acceptor`,
e.g., a recognizer of a Regular Language. 

**Example Usage:**
```python
from dfa import DFA

dfa1 = DFA(
    start=0,
    inputs={0, 1},
    label=lambda s: (s % 4) == 3,
    transition=lambda s, c: (s + c) % 4,
)

dfa2 = DFA(
    start="left",
    inputs={"move right", "move left"},
    label=lambda s: s == "left",
    transition=lambda s, c: "left" if c == "move left" else "right",
)
```

## Membership Queries

```python
assert dfa1.label([1, 1, 1, 1])
assert not dfa1.label([1, 0])

assert dfa2.label(["move right"]*100 + ["move left"])
assert not dfa2.label(["move left", "move right"])
```

## Transitions and Traces

```python
assert dfa1.transition([1, 1, 1]) == 3
assert list(dfa1.trace([1, 1, 1])) == [0, 1, 2, 3]
```

## Non-boolean output alphabets

Sometimes, it is useful to model an automata which can label a word
using a non-Boolean alphabet. For example, `{True, False, UNSURE}`.

The `DFA` object supports this by specifying the output alphabet.

```python
UNSURE = None

def my_labeler(s):
    if s % 4 == 2:
       return None
    return (s % 4) == 3


dfa3 = DFA(
    start=0,
    inputs={0, 1},
    label=my_labeler,
    transition=lambda s, c: (s + c) % 4,
    outputs={True, False, UNSURE},
)
```

**Note:** If `outputs` is set to `None`, then no checks are done that
the outputs are within the output alphabet.

```python
dfa4 = DFA(
    start=0,
    inputs={0, 1},
    label=my_labeler,
    transition=lambda s, c: (s + c) % 4,
    outputs=None,
)
```

## Other

```python
# Perform a depth first traversal to collect all reachable states.
assert dfa1.states() == {0, 1, 2, 3}
```
