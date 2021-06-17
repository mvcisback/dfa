import funcy as fn
from lazytree import LazyTree

from dfa import DFA


def dfa2dict(dfa_):
    def outputs(state):
        trans = {a: dfa_.transition((a,), start=state) for a in dfa_.inputs}
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

def check_equivalence(dfa_a_, dfa_b_):
    return check_is_subset(dfa_a_, dfa_b_) is None and check_is_subset(dfa_b_, dfa_a_) is None

def check_is_subset(dfa_, dfa_subset_candidate_):
    # first, get the complement of the non-candidate DFA
    dfa12 = (~dfa_) & dfa_subset_candidate_
    bad_states = (s for s in dfa12.states() if dfa12._label(s))
    bad_state = next(bad_states, None)
    if bad_state is None:
        return None
    all_paths = paths(dfa12, dfa12.start, end=bad_state)

    return next(all_paths)
