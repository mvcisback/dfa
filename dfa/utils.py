from typing import Optional

import funcy as fn
import itertools
from bidict import bidict
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


def enumerate_dfas(alphabet, min_size: int = 2, max_size: Optional[int] = None)  :
    for num_states in range(min_size, max_size + 1):
        #create transition dict
        transitions = defaultdict(dict)
        # for each symbol, generate an adjacency matrix
        # create an iterator of all possible adjacency matrices
        adj_list_gnr = itertools.permutations(range(num_states))  # 1 adjacency list per state
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


def minimize_dfa(orig: DFA):
    """Minimize a DFA using Hopcroft's algorithm."""
    states = orig.states()

    # Group states by label.
    groups = fn.group_by(orig._label, states)
    groups = fn.walk_values(frozenset, groups)
    groups = bidict(groups).inv

    p_part = [frozenset(grp) for grp in groups]
    w_part = set(p_part)
    while len(w_part) > 0:
        curr_set = w_part.pop()
        for char in orig.inputs:
            x_set = {s for s in states if orig._transition(s, char) in curr_set}

            new_p_part = set()
            for y_set in p_part: # Try to shatter equivalence classes.
                intersect_set = y_set & x_set
                diff_set = y_set - x_set

                if intersect_set and diff_set:  # Discovered split.
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

    # Create mapping from states to representative states of equivalence class.
    state2rep = {}
    for grp in p_part:
        rep = orig.start if (orig.start in grp) else fn.first(grp)
        state2rep.update((s, rep) for s in grp)
    
    return DFA(
        start=orig.start,
        inputs=orig.inputs,
        outputs=orig.outputs,
        label=orig._label,
        transition=lambda s, c: state2rep[orig._transition(s, c)]
    )
