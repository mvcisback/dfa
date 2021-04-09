import pydot

import dfa


def write_dot(dfa_, path):
    dfa_dict, init = dfa.dfa2dict(dfa_)

    nodes = {
        k: pydot.Node(i+1, label=f"{k}\n---\n{v}")
        for i, (k, (v, _)) in enumerate(dfa_dict.items())
    }
    g = pydot.Graph()
    init_node = pydot.Node(0, shape="point", label="")
    g.add_node(init_node)
    g.add_edge(pydot.Edge(init_node, nodes[init]))

    for start, (_, transitions) in dfa_dict.items():
        g.add_node(nodes[start])
        for action, end in transitions.items():
            g.add_edge(pydot.Edge(nodes[start], nodes[end], label=str(action)))

    with open(path, 'w') as f:
        f.write(str(g))
