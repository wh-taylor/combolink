from tests.__init__ import *


def test_trefoil_bracket():
    assert kauffman_bracket(knot(3, 1)) == Polynomial({5: -1, -3: -1, -7: 1})


def test_figure8_bracket():
    assert kauffman_bracket(knot(4, 1)) == Polynomial(
        {-8: 1, -4: -1, 0: 1, 4: -1, 8: 1}
    )


def test_two_component_unlink_bracket():
    unlink = LinkDiagram([(1, 2, 2, 1), (3, 4, 4, 3)])

    assert kauffman_bracket(unlink) == Polynomial({4: -1, 8: -1})


def test_link_properties_reject_an_empty_pd_code():
    with pytest.raises(ValueError):
        kauffman_bracket(LinkDiagram([]))


def test_trefoil_preserve_poke():
    assert kauffman_bracket(knot(3, 1)) == kauffman_bracket(poke(knot(3, 1), 1, 4))
    assert kauffman_bracket(knot(3, 1)) == kauffman_bracket(poke(knot(3, 1), 2, 5))
    assert kauffman_bracket(knot(3, 1)) == kauffman_bracket(poke(knot(3, 1), 3, 6))


def test_figure8_preserve_poke():
    assert kauffman_bracket(knot(4, 1)) == kauffman_bracket(poke(knot(4, 1), 1, 4))
    assert kauffman_bracket(knot(4, 1)) == kauffman_bracket(poke(knot(4, 1), 3, 8))
    assert kauffman_bracket(knot(4, 1)) == kauffman_bracket(poke(knot(4, 1), 2, 5))
