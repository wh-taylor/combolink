from dataclasses import dataclass
from typing import TypeAlias

from combolink.diagram import Edge, LinkDiagram, PDNotation

_CrossingPosition: TypeAlias = tuple[int, int]


@dataclass(frozen=True, slots=True)
class GraphCrossing:
    """A crossing vertex with its writhe and principal incoming edge.

    Parameters
    ----------
    index : int
        Zero-based crossing index in source PD row order.
    writhe : int
        Crossing sign, either ``-1`` or ``+1``.
    principal_edge : Edge
        Label of the incoming under-crossing edge selected by pi.
    """

    index: int
    writhe: int
    principal_edge: Edge


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """A directed diagram edge with its incidence and strand successor.

    Parameters
    ----------
    label : Edge
        Original PD edge label.
    incidence : tuple of int
        Source and target crossing indices, the incidence function psi.
    successor : Edge
        Label of the next edge along the oriented strand, the permutation S.
    """

    label: Edge
    incidence: tuple[int, int]
    successor: Edge


@dataclass(frozen=True, slots=True)
class CombinatorialLinkDiagram:
    """The six-tuple model, with derived face-boundary data.

    ``vertices`` and ``edges`` are records for V and E. Each edge stores its
    incidence and successor; each crossing stores its writhe and principal
    edge. ``face_cycles`` are derived directly from the PD crossing rotations
    as cycles of crossing positions. For disconnected projections these are
    boundary walks, not necessarily distinct complementary regions.

    Parameters
    ----------
    vertices : tuple of GraphCrossing
        Crossing vertices, indexed in source PD row order.
    edges : tuple of GraphEdge
        Directed diagram edges, retaining their original PD labels.
    face_cycles : tuple of tuple of ``(vertex, position)`` pairs
        Boundary walks derived from the PD crossing rotations.
    link_components : tuple of tuple of Edge
        Cycles of S, grouped by oriented link component.
    projection_components : tuple of tuple of int
        Connected components of the underlying crossing graph.
    """

    vertices: tuple[GraphCrossing, ...]
    edges: tuple[GraphEdge, ...]
    face_cycles: tuple[tuple[_CrossingPosition, ...], ...]
    link_components: tuple[tuple[Edge, ...], ...]
    projection_components: tuple[tuple[int, ...], ...]

    @property
    def n_crossings(self) -> int:
        """Return the number of crossing vertices."""
        return len(self.vertices)

    @property
    def n_edges(self) -> int:
        """Return the number of directed diagram edges."""
        return len(self.edges)

    @property
    def n_link_components(self) -> int:
        """Return the number of cycles of the strand-successor permutation."""
        return len(self.link_components)

    def to_pd_code(self) -> PDNotation:
        """Reconstruct the original PD code, including its edge labels.

        Returns
        -------
        PDNotation
            Crossing tuples in their original row order.
        """
        edge_by_label = {edge.label: edge for edge in self.edges}
        incoming_by_vertex: dict[int, list[Edge]] = {
            crossing.index: [] for crossing in self.vertices
        }
        for edge in self.edges:
            incoming_by_vertex[edge.incidence[1]].append(edge.label)
        pd_code: PDNotation = []

        for crossing in self.vertices:
            under_in = crossing.principal_edge
            over_in = next(
                edge
                for edge in incoming_by_vertex[crossing.index]
                if edge != under_in
            )
            under_out = edge_by_label[under_in].successor
            over_out = edge_by_label[over_in].successor

            if crossing.writhe == -1:
                pd_code.append((under_in, over_in, under_out, over_out))
            else:
                pd_code.append((under_in, over_out, under_out, over_in))

        return pd_code


def _projection_components(
    vertices: tuple[int, ...],
    incidence: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, ...], ...]:
    """Find connected components in the underlying crossing graph."""
    adjacent: dict[int, set[int]] = {vertex: set() for vertex in vertices}
    for source, target in incidence:
        adjacent[source].add(target)
        adjacent[target].add(source)

    remaining = set(vertices)
    components: list[tuple[int, ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = []
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for neighbor in adjacent[vertex] & remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(components)


def _face_cycles(
    edge_occurrences: dict[Edge, list[_CrossingPosition]],
) -> tuple[tuple[_CrossingPosition, ...], ...]:
    """Trace face-boundary walks by crossing each edge and turning at its end."""
    opposite_position: dict[_CrossingPosition, _CrossingPosition] = {}
    for occurrences in edge_occurrences.values():
        first, second = occurrences
        opposite_position[first] = second
        opposite_position[second] = first

    unvisited = set(opposite_position)
    cycles: list[tuple[_CrossingPosition, ...]] = []

    for start in sorted(unvisited):
        if start not in unvisited:
            continue
        cycle = []
        current = start
        while current in unvisited:
            unvisited.remove(current)
            cycle.append(current)
            across_vertex, across_position = opposite_position[current]
            current = (across_vertex, (across_position + 1) % 4)
        if current != start:
            raise ValueError("PD face walk did not close into a boundary cycle.")
        cycles.append(tuple(cycle))

    return tuple(cycles)


def _edge_occurrences(
    pd_code: PDNotation,
) -> dict[Edge, list[_CrossingPosition]]:
    """Map each PD edge label to its two crossing positions."""
    occurrences: dict[Edge, list[_CrossingPosition]] = {}
    for vertex, crossing in enumerate(pd_code):
        for position, edge in enumerate(crossing):
            occurrences.setdefault(edge, []).append((vertex, position))
    if any(len(positions) != 2 for positions in occurrences.values()):
        raise ValueError("each PD edge must occur at exactly two crossing positions.")
    return occurrences


def _strand_successors(
    diagram: LinkDiagram,
) -> tuple[tuple[tuple[Edge, ...], ...], dict[Edge, Edge]]:
    """Get oriented component cycles and the successor map S."""
    link_components = tuple(tuple(component) for component in diagram.components_edges)
    successors = {
        edge: component[(index + 1) % len(component)]
        for component in link_components
        for index, edge in enumerate(component)
    }
    return link_components, successors


def _record_endpoint(
    endpoint_roles: dict[Edge, dict[str, int]],
    edge: Edge,
    role: str,
    vertex: int,
) -> None:
    """Record an edge's tail or head crossing, rejecting duplicate endpoints."""
    if role in endpoint_roles[edge]:
        raise ValueError(f"PD edge {edge} has multiple {role} endpoints.")
    endpoint_roles[edge][role] = vertex


def _crossing_records(
    pd_code: PDNotation,
    edges: tuple[Edge, ...],
    successors: dict[Edge, Edge],
) -> tuple[tuple[GraphCrossing, ...], dict[Edge, dict[str, int]]]:
    """Compile crossing writhe, principal edges, and directed endpoints."""
    endpoint_roles: dict[Edge, dict[str, int]] = {edge: {} for edge in edges}
    crossings: list[GraphCrossing] = []

    for vertex, (under_in, over_first, under_out, over_second) in enumerate(
        pd_code
    ):
        if successors[under_in] != under_out:
            raise ValueError(
                "PD crossing positions do not match the diagram's oriented "
                "under-strand successor."
            )

        if successors[over_first] == over_second:
            writhe = -1
            over_in, over_out = over_first, over_second
        elif successors[over_second] == over_first:
            writhe = 1
            over_in, over_out = over_second, over_first
        else:
            raise ValueError(
                "PD crossing positions do not match the diagram's oriented "
                "over-strand successor."
            )

        crossings.append(
            GraphCrossing(
                index=vertex,
                writhe=writhe,
                principal_edge=under_in,
            )
        )
        _record_endpoint(endpoint_roles, under_in, "head", vertex)
        _record_endpoint(endpoint_roles, under_out, "tail", vertex)
        _record_endpoint(endpoint_roles, over_in, "head", vertex)
        _record_endpoint(endpoint_roles, over_out, "tail", vertex)

    return tuple(crossings), endpoint_roles


def _graph_edges(
    edge_labels: tuple[Edge, ...],
    crossings: tuple[GraphCrossing, ...],
    endpoint_roles: dict[Edge, dict[str, int]],
    successors: dict[Edge, Edge],
) -> tuple[GraphEdge, ...]:
    """Build directed edges and validate the six-tuple incidence rules."""
    incidence_by_edge: dict[Edge, tuple[int, int]] = {}
    for edge in edge_labels:
        roles = endpoint_roles[edge]
        if set(roles) != {"tail", "head"}:
            raise ValueError(
                f"PD edge {edge} must have one oriented tail and one head."
            )
        incidence_by_edge[edge] = (roles["tail"], roles["head"])

    if set(successors.values()) != set(edge_labels):
        raise ValueError("strand continuation must be a permutation of the edges.")

    incoming_count = [0] * len(crossings)
    outgoing_count = [0] * len(crossings)
    for edge, (source, target) in incidence_by_edge.items():
        outgoing_count[source] += 1
        incoming_count[target] += 1
        if incidence_by_edge[successors[edge]][0] != target:
            raise ValueError("successor edges do not meet at the same crossing.")

    if any(count != 2 for count in incoming_count + outgoing_count):
        raise ValueError("each crossing must have in-degree and out-degree two.")
    for crossing in crossings:
        if incidence_by_edge[crossing.principal_edge][1] != crossing.index:
            raise ValueError("each principal edge must be incoming at its crossing.")

    return tuple(
        GraphEdge(
            label=edge,
            incidence=incidence_by_edge[edge],
            successor=successors[edge],
        )
        for edge in edge_labels
    )


def _validate_spherical_planarity(
    crossings: tuple[GraphCrossing, ...],
    edges: tuple[GraphEdge, ...],
    face_cycles: tuple[tuple[_CrossingPosition, ...], ...],
) -> tuple[tuple[int, ...], ...]:
    """Check the spherical Euler condition for each projection component."""
    vertices = tuple(crossing.index for crossing in crossings)
    incidence = tuple(edge.incidence for edge in edges)
    components = _projection_components(vertices, incidence)
    component_by_vertex = {
        vertex: component_index
        for component_index, component in enumerate(components)
        for vertex in component
    }
    face_counts = [0] * len(components)

    for face in face_cycles:
        component_index = component_by_vertex[face[0][0]]
        if any(
            component_by_vertex[vertex] != component_index
            for vertex, _ in face
        ):
            raise ValueError("a face cycle crosses projection components.")
        face_counts[component_index] += 1

    for component_index, component in enumerate(components):
        edge_count = sum(edge.incidence[0] in component for edge in edges)
        if len(component) - edge_count + face_counts[component_index] != 2:
            raise ValueError(
                "crossing rotations do not describe spherical planar "
                "components: each component must satisfy V - E + F = 2."
            )

    return components


def to_graph(diagram: LinkDiagram) -> CombinatorialLinkDiagram:
    """Compile a valid link diagram into the paper's combinatorial model.

    The six core fields encode ``(V, E, psi, w, S, pi)``. PD edge labels are
    retained as edge identities. Face cycles are traced directly from the PD
    crossing rotations and checked for spherical planarity component by
    component.

    Parameters
    ----------
    diagram : LinkDiagram
        Valid oriented diagram to compile.

    Returns
    -------
    CombinatorialLinkDiagram
        The six-tuple data together with its face-boundary cycles.

    Raises
    ------
    TypeError
        If ``diagram`` is not a ``LinkDiagram``.
    ValueError
        If the diagram is invalid or its crossing rotations are not spherical
        planar.
    """
    if not isinstance(diagram, LinkDiagram):
        raise TypeError("diagram must be a LinkDiagram.")
    if not diagram.is_valid():
        raise ValueError("cannot compile an invalid link diagram.")

    pd_code = list(diagram.crossings)
    edge_occurrences = _edge_occurrences(pd_code)
    edge_labels = tuple(sorted(edge_occurrences))
    link_components, successors = _strand_successors(diagram)
    crossings, endpoint_roles = _crossing_records(
        pd_code,
        edge_labels,
        successors,
    )
    edges = _graph_edges(edge_labels, crossings, endpoint_roles, successors)
    faces = _face_cycles(edge_occurrences)
    projection_components = _validate_spherical_planarity(
        crossings,
        edges,
        faces,
    )

    return CombinatorialLinkDiagram(
        vertices=crossings,
        edges=edges,
        face_cycles=faces,
        link_components=link_components,
        projection_components=projection_components,
    )
