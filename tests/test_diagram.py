from unknotter import reflect, reverse
from unknotter.diagram import Diagram


def test_diagram_equality_with_non_diagram_objects():
    diagram = Diagram([(1, 2, 2, 1)])

    assert diagram != None
    assert diagram != object()


def test_diagram_validity():
    assert Diagram([(1, 2, 2, 1)]).is_valid()
    assert not Diagram([]).is_valid()
    assert not Diagram([(1, 2, 2, 3)]).is_valid()
    assert not Diagram([(1, 2, 2)]).is_valid()


def test_link_components_are_derived_from_pd_code():
    hopf_link = Diagram([(1, 4, 2, 3), (3, 2, 4, 1)])

    assert hopf_link.is_valid()
    assert hopf_link.n_components == 2
    assert hopf_link.components == ((1, 2), (3, 4))


def test_unlink_components_use_single_crossing_unknot_forms():
    unlink = Diagram([(1, 2, 2, 1), (3, 4, 4, 3)])

    assert unlink.is_valid()
    assert unlink.n_components == 2
    assert unlink.components == ((1, 2), (3, 4))
    assert reverse(unlink).n_components == 2
    assert reflect(unlink).n_components == 2
