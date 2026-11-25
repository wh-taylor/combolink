from tests.__init__ import *


def test_diagram_equality_with_non_diagram_objects():
    diagram = LinkDiagram([(1, 2, 2, 1)])

    assert diagram != None
    assert diagram != object()


def test_diagram_validity():
    assert LinkDiagram([(1, 2, 2, 1)]).is_valid()
    assert not LinkDiagram([1, 1, 1, 1]).is_valid()
    assert not LinkDiagram([(1, 2, 2, 3)]).is_valid()
    assert not LinkDiagram([(1, 2, 2)]).is_valid()


def test_link_components_are_derived_from_pd_code():
    hopf_link = LinkDiagram([(1, 4, 2, 3), (3, 2, 4, 1)])

    assert hopf_link.is_valid()
    assert hopf_link.n_components == 2
    assert hopf_link.components_edges == ((1, 2), (3, 4))


def test_unlink_components_use_single_crossing_unknot_forms():
    unlink = LinkDiagram([(1, 2, 2, 1), (3, 4, 4, 3)])

    assert unlink.is_valid()
    assert unlink.n_components == 2
    assert unlink.components_edges == ((1, 2), (3, 4))
    assert reverse(unlink).n_components == 2
    assert reflect(unlink).n_components == 2
