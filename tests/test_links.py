from tests.__init__ import *


HOPF_LINK = Diagram(
    [
        (1, 4, 2, 3),
        (3, 2, 4, 1),
        (5, 6, 6, 5),
    ]
)


def assert_edge_cycles_are_traversable(diagram):
    for edge in range(1, 2 * len(diagram.pd_code) + 1):
        diagram._get_forth_index(edge)


@pytest.mark.parametrize(
    "move",
    [
        left_positive_twist,
        left_negative_twist,
        right_positive_twist,
        right_negative_twist,
    ],
)
@pytest.mark.parametrize("edge", range(1, 7))
def test_twists_preserve_link_components_and_can_be_undone(move, edge):
    twisted = move(HOPF_LINK, edge)

    assert twisted.is_valid()
    assert twisted.n_components == 3
    assert_edge_cycles_are_traversable(twisted)
    assert any(
        untwist(twisted, candidate) == HOPF_LINK
        for candidate in get_untwistables(twisted)
    )


@pytest.mark.parametrize("under_edge, over_edge", get_pokables(HOPF_LINK))
def test_pokes_between_link_components_preserve_components_and_can_be_undone(
    under_edge, over_edge
):
    poked = poke(HOPF_LINK, under_edge, over_edge)

    assert poked.is_valid()
    assert poked.n_components == 3
    assert_edge_cycles_are_traversable(poked)
    assert any(
        unpoke(poked, *candidate) == HOPF_LINK for candidate in get_unpokables(poked)
    )


def test_slides_preserve_components_using_single_crossing_unknots():
    diagram = Diagram(
        [
            (8, 1, 9, 2),
            (2, 9, 3, 10),
            (3, 11, 4, 10),
            (7, 5, 8, 4),
            (12, 6, 1, 5),
            (6, 12, 7, 11),
            (13, 14, 14, 13),
        ]
    )

    slid = slide(diagram, 1, 5, 8)

    assert slid.is_valid()
    assert slid.n_components == 2
    assert_edge_cycles_are_traversable(slid)


def test_one_crossing_unknot_can_be_untwisted_without_becoming_crossingless():
    unknot = Diagram([(1, 2, 2, 1)])

    assert get_untwistables(unknot)
    for edge in get_untwistables(unknot):
        simplified = untwist(unknot, edge)
        assert simplified.is_valid()
        assert simplified.n_components == 1
        assert len(simplified.pd_code) == 1
