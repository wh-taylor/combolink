from tests.__init__ import *


def test_to_graph_encodes_the_six_tuple_and_pd_rotation_face_cycles():
    diagram = knot(3, 1)

    model = to_graph(diagram)

    assert model.n_crossings == 3
    assert model.n_edges == 6
    assert model.n_link_components == 1
    assert len(model.face_cycles) == 5
    assert model.to_pd_code() == diagram.pd_code
    assert sum(crossing.writhe for crossing in model.vertices) == get_writhe(
        diagram
    )
    assert model.n_crossings - model.n_edges + len(model.face_cycles) == 2

    incidence = {edge.label: edge.incidence for edge in model.edges}
    successor = {edge.label: edge.successor for edge in model.edges}
    for edge, (_, target) in incidence.items():
        assert incidence[successor[edge]][0] == target
    for crossing in model.vertices:
        assert incidence[crossing.principal_edge][1] == crossing.index

    all_positions = {position for cycle in model.face_cycles for position in cycle}
    expected_positions = {
        (crossing.index, position)
        for crossing in model.vertices
        for position in range(4)
    }
    assert all_positions == expected_positions
    assert sum(len(cycle) for cycle in model.face_cycles) == 4 * model.n_crossings


def test_to_graph_keeps_link_components_and_crossing_incidence():
    hopf_link = LinkDiagram([(1, 4, 2, 3), (3, 2, 4, 1)])

    model = to_graph(hopf_link)

    assert model.n_link_components == 2
    assert model.projection_components == ((0, 1),)
    assert len(model.face_cycles) == 4
    assert model.to_pd_code() == hopf_link.pd_code


def test_pd_rotation_face_cycles_support_both_crossing_signs():
    diagrams = (knot(3, 1), reflect(knot(3, 1)), knot(4, 1))
    models = tuple(to_graph(diagram) for diagram in diagrams)

    assert {
        crossing.writhe for model in models for crossing in model.vertices
    } == {-1, 1}
    for diagram, model in zip(diagrams, models, strict=True):
        assert model.to_pd_code() == diagram.pd_code
        assert (
            model.n_crossings - model.n_edges + len(model.face_cycles)
            == 2 * len(model.projection_components)
        )

        edge_positions = {}
        for cycle in model.face_cycles:
            for crossing_position in cycle:
                vertex, position = crossing_position
                edge = diagram.pd_code[vertex][position]
                edge_positions.setdefault(edge, []).append(crossing_position)
        for cycle in model.face_cycles:
            wrapped_cycle = cycle[1:] + cycle[:1]
            for crossing_position, next_position in zip(
                cycle, wrapped_cycle, strict=True
            ):
                vertex, position = crossing_position
                edge = diagram.pd_code[vertex][position]
                opposite = next(
                    other
                    for other in edge_positions[edge]
                    if other != crossing_position
                )
                assert next_position == (opposite[0], (opposite[1] + 1) % 4)


def test_to_graph_checks_face_cycles_componentwise_for_split_projection():
    unlink = LinkDiagram([(1, 2, 2, 1), (3, 4, 4, 3)])

    model = to_graph(unlink)

    assert model.projection_components == ((0,), (1,))
    assert model.n_link_components == 2
    assert len(model.face_cycles) == 6
    assert (
        model.n_crossings - model.n_edges + len(model.face_cycles)
        == 2 * len(model.projection_components)
    )


def test_to_graph_rejects_non_spherical_crossing_rotations():
    non_planar = LinkDiagram(
        [(2, 6, 3, 1), (1, 5, 2, 6), (3, 4, 4, 5)]
    )

    assert non_planar.is_valid()
    with pytest.raises(ValueError, match="spherical planar"):
        to_graph(non_planar)


def test_to_graph_rejects_invalid_diagrams():
    # Empty PD codes are not valid LinkDiagram instances.
    with pytest.raises(ValueError, match="invalid"):
        to_graph(LinkDiagram([1, 1, 1, 1]))
