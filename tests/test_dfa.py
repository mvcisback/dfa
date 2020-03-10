from itertools import product

import pytest
import hypothesis.strategies as st
from hypothesis import given

from dfa import DFA, SupAlphabet, ProductAlphabet, ExponentialAlphabet


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

    hash(alphabet)  # Make sure hashable.

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


def test_exponential_alphabet():
    alphabet = ExponentialAlphabet(base={0, 1}, dim=3)
    assert (0, 0, 0) in alphabet
    assert set(alphabet) == set(product(*(3*[(0, 1)])))

    assert product(*(3*[(1,)])) < alphabet
    assert ExponentialAlphabet(base={1}, dim=3) < alphabet
    assert alphabet == alphabet
    assert repr(alphabet) == "{0, 1}^3"


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

    hash(machine11.inputs)  # Make sure hashable.
    assert isinstance(machine11.inputs, ProductAlphabet)
    assert set(machine11.inputs) == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert machine11.inputs == machine11.inputs
    assert ProductAlphabet({0}, {0}) < machine11.inputs

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


def test_seq_composition():
    mod_5 = DFA(
        start=0,
        label=lambda s: s,
        transition=lambda s, c: (s + c) % 5,
        inputs={0, 1},
        outputs={0, 1, 2, 3, 4},
    )
    eq_0 = DFA(
        start=0,
        label=lambda s: s == 0,
        transition=lambda s, c: c,
        inputs={0, 1, 2, 3, 4},
        outputs={True, False}
    )

    eq_0_mod_5 = eq_0 << mod_5
    assert eq_0_mod_5.inputs == {0, 1}
    assert eq_0_mod_5.outputs == {True, False}
    assert eq_0_mod_5.label([0, 0, 0, 0])
    assert eq_0_mod_5.label([1, 1, 1, 1, 1, 0])
    assert not eq_0_mod_5.label([1, 1, 1, 1, 1])
    assert not eq_0_mod_5.label([0, 1, 0, 0, 0])
