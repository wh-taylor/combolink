from tests.__init__ import *


def test_disjoint_union_relabels_edges_and_preserves_components():
    first = TREFOIL
    second = HOPF_LINK

    union = disjoint_union(first, second)

    assert union.is_valid()
    assert union.n_components == first.n_components + second.n_components
    assert len(union.pd_code) == len(first.pd_code) + len(second.pd_code)
    assert union.pd_code[: len(first.pd_code)] == first.pd_code
    assert union.pd_code[len(first.pd_code) :] == [
        tuple(edge + 2 * len(first.pd_code) for edge in crossing)
        for crossing in second.pd_code
    ]


def test_join_merges_only_the_selected_components():
    first = HOPF_LINK
    second = TREFOIL

    joined = join(first, second, 1, 1)

    assert joined.is_valid()
    assert joined.n_components == first.n_components + second.n_components - 1
    assert len(joined.pd_code) == len(first.pd_code) + len(second.pd_code)
    assert first == HOPF_LINK
    assert second == TREFOIL


def test_join_works_for_every_edge_pair_in_hopf_link_and_trefoil():
    first = HOPF_LINK
    second = TREFOIL

    for self_edge in range(1, 2 * len(first.pd_code) + 1):
        for other_edge in range(1, 2 * len(second.pd_code) + 1):
            joined = join(first, second, self_edge, other_edge)

            assert joined.is_valid()
            assert joined.n_components == first.n_components + second.n_components - 1
            for edge in range(1, 2 * len(joined.pd_code) + 1):
                joined._get_forth_index(edge)


def test_connected_sum_accepts_generic_knot_diagrams():
    composite_knot = join(TREFOIL, TREFOIL, 1, 1)
    other_knot = FIGURE_EIGHT

    result = connected_sum(composite_knot, other_knot)

    assert result.is_valid()
    assert result.n_components == 1
    assert len(result.pd_code) == len(composite_knot.pd_code) + len(other_knot.pd_code)


def test_connected_sum_rejects_link_diagrams():
    with pytest.raises(ValueError, match="requires knot diagrams"):
        connected_sum(HOPF_LINK, TREFOIL)


def test_join_rejects_edges_outside_their_diagrams():
    with pytest.raises(ValueError, match="self_edge"):
        join(TREFOIL, FIGURE_EIGHT, 0, 1)

    with pytest.raises(ValueError, match="other_edge"):
        join(TREFOIL, FIGURE_EIGHT, 1, 9)
