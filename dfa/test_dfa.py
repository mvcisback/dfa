import pytest

import hypothesis.strategies as st
from hypothesis import given

from dfa import DFA, SupAlphabet, ProductAlphabet


@given(st.lists(st.booleans()))
def test_example1(word):
    dfa = DFA(
        start=0,
        inputs={0, 1},
        label=lambda s: (s % 4) == 3,
        transition=lambda s, c: (s + c) % 4,
    )
    assert hash(dfa)
    accept = sum(word) % 4 == 3
    assert dfa.label(word) == accept
    assert dfa.states() == {0, 1, 2, 3}
    assert dfa.transduce(()) == ()
    assert dfa.transduce((1,)) == (False,)
    assert dfa.transduce((1, 1, 1, 1)) == (False, False, False, True)


@given(st.lists(
    st.one_of(
        st.just("move left"),
        st.just("move right"))
))
def test_example2(word):
    dfa = DFA(
        start="left",
        inputs=["move right", "move left"],
        label=lambda s: s == "left",
        transition=lambda s, c: "left" if c == "move left" else "right",
    )
    assert hash(dfa)
    accept = (len(word) == 0) or (word[-1] == "move left")
    assert dfa.label(word) == accept
    assert dfa.states() == {"left", "right"}


def test_sup_alphabet():
    machine1 = DFA(
        start=0, label=lambda s: s,
        transition=lambda s, c: (s + c) & 1,
    )
    alphabet = machine1.inputs

    assert isinstance(alphabet, SupAlphabet)
    assert 'x' in alphabet

    assert not (alphabet < alphabet)
    assert not (alphabet > alphabet)

    assert alphabet <= alphabet
    assert alphabet >= alphabet
    assert alphabet == alphabet

    assert alphabet != {0, 1}
    assert {0, 1} != alphabet

    assert {0, 1} < alphabet
    assert alphabet > {0, 1}

    assert not (alphabet < {0, 1})
    assert not ({0, 1} > alphabet)

    assert {0, 1} <= alphabet
    assert alphabet >= {0, 1}

    assert not ({0, 1} >= alphabet)
    assert not (alphabet <= {0, 1})


def test_parallel_composition():
    machine1 = DFA(
        start=0, inputs={0, 1}, label=lambda s: s,
        transition=lambda s, c: (s + c) & 1,
    )
    machine2 = DFA(
        start=0, label=lambda s: s,
        transition=lambda s, c: (s + c) & 1,
    )
    machine11 = machine1 | machine1

    assert isinstance(machine11.inputs, ProductAlphabet)
    assert machine11.label([(0, 0), (1, 0)]) == (1, 0)
    assert len(machine11.inputs) == 4
    assert len(machine11.outputs) == 4
    assert len(str(machine11.inputs)) == len("{0, 1} x {0, 1}")
    assert len(str(machine11.outputs)) == len("{False, True} x {False, True}")

    machine12 = machine1 | machine2
    assert machine12.label([(0, 0), (1, 0)]) == (1, 0)
    assert (1, 'x') in machine12.inputs
    assert (2, 'x') not in machine12.inputs
    with pytest.raises(Exception):
        len(machine12)
