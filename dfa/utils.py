import funcy as fn
from lazytree import LazyTree

from dfa import DFA, State, Letter


DFADict = dict[State, tuple[Letter, dict[Letter, State]]]


def dfa2dict(dfa_) -> tuple[DFADict, State]:
    def outputs(state):
        trans = {a: dfa_._transition(state, a) for a in dfa_.inputs}
        return dfa_._label(state), trans

    return {s: outputs(s) for s in dfa_.states()}, dfa_.start


def dict2dfa(dfa_dict, start):
    return DFA(
        start=start,
        inputs=fn.mapcat(dict.keys, fn.pluck(1, dfa_dict.values())),
        outputs=fn.pluck(0, dfa_dict.values()),
        transition=lambda s, c: dfa_dict[s][1][c],
        label=lambda s: dfa_dict[s][0],
    )


def paths(dfa_, start, end=None, *, max_length=float('inf'), randomize=False):
    """Generates all paths froms start to end, subject to max_length.
    """
    if max_length is None:
        max_length = float('inf')

    def child_map(word_path):
        word, path = word_path
        for i in dfa_.inputs:
            state2 = dfa_.transition((i,), start=path[-1])
            yield word + (i,), path + (state2,)

    tree = LazyTree(root=((), (dfa_.start,)), child_map=child_map)
    paths_ = tree.iddfs(max_depth=max_length, randomize=randomize)

    return (word for word, path in paths_ if end is None or path[-1] == end)


def find_word(lang: DFA):
    """Returns a word in the language of DFA or None if language empty."""
    accepted = (s for s in lang.states() if lang._label(s))
    state = next(accepted, None)
    if state is None:
        return None
    all_paths = paths(lang, lang.start, end=state)
    return next(all_paths)


def find_equiv_counterexample(dfa_a, dfa_b):
    """
    Returns None if DFAs are equivalent; if not, returns a counterexample.
    """
    return find_word(dfa_a ^ dfa_b)


def find_subset_counterexample(smaller, bigger):
    """
    Returns None if smaller ⊆ bigger; if not, returns x ∈ smaller - bigger.
    """
    return find_word(~bigger & smaller)
