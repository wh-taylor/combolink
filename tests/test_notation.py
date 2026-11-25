from tests.__init__ import *


HOPF_LINK = LinkDiagram([(1, 4, 2, 3), (3, 2, 4, 1)])


def test_gauss_code_uses_pd_row_ids_and_over_under_signs():
    assert gauss_code(TREFOIL) == [[2, -1, 3, -2, 1, -3]]


def test_gauss_code_returns_one_sequence_per_component():
    assert gauss_code(HOPF_LINK) == [[-1, 2], [1, -2]]


def test_dt_notation_returns_classical_sequence_for_a_knot():
    assert dt_notation(TREFOIL) == [4, 6, 2]


def test_dt_notation_negates_an_even_overcrossing():
    diagram = LinkDiagram([(1, 1, 2, 2)])

    assert dt_notation(diagram) == [-2]


def test_notation_handles_repeated_edge_labels_at_a_crossing():
    diagram = LinkDiagram([(1, 1, 2, 2)])

    assert gauss_code(diagram) == [[-1, 1]]


def test_dt_notation_rejects_multi_component_diagrams():
    with pytest.raises(ValueError, match="single-component"):
        dt_notation(HOPF_LINK)


@pytest.mark.parametrize("notation", [gauss_code, dt_notation])
def test_notation_rejects_invalid_diagrams(notation):
    with pytest.raises(ValueError, match="invalid diagram"):
        notation(LinkDiagram([1, 1, 1, 1]))
