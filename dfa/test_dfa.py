import hypothesis.strategies as st
from hypothesis import given

from dfa import DFA


@given(st.lists(st.booleans()))
def test_example1(word):
    dfa = DFA(
        start=0,
        alphabet={0, 1},
        accept=lambda s: (s % 4) == 3,
        transition=lambda s, c: (s + c) % 4,
    )
    assert hash(dfa)
    accept = sum(word) % 4 == 3
    assert dfa.accepts(word) == accept
    assert dfa.states() == {0, 1, 2, 3}


@given(st.lists(
    st.one_of(
        st.just("move left"),
        st.just("move right"))
))
def test_example2(word):
    dfa = DFA(
        start="left",
        alphabet=["move right", "move left"],
        accept=lambda s: s == "left",
        transition=lambda s, c: "left" if c == "move left" else "right",
    )
    assert hash(dfa)
    accept = (len(word) == 0) or (word[-1] == "move left")
    assert dfa.accepts(word) == accept
    assert dfa.states() == {"left", "right"}
