import dfa
from dfa.utils import dict2dfa, dfa2dict, paths


def test_dict2dfa():
    dfa_dict = {
        0: (False, {0: 0, 1: 1}),
        1: (False, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 3}),
        3: (True, {0: 3, 1: 0})
    }
    dfa = dict2dfa(dfa_dict, start=0)
    assert (dfa_dict, 0) == dfa2dict(dfa)


def test_paths():
    dfa_ = dfa.DFA(
        start=0,
        inputs={0, 1},
        label=lambda s: (s % 4) == 3,
        transition=lambda s, c: (s + c) % 4,
    )
    access_strings = paths(dfa_, start=0, end=1, max_length=7)

    for word in access_strings:
        assert dfa_.transition(word, start=0) == 1
