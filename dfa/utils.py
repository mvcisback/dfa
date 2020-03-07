import funcy as fn
from lazytree import LazyTree

from dfa import DFA, ProductAlphabet


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


def empty(inputs=None) -> DFA:
    """Constructs DFA for the empty language."""
    false = fn.constantly(False)
    return DFA(start=False, label=false, transition=false, inputs=inputs)


def universal(inputs=None) -> DFA:
    """Constructs DFA for the universal language."""
    true = fn.constantly(True)
    return DFA(start=True, label=true, transition=true, inputs=inputs)


def tee(left: DFA, right: DFA) -> DFA:
    if left.inputs <= right.inputs:
        inputs = left.inputs
    elif right.inputs <= left.inputs:
        inputs = right.inputs
    else:
        raise RuntimeError("Inputs need to be compatible")

    def transition(s, c):
        return left._transition(s[0], c), right._transition(s[1], c)

    return DFA(
        start=(left.start, right.start),
        inputs=inputs,
        transition=transition,
        label=lambda s: (left._label(s[0]), right._label(s[1])),
        outputs=ProductAlphabet(left.outputs, right.outputs),
    )
