from tempfile import TemporaryDirectory

import dfa
from dfa.draw import write_dot


def test_draw_smoke():
    dfa1 = dfa.DFA(
        start=0,
        inputs={0, 1},
        label=lambda s: (s % 4) == 3,
        transition=lambda s, c: (s + c) % 4,
    )
    with TemporaryDirectory() as path:
        write_dot(dfa1, f"{path}/test.dot")
