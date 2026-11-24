from combolink.diagram import *


def reverse(self: Diagram) -> Diagram:
    """Return a diagram with opposite orientation of `diagram`."""
    return Diagram([(d, c, b, a) for (a, b, c, d) in self.pd_code])


def reflect(self: Diagram) -> Diagram:
    """Return a diagram of the reflection of the link of `diagram`."""
    return Diagram([(a, d, c, b) for (a, b, c, d) in self.pd_code])

def disjoint_union(self, *others: Diagram):
    """Return the disjoint union of any number of diagrams."""
    result = self
    for other in others:
        result = _disjoint_union(result, other)
    return result

def _disjoint_union(self: Diagram, other: Diagram) -> Diagram:
    """Return the disjoint union of two diagrams."""
    if not self.is_valid() or not other.is_valid():
        raise ValueError("cannot combine invalid diagrams.")

    other_shifted = other._shift_unbounded(2 * len(self.pd_code))
    return Diagram(self.pd_code + other_shifted.pd_code)


def _head_occurrences(
    diagram: Diagram, edge_shift: int, crossing_shift: int
) -> dict[Edge, tuple[int, int]]:
    result: dict[Edge, tuple[int, int]] = {}
    for edge in range(1, 2 * len(diagram.pd_code) + 1):
        try:
            crossing_index, edge_index = diagram._get_forth_index(edge)
        except NotImplementedError as error:
            raise ValueError("join requires oriented diagram edges.") from error
        result[edge + edge_shift] = (
            crossing_index + crossing_shift,
            edge_index,
        )
    return result


def _forward_occurrences(
    diagram: Diagram, edge: Edge, crossing_shift: int = 0
) -> list[tuple[int, int]]:
    next_edge = diagram._next(edge)
    return [
        (crossing_index + crossing_shift, edge_index)
        for crossing_index, crossing in enumerate(diagram.pd_code)
        for edge_index, crossing_edge in enumerate(crossing)
        if crossing_edge == edge and crossing[(edge_index + 2) % 4] == next_edge
    ]


def _build_joined_candidate(
    original_pd_code: list[list[Edge]],
    heads: dict[Edge, tuple[int, int]],
    self_edge: Edge,
    shifted_other_edge: Edge,
    self_head: tuple[int, int],
    other_head: tuple[int, int],
) -> Diagram | None:
    pd_code = [crossing.copy() for crossing in original_pd_code]
    self_next_index = (self_head[1] + 2) % 4
    other_next_index = (other_head[1] + 2) % 4
    self_next = pd_code[self_head[0]][self_next_index]
    other_next = pd_code[other_head[0]][other_next_index]
    pd_code[self_head[0]][self_next_index] = other_next
    pd_code[other_head[0]][other_next_index] = self_next

    candidate_heads = heads.copy()
    candidate_heads[self_edge] = self_head
    candidate_heads[shifted_other_edge] = other_head
    next_edges = {
        edge: pd_code[crossing_index][(edge_index + 2) % 4]
        for edge, (crossing_index, edge_index) in candidate_heads.items()
    }
    if set(next_edges.values()) != set(next_edges):
        return None

    unvisited = set(next_edges)
    components: list[list[Edge]] = []
    while unvisited:
        start = min(unvisited)
        component = []
        edge = start
        while edge in unvisited:
            unvisited.remove(edge)
            component.append(edge)
            edge = next_edges[edge]
        if edge != start:
            return None
        components.append(component)

    relabeling: dict[Edge, Edge] = {}
    next_label = 1
    for component in components:
        for edge in component:
            relabeling[edge] = next_label
            next_label += 1

    joined_code: PDNotation = [
        (
            relabeling[a],
            relabeling[b],
            relabeling[c],
            relabeling[d],
        )
        for a, b, c, d in pd_code
    ]
    joined = Diagram(joined_code)
    if not joined.is_valid():
        return None
    try:
        for edge in next_edges:
            joined._get_forth_index(relabeling[edge])
    except NotImplementedError:
        return None
    return joined


def connected_sum(self: Diagram, other: Diagram) -> Diagram:
    """Return the connected sum of two knot diagrams."""
    if not self.is_valid() or not other.is_valid():
        raise ValueError("cannot combine invalid diagrams.")
    if self.n_components != 1 or other.n_components != 1:
        raise ValueError("connected_sum requires knot diagrams.")

    return join(self, other, self.components[0][0], other.components[0][0])

def join(self: Diagram, other: Diagram, self_edge: Edge, other_edge: Edge) -> Diagram:
    """Return the joining of two diagrams by given edges (generalizes connected sum)."""
    if not self.is_valid() or not other.is_valid():
        raise ValueError("cannot combine invalid diagrams.")
    if type(self_edge) is not int or self_edge not in range(
        1, 2 * len(self.pd_code) + 1
    ):
        raise ValueError("self_edge must belong to the first diagram.")
    if type(other_edge) is not int or other_edge not in range(
        1, 2 * len(other.pd_code) + 1
    ):
        raise ValueError("other_edge must belong to the second diagram.")

    edge_offset = 2 * len(self.pd_code)
    crossing_offset = len(self.pd_code)
    shifted_other_edge = other_edge + edge_offset

    heads = _head_occurrences(self, 0, 0)
    heads.update(_head_occurrences(other, edge_offset, crossing_offset))
    original_pd_code = [list(crossing) for crossing in self.pd_code]
    original_pd_code.extend(
        list(crossing)
        for crossing in other._shift_unbounded(edge_offset).pd_code
    )

    self_heads = _forward_occurrences(self, self_edge)
    other_heads = _forward_occurrences(other, other_edge, crossing_offset)
    for self_head in self_heads:
        for other_head in other_heads:
            joined = _build_joined_candidate(
                original_pd_code,
                heads,
                self_edge,
                shifted_other_edge,
                self_head,
                other_head,
            )
            if joined is not None:
                return joined
    raise ValueError("the selected edges could not be joined.")
