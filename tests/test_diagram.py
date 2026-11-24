from unknotter import reflect, reverse
from unknotter.diagram import Diagram


def test_diagram_equality_with_non_diagram_objects():
    diagram = Diagram([(1, 2, 2, 1)])

    assert diagram != None
    assert diagram != object()


def test_diagram_validity():
    assert Diagram([(1, 2, 2, 1)]).is_valid()
    assert not Diagram([(1, 2, 2, 3)]).is_valid()
    assert not Diagram([(1, 2, 2)]).is_valid()


def test_link_components_are_derived_from_pd_code():
    hopf_link = Diagram([(1, 4, 2, 3), (3, 2, 4, 1)])

    assert hopf_link.is_valid()
    assert hopf_link.n_components == 2
    assert hopf_link.components == ((1, 2), (3, 4))


def test_crossingless_links_require_an_explicit_component_count():
    unknot = Diagram([])
    two_component_unlink = Diagram([], n_components=2)

    assert unknot.components == ((),)
    assert two_component_unlink.components == ((), ())
    assert unknot != two_component_unlink
    assert Diagram([], n_components=2).is_valid()
    assert reverse(two_component_unlink).n_components == 2
    assert reflect(two_component_unlink).n_components == 2
