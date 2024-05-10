from itertools import combinations

import funcy as fn

import dfa
from dfa.utils import dict2dfa, dfa2dict, paths
from dfa.utils import find_subset_counterexample, find_equiv_counterexample
from dfa.utils import enumerate_dfas, minimize, words, find_word
from dfa.utils import min_distance_to_accept_by_state


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
    dfa2 = dfa1.minimize()
    assert find_equiv_counterexample(true_dfa, dfa2) is None


def test_enumerate():
    dfas = fn.take(10, enumerate_dfas('abc'))
    for dfa1, dfa2 in combinations(dfas, 2):
        assert find_equiv_counterexample(dfa1, dfa2) is not None

    # Check first 3 DFAs are as expected with only a single output.
    dfas = fn.take(7, enumerate_dfas('a'))
    sizes = [len(d.states()) for d in dfas]
    assert sizes == [1, 1, 2, 2, 2, 2, 3]


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


def test_find_word_bug():
    start = 0
    dfa_dict = {
        0: (False,
            {'a': 0,
             'b': 2,
             'c': 0,
             'd': 0,
             'e': 0,
             'f': 0,
             'g': 0,
             'h': 0,
             'i': 0,
             'j': 0,
             'k': 1,
             'l': 0}),
        1: (False,
            {'a': 1,
             'b': 1,
             'c': 1,
             'd': 0,
             'e': 1,
             'f': 1,
             'g': 1,
             'h': 1,
             'i': 1,
             'j': 1,
             'k': 1,
             'l': 1}),
        2: (True,
            {'a': 2,
             'b': 2,
             'c': 2,
             'd': 2,
             'e': 2,
             'f': 2,
             'g': 2,
             'h': 2,
             'i': 2,
             'j': 2,
             'k': 2,
             'l': 2})}
    lang = dict2dfa(dfa_dict, start=start)
    words = (w for s, w in lang.walk() if lang._label(s) is True)
    assert lang.label(lang.find_word())


def test_min_distance_to_accept_by_state():
    def label(s):
        if s == 'fail': return False
        return s == 3

    def transition(s, c):
        if 'fail' in (s, c): return False
        return min(3, max(0, s + c))

    d = dfa.DFA(start=0,
                inputs={0,1,'fail'},
                label=label,
                transition=transition)

    distances = min_distance_to_accept_by_state(d)
    for i in range(4):
        assert distances[i] == 3 - i
    assert distances['fail'] == float('inf')
