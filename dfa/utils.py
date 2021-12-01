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


def dict2dfa(dfa_dict, start, outputs=None):
    outputs = set() if outputs is None else set(outputs)
    outputs |= set(fn.pluck(0, dfa_dict.values()))

    return DFA(
        start=start,
        inputs=fn.mapcat(dict.keys, fn.pluck(1, dfa_dict.values())),
        outputs=outputs,
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
    return next(words(lang), None)


def words(lang: DFA):
    """Iterates over all works word in the language of DFA or None."""
    accepting = (s for s in lang.states() if lang._label(s))
    paths_to_accepting = (paths(lang, lang.start, end=s) for s in accepting)
    yield from fn.interleave(*paths_to_accepting)


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


def enumerate_dfas(alphabet, outputs=(False, True)):
    dfas = _enumerate_dfas(alphabet, outputs)
    yield from fn.distinct(dfas, key=minimize)


def _enumerate_dfas(alphabet, outputs):
    for num_states in fn.count(start=1):
        transitions = defaultdict(dict)
        # Create an iterator of all possible adjacency matrices.
        adj_list_gnr = itertools.permutations(range(num_states))
        # Generate all possible letter -> adjacency matrix maps.
        total_gnr = itertools.product(adj_list_gnr, repeat=len(alphabet))
        for adjacency_lists in total_gnr:
            # Construct the DFA transitions based on adjacency lists.
            for char, adj_list in zip(alphabet, adjacency_lists):
                for state_idx, resulting_state in enumerate(adj_list):
                    transitions[state_idx][char] = resulting_state

            # Generate all possible permutations of accepting states.
            for accepting in itertools.product(outputs, repeat=num_states):
                dfa_dict = {}
                for state, label in enumerate(accepting):
                    dfa_dict[state] = (label, transitions[state])

                assert len(dfa_dict) == num_states
                # Generate all possible start states.
                for start in range(num_states):
                    yield dict2dfa(dfa_dict, start=state, outputs=outputs)


def minimize(orig: DFA):
    """Minimize a DFA using Hopcroft's algorithm."""
    states = orig.states()

    # Group states by label.
    groups = fn.group_by(orig._label, states)
    groups = fn.walk_values(frozenset, groups)
    groups = bidict(groups).inv

    p_part = [frozenset(grp) for grp in groups]
    w_part = set(p_part)
    while len(w_part) > 0:
        curr = w_part.pop()
        for char in orig.inputs:
            new_p_part = set()
            x_set = {s for s in states if orig._transition(s, char) in curr}
            for y_set in p_part:  # Try to shatter equivalence classes.
                intersect_set = y_set & x_set
                diff_set = y_set - x_set

                if intersect_set and diff_set:  # Discovered split.
                    new_p_part.add(intersect_set)
                    new_p_part.add(diff_set)

                    if y_set in w_part:
                        w_part.remove(y_set)
                        w_part.add(intersect_set)
                        w_part.add(diff_set)
                    elif len(intersect_set) <= len(diff_set):
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
    ).normalize()
