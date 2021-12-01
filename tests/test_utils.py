from itertools import combinations

import funcy as fn

import dfa
from dfa.utils import dict2dfa, dfa2dict, paths
from dfa.utils import find_subset_counterexample, find_equiv_counterexample
from dfa.utils import enumerate_dfas, minimize, words, find_word


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


def test_subset_equivalence():
    dfa_dict = {
        0: (False, {0: 0, 1: 1}),
        1: (False, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 3}),
        3: (True, {0: 3, 1: 0})
    }

    dfa_dict_super = {
        0: (False, {0: 0, 1: 1}),
        1: (False, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 3}),
        3: (True, {0: 4, 1: 0}),
        4: (True, {0: 4, 1: 5}),
        5: (True, {0: 0, 1: 1})
    }

    dfa_dict_equiv = {
        0: (False, {0: 0, 1: 1}),
        1: (False, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 3}),
        3: (True, {0: 4, 1: 0}),
        4: (True, {0: 4, 1: 0}),
    }

    dfa1 = dict2dfa(dfa_dict, 0)
    dfa2 = dict2dfa(dfa_dict_super, 0)
    dfa3 = dict2dfa(dfa_dict_equiv, 0)

    assert find_subset_counterexample(dfa1, dfa2) is None
    assert find_subset_counterexample(dfa2, dfa1) is not None
    assert find_equiv_counterexample(dfa1, dfa3) is None


def test_minimize():
    dfa_dict_super = {
        0: (False, {0: 1, 1: 2}),
        1: (False, {0: 0, 1: 3}),
        2: (True, {0: 4, 1: 5}),
        3: (True, {0: 4, 1: 5}),
        4: (True, {0: 4, 1: 5}),
        5: (False, {0: 5, 1: 5})
    }

    dfa_dict_min = {
        0: (False, {0: 0, 1: 1}),
        1: (True, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 2}),
    }
    dfa1 = dict2dfa(dfa_dict_super, 0)
    true_dfa = dict2dfa(dfa_dict_min, 0)
    dfa2 = minimize(dfa1)
    assert find_equiv_counterexample(true_dfa, dfa2) is None


def test_enumerate():
    dfas = fn.take(10, enumerate_dfas('abc'))
    for dfa1, dfa2 in combinations(dfas, 2):
        assert find_equiv_counterexample(dfa1, dfa2) is not None


def test_words():
    dfa_dict = {
        0: (False, {0: 0, 1: 1}),
        1: (False, {0: 1, 1: 2}),
        2: (False, {0: 2, 1: 3}),
        3: (True, {0: 3, 1: 0})
    }
    lang = dict2dfa(dfa_dict, start=0)
    x = find_word(lang)
    assert x is not None
    assert lang.label(x)

    xs = set(fn.take(5, words(lang)))
    assert len(xs) == 5
    assert all(lang.label(x) for x in xs)
