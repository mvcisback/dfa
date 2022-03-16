import hypothesis.strategies as st
from hypothesis import given

from dfa import DFA


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


def test_run_count():
    count_mod4 = DFA(
        start=0,
        inputs={0, 1},
        outputs={0, 1, 2, 3},
        label=lambda s: s == 0,
        transition=lambda s, c: (s + c) % 4
    )
    machine = count_mod4.run()
    next(machine)

    count = 0
    state = None
    while state != count_mod4.start:
        count += 1
        state = machine.send(1)
    assert count == 4


def test_int_encoding():
    is_left = DFA(
        start="left",
        inputs=["move right", "move left"],
        label=lambda s: s == "left",
        transition=lambda s, c: "left" if c == "move left" else "right",
    )
    empty = DFA(
        start=False,
        inputs={0, 1},
        label=lambda _: False,
        transition=lambda *_: False,
    )
    assert empty.to_int() == 0b1_0_10_1_0
    assert is_left.to_int() == 0b1_10_1_10_1_0_0_0_011_100

    for lang in [empty, ~empty, is_left, ~is_left]:
        inputs = sorted(lang.inputs)
        lang2 = DFA.from_int(lang.to_int(), inputs)
        assert lang == lang2
