from tests.__init__ import *


def test_moves_are_deterministic_and_transitions_apply_them():
    diagram = knot(3, 1)

    moves = get_moves(diagram)
    diagram_transitions = list(transitions(diagram))

    assert moves
    assert moves == get_moves(diagram)
    assert len(moves) == len(set(moves))
    assert [move for move, _ in diagram_transitions] == moves
    assert all(next_diagram.is_valid() for _, next_diagram in diagram_transitions)
    assert all(
        apply_move(diagram, move) == next_diagram
        for move, next_diagram in diagram_transitions
    )


def test_move_rejects_invalid_shape():
    with pytest.raises(ValueError, match="requires 2 edge"):
        Move(MoveKind.POKE, (1,))

    with pytest.raises(ValueError, match="distinct edges"):
        Move(MoveKind.POKE, (1, 1))


def test_moves_and_move_kinds_have_readable_representations():
    poke = Move(MoveKind.POKE, (2, 5))
    twist = Move(MoveKind.LEFT_POSITIVE_TWIST, (3,))

    assert str(MoveKind.LEFT_POSITIVE_TWIST) == "LeftPositiveTwist"
    assert repr(MoveKind.LEFT_POSITIVE_TWIST) == "LeftPositiveTwist"
    assert str(poke) == "Move(Poke, (2, 5))"
    assert repr(poke) == "Move(Poke, (2, 5))"
    assert str(twist) == "Move(LeftPositiveTwist, (3,))"


def test_apply_move_rejects_invalid_diagram_and_out_of_range_edges():
    with pytest.raises(ValueError, match="invalid diagram"):
        apply_move(LinkDiagram([1, 1, 1, 1]), Move(MoveKind.UNTWIST, (1,)))

    with pytest.raises(ValueError, match="belong to the diagram"):
        apply_move(TREFOIL, Move(MoveKind.UNTWIST, (7,)))
