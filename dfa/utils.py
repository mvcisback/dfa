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
    return check_is_subset(dfa_a_, dfa_b_) and check_is_subset(dfa_b_, dfa_a_)

def check_is_subset(dfa_, dfa_subset_candidate_):
    # first, get the complement of the non-candidate DFA
    dfa_dict, dfa_start = dfa2dict(dfa_)
    complement_dfa_dict = {state: (not dfa_dict[state][0], dfa_dict[state][1]) for state in dfa_dict}
    complement_dfa_ = dict2dfa(complement_dfa_dict, dfa_start)

    # now, get the automata that recognizes the languages of the candidate and the complement
    candidate_dfa_dict, candidate_dfa_start = dfa2dict(dfa_subset_candidate_)

    intersection_dfa_dict = {}
    for state_u, (u_label, u_transdict) in complement_dfa_dict.items():
        for state_v, (v_label, v_transdict) in candidate_dfa_dict.items():
            joint_transdict = {}
            joint_label = u_label and v_label
            for transition_label in u_transdict:
                if transition_label in v_transdict:
                    joint_transdict[transition_label] = (u_transdict[transition_label], v_transdict[transition_label])
            intersection_dfa_dict[(state_u, state_v)] = (joint_label, joint_transdict)

    joint_start_state = (dfa_start, candidate_dfa_start)
    # lastly, check reachable states. if there is a reachable state, we are not a subset
    intersect_dfa = dict2dfa(intersection_dfa_dict, joint_start_state)
    reachable_states = intersect_dfa.states()
    for reachable_state in reachable_states:
        if intersection_dfa_dict[reachable_state][0]:
            return False
    return True
