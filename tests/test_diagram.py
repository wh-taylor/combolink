from unknotter.diagram import Diagram


def test_diagram_equality_with_non_diagram_objects():
    diagram = Diagram([(1, 2, 2, 1)])

    assert diagram != None
    assert diagram != object()


def test_diagram_validity():
    assert Diagram([(1, 2, 2, 1)]).is_valid()
    assert not Diagram([(1, 2, 2, 3)]).is_valid()
    assert not Diagram([(1, 2, 2)]).is_valid()
