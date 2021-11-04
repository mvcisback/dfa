import funcy as fn
import itertools
import numpy as np
from lazytree import LazyTree
from collections import defaultdict

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

def find_equiv_counterexample(dfa_a, dfa_b):
    """
    Returns None if DFAs are equivalent; if not, returns a counterexample.
    """
    return find_subset_counterexample(dfa_b, dfa_a) if find_subset_counterexample(dfa_a, dfa_b) is None \
        else find_subset_counterexample(dfa_a, dfa_b)

def find_subset_counterexample(smaller, bigger):
    """
    Returns None if dfa_subset_candidate is a subset of dfa; if not, returns a counterexample.
    """
    # first, get the complement of the non-candidate DFA
    should_be_empty = (~bigger) & smaller
    bad_states = (s for s in should_be_empty.states() if should_be_empty._label(s))
    bad_state = next(bad_states, None)
    if bad_state is None:
        return None
    all_paths = paths(should_be_empty, should_be_empty.start, end=bad_state)

    return next(all_paths)

def enumerate_dfas(max_size: int, alphabet, min_size: int=2):
    for num_states in range(min_size, max_size + 1):
        #create transition dict
        transitions = defaultdict(dict)
        # for each symbol, generate an adjacency matrix
        # create an iterator of all possible adjacency matrices
        adj_list_gnr = itertools.permutations(np.arange(num_states))  # 1 adjacency list per state
        # generate all possible adjacency matrices for all possible alphabets
        total_gnr = itertools.product(adj_list_gnr, repeat=len(alphabet))
        adjacency_lists = next(total_gnr, None)
        while adjacency_lists is not None:
            # go through each adjacency list and construct the DFA transitions
            for alpha_idx, adj_list in enumerate(adjacency_lists):
                for state_idx, resulting_state in enumerate(adj_list):
                    transitions[state_idx][alphabet[alpha_idx]] = resulting_state
            #generate all possible permutations of accepting states
            accepting_bitvector_gnr = itertools.product([0,1], repeat=num_states)
            #yield transitions
            for accepting_bitvector in accepting_bitvector_gnr:
                dfa_dict = {}
                for acc_idx, is_accepting in enumerate(accepting_bitvector):
                    new_value = (is_accepting, transitions[acc_idx])
                    dfa_dict[acc_idx] = new_value
                for possible_start_state in range(num_states):
                    #now, go from dict to DFA
                    yield dict2dfa(dfa_dict, start=possible_start_state)
            adjacency_lists = next(total_gnr, None)
