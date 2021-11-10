import funcy as fn
import itertools
import numpy as np
from lazytree import LazyTree

from dfa import DFA, State, Letter
from collections import defaultdict



DFADict = dict[State, tuple[Letter, dict[Letter, State]]]


def dfa2dict(dfa_, *, reindex=False) -> tuple[DFADict, State]:
    dfa_.states()  # Explicitly compute states.
    if reindex:
        relabel = {s: i for i, s in enumerate(dfa_._states)}.get
    else:
        relabel = fn.identity

    def outputs(state):
        trans = {a: relabel(dfa_._transition(state, a)) for a in dfa_.inputs}
        return dfa_._label(state), trans

    dfa_dict = {relabel(s): outputs(s) for s in dfa_.states()}
    return dfa_dict, relabel(dfa_.start)


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

def minimize_dfa(dfa):
    # implementation of Hopcroft's DFA minimization algorithm
    accepting_states = set()
    rejecting_states = set()
    for state in dfa.states():
        if dfa._label(state):
            accepting_states.add(state)
        else:
            rejecting_states.add(state)
    p_part = {frozenset(accepting_states), frozenset(rejecting_states)}
    w_part = {frozenset(accepting_states), frozenset(rejecting_states)}
    while len(w_part) > 0:
        curr_set = w_part.pop()
        for char in dfa.inputs:
            x_set = set()
            for state in dfa.states():
                if dfa._transition(state, char) in curr_set:
                    x_set.add(state)
            new_p_part = set()
            for y_set in p_part:
                intersect_set = frozenset(y_set.intersection(x_set))
                diff_set = frozenset(y_set - x_set)
                if len(intersect_set) > 0 and len(diff_set) > 0:
                    new_p_part.add(intersect_set)
                    new_p_part.add(diff_set)
                    if y_set in w_part:
                        w_part.remove(y_set)
                        w_part.add(intersect_set)
                        w_part.add(diff_set)
                    else:
                        if len(intersect_set) <= len(diff_set):
                            w_part.add(intersect_set)
                        else:
                            w_part.add(diff_set)
                else:
                    new_p_part.add(y_set)
            p_part = new_p_part
    # take the partition P and create a DFA from it
    minimized_dfa_dict = {}
    #make a dict where we can hash the new state (idx) given old state sets
    set_to_idx_dict = dict((x[1], x[0]) for x in enumerate(p_part))
    start_state = None
    #use that to get transitions between sets and then construct the dfa from it
    for state_set, idx in set_to_idx_dict.items():
        if dfa.start in state_set:
            start_state = idx
        state_transitions = {}
        is_accepting = True if len(state_set.intersection(accepting_states)) > 0 else False
        for char in dfa.inputs:
            old_state = dfa._transition(list(state_set)[0], char)
            for partition in set_to_idx_dict:
                if old_state in partition:
                    state_transitions[char] = set_to_idx_dict[partition]
        minimized_dfa_dict[idx] = (is_accepting, state_transitions)
    return dict2dfa(minimized_dfa_dict, start_state)
