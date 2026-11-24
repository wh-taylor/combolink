from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
import math
import random
import time
from combolink.diagram import *
from combolink.properties import get_edges, is_infinity_unknot


class MoveKind(str, Enum):
    LEFT_POSITIVE_TWIST = "left_positive_twist"
    LEFT_NEGATIVE_TWIST = "left_negative_twist"
    RIGHT_POSITIVE_TWIST = "right_positive_twist"
    RIGHT_NEGATIVE_TWIST = "right_negative_twist"
    UNTWIST = "untwist"
    POKE = "poke"
    UNPOKE = "unpoke"
    SLIDE = "slide"

    def __str__(self) -> str:
        return "".join(part.title() for part in self.name.split("_"))

    def __repr__(self) -> str:
        return str(self)


_MOVE_ARITIES = {
    MoveKind.LEFT_POSITIVE_TWIST: 1,
    MoveKind.LEFT_NEGATIVE_TWIST: 1,
    MoveKind.RIGHT_POSITIVE_TWIST: 1,
    MoveKind.RIGHT_NEGATIVE_TWIST: 1,
    MoveKind.UNTWIST: 1,
    MoveKind.POKE: 2,
    MoveKind.UNPOKE: 2,
    MoveKind.SLIDE: 3,
}


@dataclass(frozen=True)
class Move:
    """A Reidemeister move and its ordered edge arguments."""

    kind: MoveKind
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MoveKind):
            raise TypeError("kind must be a MoveKind.")
        if not isinstance(self.edges, tuple):
            raise TypeError("edges must be a tuple.")
        if len(self.edges) != _MOVE_ARITIES[self.kind]:
            raise ValueError(
                f"{self.kind.value} requires {_MOVE_ARITIES[self.kind]} edge(s)."
            )
        if any(type(edge) is not int or edge < 1 for edge in self.edges):
            raise ValueError("move edges must be positive integers.")
        if self.kind in (MoveKind.POKE, MoveKind.UNPOKE, MoveKind.SLIDE):
            if len(set(self.edges)) != len(self.edges):
                raise ValueError(f"{self.kind.value} requires distinct edges.")

    def __str__(self) -> str:
        return f"Move({self.kind}, {self.edges!r})"

    def __repr__(self) -> str:
        return str(self)


def _is_unpokable(self: Diagram, edge1: Edge, edge2: Edge) -> bool:
    """Return whether the edges have the crossing pattern for an R2 removal."""
    return any((
        self._is_open(edge1) and self._is_closed(edge2),
        self._is_open(edge2) and self._is_closed(edge1),
    ))

def _is_slidable(self: Diagram, edge1: Edge, edge2: Edge, edge3: Edge) -> bool:
    """Return whether the edges have the crossing pattern for an R3 move."""
    return any((
        self._is_open(edge1) and self._is_closed(edge2) and self._is_half_open(edge3),
        self._is_open(edge1) and self._is_closed(edge3) and self._is_half_open(edge2),
        self._is_open(edge2) and self._is_closed(edge1) and self._is_half_open(edge3),
        self._is_open(edge2) and self._is_closed(edge3) and self._is_half_open(edge1),
        self._is_open(edge3) and self._is_closed(edge1) and self._is_half_open(edge2),
        self._is_open(edge3) and self._is_closed(edge2) and self._is_half_open(edge1),
    ))


def _projection_component_ids(self: Diagram) -> dict[Edge, int]:
    """Map each edge to its connected component in the crossing projection."""
    crossing_indices_by_edge: dict[Edge, set[int]] = {}
    for crossing_index, crossing in enumerate(self.pd_code):
        for edge in crossing:
            crossing_indices_by_edge.setdefault(edge, set()).add(crossing_index)

    crossing_component_ids: dict[int, int] = {}
    component_id = 0
    for start in range(len(self.pd_code)):
        if start in crossing_component_ids:
            continue
        crossing_component_ids[start] = component_id
        stack = [start]
        while stack:
            crossing_index = stack.pop()
            for edge in self.pd_code[crossing_index]:
                for adjacent in crossing_indices_by_edge[edge]:
                    if adjacent not in crossing_component_ids:
                        crossing_component_ids[adjacent] = component_id
                        stack.append(adjacent)
        component_id += 1

    return {
        edge: crossing_component_ids[next(iter(indices))]
        for edge, indices in crossing_indices_by_edge.items()
    }


def get_twistables(self: Diagram) -> list[Edge]:
    """Return the list of edges that can be twisted (which is all of them)."""
    return get_edges(self)

def get_untwistables(self: Diagram) -> list[Edge]:
    """Return the list of edges that can be untwisted."""
    if is_infinity_unknot(self):
        return []

    untwistables = []
    for crossing in self.pd_code:
        if len(set(crossing)) == 3:
            untwistables.append(max(set(crossing), key=crossing.count))
        elif len(set(crossing)) == 2 and all(
            crossing.count(edge) == 2 for edge in set(crossing)
        ):
            untwistables.extend(dict.fromkeys(crossing))
    return untwistables

def get_pokables(self: Diagram) -> list[tuple[Edge, Edge]]:
    """Return the list of ordered pairs of edges that can be poked."""
    pokables = []
    for edge in get_edges(self):
        pokable_with = []
        face_ccw, face_cw = self._get_adjacent_faces(edge)
        for signed_edge in face_ccw + face_cw:
            adj_edge = abs(signed_edge)
            if adj_edge != edge and adj_edge not in pokable_with:
                pokable_with.append(adj_edge)
        pokables += ((edge, e) for e in pokable_with)

    projection_components = _projection_component_ids(self)
    edges_by_component: dict[int, list[Edge]] = {}
    for edge, component_id in projection_components.items():
        edges_by_component.setdefault(component_id, []).append(edge)
    seen = set(pokables)
    component_edges = list(edges_by_component.values())
    # PD codes omit nesting, so disconnected projections use an exterior-face convention.
    for index, edges in enumerate(component_edges):
        for other_edges in component_edges[index + 1:]:
            for edge in edges:
                for other_edge in other_edges:
                    for pair in ((edge, other_edge), (other_edge, edge)):
                        if pair not in seen:
                            pokables.append(pair)
                            seen.add(pair)
    return pokables

def get_unpokables(self: Diagram) -> list[tuple[Edge, Edge]]:
    """Return the list of ordered pairs of edges that can be unpoked."""
    unpokables = []
    for edge in get_edges(self):
        if any(edge in pair for pair in unpokables):
            continue
        face_ccw, face_cw = self._get_adjacent_faces(edge)
        if len(face_ccw) == 2 and _is_unpokable(self, *[abs(n) for n in face_ccw]):
            candidate = tuple(sorted(abs(n) for n in face_ccw))
            if (
                sum(all(part in crossing for part in candidate) for crossing in self.pd_code) == 2
                and candidate not in unpokables
            ):
                unpokables.append(candidate)
        if len(face_cw) == 2 and _is_unpokable(self, *[abs(n) for n in face_cw]):
            candidate = tuple(sorted(abs(n) for n in face_cw))
            if (
                sum(all(part in crossing for part in candidate) for crossing in self.pd_code) == 2
                and candidate not in unpokables
            ):
                unpokables.append(candidate)
    return unpokables

def get_slidables(self: Diagram) -> list[tuple[Edge, Edge, Edge]]:
    """Return the list of ordered triplets of edges that can be slid."""
    slidables = []
    for edge in get_edges(self):
        if any(edge in triplet for triplet in slidables):
            continue
        face_ccw, face_cw = self._get_adjacent_faces(edge)
        if len(face_ccw) == 3 and _is_slidable(self, *[abs(n) for n in face_ccw]):
                slidables.append(tuple(sorted(abs(n) for n in face_ccw)))
        if len(face_cw) == 3 and _is_slidable(self, *[abs(n) for n in face_cw]):
                slidables.append(tuple(sorted(abs(n) for n in face_cw)))
    return slidables

def _has_oriented_edge_cycles(self: Diagram) -> bool:
    """Return whether every edge has an oriented crossing it faces toward."""
    if not self.is_valid():
        return False
    try:
        for edge in range(1, 2 * len(self.pd_code) + 1):
            self._get_forth_index(edge)
    except NotImplementedError:
        return False
    return True


def _preserve_component_count(pd_code: PDNotation, component_count: int) -> Diagram:
    """Restore missing components with single-crossing unknot diagrams."""
    current_count = 0
    if pd_code:
        candidate = Diagram(pd_code)
        if not candidate.is_valid():
            raise ReidemeisterError("move produced an invalid PD code.")
        current_count = candidate.n_components
    if current_count > component_count:
        raise ReidemeisterError("move changed the number of link components.")
    while current_count < component_count:
        first_edge = 2 * len(pd_code) + 1
        pd_code.append(
            (first_edge, first_edge + 1, first_edge + 1, first_edge)
        )
        current_count += 1
    return Diagram(pd_code)


def _relabel_after_contractions(
    pd_code: PDNotation,
    components: tuple[tuple[Edge, ...], ...],
    merged_edges: dict[Edge, Edge],
    removed_edges: set[Edge],
) -> PDNotation:
    """Relabel edges after removing crossings and merging adjacent arcs."""
    component_orders: list[list[Edge]] = []
    for component in components:
        order = []
        for edge in component:
            if edge in removed_edges:
                continue
            representative = merged_edges.get(edge, edge)
            if not order or order[-1] != representative:
                order.append(representative)
        if len(order) > 1 and order[0] == order[-1]:
            order.pop()
        if order:
            component_orders.append(order)

    labels: dict[Edge, Edge] = {}
    next_label = 1
    for order in component_orders:
        for edge in order:
            labels[edge] = next_label
            next_label += 1

    old_to_new: dict[Edge, Edge] = {}
    for component in components:
        for edge in component:
            if edge in removed_edges:
                continue
            representative = merged_edges.get(edge, edge)
            if representative not in labels:
                raise ReidemeisterError("could not reconnect the remaining PD edges.")
            old_to_new[edge] = labels[representative]

    try:
        return [
            (
                old_to_new[a],
                old_to_new[b],
                old_to_new[c],
                old_to_new[d],
            )
            for a, b, c, d in pd_code
        ]
    except KeyError as error:
        raise ReidemeisterError("removed crossing left an unmatched PD edge.") from error


def _prepare_twist(
    self: Diagram,
    target_edge: Edge,
    retained_occurrence: tuple[int, int],
) -> PDNotation:
    """Readjust the edge values of `diagram` with the expectation of a twist at `target_edge`."""
    pd_code: PDNotation = []
    target_occurrences = [
        (crossing_index, edge_index)
        for crossing_index, crossing in enumerate(self.pd_code)
        for edge_index, edge in enumerate(crossing)
        if edge == target_edge
    ]
    if len(target_occurrences) != 2:
        raise ReidemeisterError("given edge does not occur twice in the diagram.")

    # Map over each edge in each crossing of `diagram`.
    for crossing_index, crossing in enumerate(self.pd_code):
        new_crossing_as_list: list[Edge] = []
        for edge_index, edge in enumerate(crossing):
            if edge > target_edge:
                new_crossing_as_list.append(edge + 2)
            elif edge == target_edge and (crossing_index, edge_index) != retained_occurrence:
                new_crossing_as_list.append(edge + 2)
            else:
                new_crossing_as_list.append(edge)
        new_crossing: Crossing = (
            new_crossing_as_list[0],
            new_crossing_as_list[1],
            new_crossing_as_list[2],
            new_crossing_as_list[3],
        )
        pd_code.append(new_crossing)
    
    return pd_code


def _twist(self: Diagram, edge: Edge, crossing: Crossing) -> Diagram:
    """Apply a specified crossing pattern as a Reidemeister I move."""
    occurrences = [
        (crossing_index, edge_index)
        for crossing_index, row in enumerate(self.pd_code)
        for edge_index, crossing_edge in enumerate(row)
        if crossing_edge == edge
    ]
    fallback = None
    for retained_occurrence in occurrences:
        pd_code = _prepare_twist(self, edge, retained_occurrence)
        candidate = Diagram(pd_code + [crossing])
        if fallback is None and candidate.is_valid():
            fallback = candidate
        if _has_oriented_edge_cycles(candidate):
            return candidate
    if self.n_components == 1 and fallback is not None:
        return fallback
    raise ReidemeisterError("could not orient the resulting twist.")

def left_positive_twist(self: Diagram, edge: Edge) -> Diagram:
    """Apply a left-positive twist on `edge`."""
    if is_infinity_unknot(self):
        if edge == 1:
            return Diagram([(1, 2, 2, 3), (3, 1, 4, 4)])
        if edge == 2:
            return Diagram([(1, 4, 2, 1), (3, 2, 4, 3)])
    if edge == 1 or edge == 2*len(self.pd_code):
        return left_positive_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge, edge + 2, edge + 1, edge + 1))

def left_negative_twist(self: Diagram, edge: Edge) -> Diagram:
    """Apply a left-negative twist on `edge`."""
    if is_infinity_unknot(self):
        if edge == 1:
            return Diagram([(1, 2, 2, 3), (4, 3, 1, 4)])
        if edge == 2:
            return Diagram([(1, 4, 2, 1), (2, 4, 3, 3)])
    if edge == 1 or edge == 2*len(self.pd_code):
        return left_negative_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge + 1, edge, edge + 2, edge + 1))

def right_positive_twist(self: Diagram, edge: Edge) -> Diagram:
    """Apply a right-positive twist on `edge`."""
    if is_infinity_unknot(self):
        if edge == 1:
            return Diagram([(1, 2, 2, 3), (3, 4, 4, 1)])
        if edge == 2:
            return Diagram([(1, 4, 2, 1), (3, 3, 4, 2)])
    if edge == 1 or edge == 2*len(self.pd_code):
        return right_positive_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge + 1, edge + 1, edge + 2, edge))

def right_negative_twist(self: Diagram, edge: Edge) -> Diagram:
    """Apply a right-negative twist on `edge`."""
    if is_infinity_unknot(self):
        if edge == 1:
            return Diagram([(1, 2, 2, 3), (4, 4, 1, 3)])
        if edge == 2:
            return Diagram([(1, 4, 2, 1), (2, 3, 3, 4)])
    if edge == 1 or edge == 2*len(self.pd_code):
        return right_negative_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge, edge + 1, edge + 1, edge + 2))

def untwist(self: Diagram, edge: Edge) -> Diagram:
    """Remove the twist adjacent to the given edge."""
    crossing_index = next(
        (index for index, crossing in enumerate(self.pd_code) if crossing.count(edge) == 2),
        None,
    )
    if crossing_index is None:
        raise ReidemeisterError("given edge is not on a twist, so it cannot be untwisted.")
    crossing = self.pd_code[crossing_index]
    other_edges = [crossing_edge for crossing_edge in crossing if crossing_edge != edge]
    if len(other_edges) != 2:
        raise ReidemeisterError("given crossing is not a valid twist.")
    merged_edges: dict[Edge, Edge] = {}
    removed_edges: set[Edge] = {edge}
    if other_edges[0] == other_edges[1]:
        removed_edges.add(other_edges[0])
    else:
        if not any(
            other_edges[0] in component and other_edges[1] in component
            for component in self.components
        ):
            raise ReidemeisterError("twist edges belong to different components.")
        merged_edges[max(other_edges)] = min(other_edges)

    pd_code = [
        row for index, row in enumerate(self.pd_code)
        if index != crossing_index
    ]
    pd_code = _relabel_after_contractions(
        pd_code,
        self.components,
        merged_edges,
        removed_edges,
    )
    return _preserve_component_count(pd_code, self.n_components)

def _prepare_poke(
    self: Diagram,
    lower_edge: Edge,
    higher_edge: Edge,
    retained_occurrences: dict[Edge, tuple[int, int]],
) -> PDNotation:
    """Readjust edge labels before a poke using the selected retained endpoints."""
    pd_code: PDNotation = []

    # Map over each edge in each crossing of `diagram`.
    for crossing_index, crossing in enumerate(self.pd_code):
        new_crossing_as_list: list[Edge] = []
        for edge_index, edge in enumerate(crossing):
            # Keep the selected endpoint on each original edge and split its other endpoint.
            occurrence = (crossing_index, edge_index)
            if edge < lower_edge:
                new_crossing_as_list.append(edge)
            elif edge == lower_edge:
                new_crossing_as_list.append(
                    edge if occurrence == retained_occurrences[lower_edge] else edge + 2
                )
            elif edge < higher_edge:
                new_crossing_as_list.append(edge + 2)
            elif edge == higher_edge:
                new_crossing_as_list.append(
                    edge + 2
                    if occurrence == retained_occurrences[higher_edge]
                    else edge + 4
                )
            else:
                new_crossing_as_list.append(edge + 4)
        new_crossing: Crossing = (
            new_crossing_as_list[0],
            new_crossing_as_list[1],
            new_crossing_as_list[2],
            new_crossing_as_list[3],
        )
        pd_code.append(new_crossing)

    return pd_code


def _append_poke_crossings(
    pd_code: PDNotation,
    lower_edge: Edge,
    higher_edge: Edge,
    under_edge: Edge,
    face_orientation: str,
) -> None:
    """Append the two crossings for a selected R2 face orientation."""
    if face_orientation == "negative_cw":
        if under_edge == lower_edge:
            pd_code.extend([
                (lower_edge, higher_edge + 2, lower_edge + 1, higher_edge + 3),
                (lower_edge + 1, higher_edge + 4, lower_edge + 2, higher_edge + 3),
            ])
        else:
            pd_code.extend([
                (higher_edge + 2, lower_edge + 1, higher_edge + 3, lower_edge),
                (higher_edge + 3, lower_edge + 1, higher_edge + 4, lower_edge + 2),
            ])
    elif face_orientation == "negative_ccw":
        if under_edge == lower_edge:
            pd_code.extend([
                (lower_edge, higher_edge + 3, lower_edge + 1, higher_edge + 2),
                (lower_edge + 1, higher_edge + 3, lower_edge + 2, higher_edge + 4),
            ])
        else:
            pd_code.extend([
                (higher_edge + 2, lower_edge, higher_edge + 3, lower_edge + 1),
                (higher_edge + 3, lower_edge + 2, higher_edge + 4, lower_edge + 1),
            ])
    elif face_orientation == "positive_cw":
        if under_edge == lower_edge:
            pd_code.extend([
                (lower_edge, higher_edge + 4, lower_edge + 1, higher_edge + 3),
                (lower_edge + 1, higher_edge + 2, lower_edge + 2, higher_edge + 3),
            ])
        else:
            pd_code.extend([
                (higher_edge + 2, lower_edge + 1, higher_edge + 3, lower_edge + 2),
                (higher_edge + 3, lower_edge + 1, higher_edge + 4, lower_edge),
            ])
    elif face_orientation == "positive_ccw":
        if under_edge == lower_edge:
            pd_code.extend([
                (lower_edge, higher_edge + 3, lower_edge + 1, higher_edge + 4),
                (lower_edge + 1, higher_edge + 3, lower_edge + 2, higher_edge + 2),
            ])
        else:
            pd_code.extend([
                (higher_edge + 2, lower_edge + 2, higher_edge + 3, lower_edge + 1),
                (higher_edge + 3, lower_edge, higher_edge + 4, lower_edge + 1),
            ])


def poke(self: Diagram, under_edge: Edge, over_edge: Edge) -> Diagram:
    """Poke `under_edge` underneath `over_edge`."""
    if under_edge == over_edge:
        raise ReidemeisterError("cannot poke an edge underneath itself.")

    # Handle infinity unknots as special cases.
    if self == Diagram([(1, 2, 2, 1)]):
        if under_edge == 1 and over_edge == 2:
            return Diagram([(1, 4, 2, 5), (2, 6, 3, 5), (3, 6, 4, 1)])
        else:
            return Diagram([(4, 2, 5, 1), (5, 2, 6, 3), (3, 6, 4, 1)])
    elif self == Diagram([(2, 2, 1, 1)]):
        if under_edge == 1 and over_edge == 2:
            return Diagram([(1, 4, 2, 5), (2, 6, 3, 5), (6, 4, 1, 3)])
        else:
            return Diagram([(4, 2, 5, 1), (5, 2, 6, 3), (6, 4, 1, 3)])
    
    lower_edge = min(under_edge, over_edge)
    higher_edge = max(under_edge, over_edge)

    face_ccw, face_cw = self._get_adjacent_faces(lower_edge)
    face_orientations = []
    if -higher_edge in face_cw:
        face_orientations.append("negative_cw")
    if -higher_edge in face_ccw:
        face_orientations.append("negative_ccw")
    if higher_edge in face_cw:
        face_orientations.append("positive_cw")
    if higher_edge in face_ccw:
        face_orientations.append("positive_ccw")

    projection_components = _projection_component_ids(self)
    if not face_orientations:
        if projection_components[under_edge] == projection_components[over_edge]:
            raise ReidemeisterError("can only poke edges along the same face.")
        face_orientations = [
            "negative_cw",
            "negative_ccw",
            "positive_cw",
            "positive_ccw",
        ]

    occurrences = {
        edge: [
            (crossing_index, edge_index)
            for crossing_index, crossing in enumerate(self.pd_code)
            for edge_index, crossing_edge in enumerate(crossing)
            if crossing_edge == edge
        ]
        for edge in (lower_edge, higher_edge)
    }
    if any(len(edge_occurrences) != 2 for edge_occurrences in occurrences.values()):
        raise ReidemeisterError("each poked edge must occur twice in the diagram.")

    for face_orientation in face_orientations:
        for lower_occurrence in occurrences[lower_edge]:
            for higher_occurrence in occurrences[higher_edge]:
                pd_code = _prepare_poke(
                    self,
                    lower_edge,
                    higher_edge,
                    {
                        lower_edge: lower_occurrence,
                        higher_edge: higher_occurrence,
                    },
                )
                _append_poke_crossings(
                    pd_code,
                    lower_edge,
                    higher_edge,
                    under_edge,
                    face_orientation,
                )
                candidate = Diagram(pd_code)
                if _has_oriented_edge_cycles(candidate):
                    return candidate

    raise ReidemeisterError("could not orient the resulting poke.")

def unpoke(self: Diagram, edge1: Edge, edge2: Edge) -> Diagram:
    """Remove the poke between the two given edges."""
    removed_crossings = [
        crossing
        for crossing in self.pd_code
        if edge1 in crossing and edge2 in crossing
    ]
    if len(removed_crossings) != 2:
        raise ReidemeisterError("given edge is not on a poke, so it cannot be unpoked.")
    removed_indices = {
        index
        for index, crossing in enumerate(self.pd_code)
        if edge1 in crossing and edge2 in crossing
    }
    pd_code = [
        crossing
        for index, crossing in enumerate(self.pd_code)
        if index not in removed_indices
    ]

    edge_counts: dict[Edge, int] = {
        edge: sum(crossing.count(edge) for crossing in pd_code)
        for component in self.components
        for edge in component
    }
    merged_edges: dict[Edge, Edge] = {}
    removed_edges: set[Edge] = set()
    for component in self.components:
        zero_indices = [
            index for index, edge in enumerate(component)
            if edge_counts[edge] == 0
        ]
        if len(zero_indices) == len(component):
            removed_edges.update(component)
            continue
        if not zero_indices:
            if all(edge_counts[edge] == 2 for edge in component):
                continue
            raise ReidemeisterError("could not reconnect unpoked link edges.")

        zero_set = set(zero_indices)
        zero_runs = [
            index
            for index in zero_indices
            if (index - 1) % len(component) not in zero_set
        ]
        for start in zero_runs:
            run = []
            index = start
            while edge_counts[component[index]] == 0:
                run.append(component[index])
                index = (index + 1) % len(component)
            previous_edge = component[(start - 1) % len(component)]
            next_edge = component[index]
            if edge_counts[previous_edge] != 1 or edge_counts[next_edge] != 1:
                raise ReidemeisterError("could not reconnect unpoked link edges.")
            if next_edge in merged_edges or previous_edge in merged_edges.values():
                raise ReidemeisterError("unpoke would merge an edge more than once.")
            merged_edges[next_edge] = previous_edge
            removed_edges.update(run)

    pd_code = _relabel_after_contractions(
        pd_code,
        self.components,
        merged_edges,
        removed_edges,
    )
    return _preserve_component_count(pd_code, self.n_components)

def slide(self: Diagram, edge1: Edge, edge2: Edge, edge3: Edge) -> Diagram:
    """Slide an edge over the face formed by the three given edges."""
    edges = [edge1, edge2, edge3]

    # Check if edges all lie on the same face
    face_ccw, face_cw = self._get_adjacent_faces(edge1)
    if not (all(edge in face_ccw or -edge in face_ccw for edge in edges) and len(face_ccw) == 3 or all(edge in face_cw or -edge in face_cw for edge in edges) and len(face_cw) == 3):
        raise ReidemeisterError("can only slide three edges along the same face.")
    
    # Check if edges are layered properly
    if not _is_slidable(self, edge1, edge2, edge3):
        raise ReidemeisterError("given edges do not follow the correct pattern for a slide.")

    # Initialize three crossings to be updated while iterating over the relevant crossings.
    pd_code = [[0, 0, 0, 0] for _ in range(len(self.pd_code))]

    # Map over each edge in each relevant crossing by index.
    # The crossing index is the index of a crossing in the PD notation as a list.
    for crossing_index in range(len(self.pd_code)):
        # The edge index is the index of an edge in a crossing.
        for edge_index in range(4):
            # Shift the relevant crossings down two. However, if the edge is one of the three edges forming the face of the slide, use the edge shifted down two from its friend instead.
            # See `_get_friend_index` for the definition of a friend.
            if any(edge in self.pd_code[crossing_index] for edge in edges) and self.pd_code[crossing_index][edge_index] in [edge1, edge2, edge3]:
                friend_crossing_index, friend_edge_index = self._get_friend_index(crossing_index, edge_index)
                pd_code[crossing_index][edge_index] = (
                    self.pd_code[friend_crossing_index][(friend_edge_index + 2) % 4]
                )
            elif any(edge in self.pd_code[crossing_index] for edge in edges):
                pd_code[crossing_index][edge_index] = self.pd_code[crossing_index][(edge_index + 2) % 4]
            else:
                pd_code[crossing_index][edge_index] = self.pd_code[crossing_index][edge_index]
    
    pd_code = [tuple(crossing) for crossing in pd_code]

    return Diagram(pd_code)


def get_moves(self: Diagram) -> list[Move]:
    """Return all legal Reidemeister moves in a deterministic order."""
    if not self.is_valid():
        raise ValueError("cannot get moves for an invalid diagram.")

    moves = [
        Move(kind, (edge,))
        for edge in get_twistables(self)
        for kind in (
            MoveKind.LEFT_POSITIVE_TWIST,
            MoveKind.LEFT_NEGATIVE_TWIST,
            MoveKind.RIGHT_POSITIVE_TWIST,
            MoveKind.RIGHT_NEGATIVE_TWIST,
        )
    ]
    moves.extend(Move(MoveKind.UNTWIST, (edge,)) for edge in get_untwistables(self))
    moves.extend(Move(MoveKind.POKE, edges) for edges in get_pokables(self))
    moves.extend(Move(MoveKind.UNPOKE, edges) for edges in get_unpokables(self))
    moves.extend(Move(MoveKind.SLIDE, edges) for edges in get_slidables(self))

    return list(dict.fromkeys(moves))


def apply_move(self: Diagram, move: Move) -> Diagram:
    """Apply a move to a diagram, raising an error if its arguments are invalid."""
    if not isinstance(move, Move):
        raise TypeError("move must be a Move.")
    if not self.is_valid():
        raise ValueError("cannot apply a move to an invalid diagram.")
    if any(edge > 2 * len(self.pd_code) for edge in move.edges):
        raise ValueError("move edges must belong to the diagram.")

    match move.kind:
        case MoveKind.LEFT_POSITIVE_TWIST:
            return left_positive_twist(self, *move.edges)
        case MoveKind.LEFT_NEGATIVE_TWIST:
            return left_negative_twist(self, *move.edges)
        case MoveKind.RIGHT_POSITIVE_TWIST:
            return right_positive_twist(self, *move.edges)
        case MoveKind.RIGHT_NEGATIVE_TWIST:
            return right_negative_twist(self, *move.edges)
        case MoveKind.UNTWIST:
            return untwist(self, *move.edges)
        case MoveKind.POKE:
            return poke(self, *move.edges)
        case MoveKind.UNPOKE:
            return unpoke(self, *move.edges)
        case MoveKind.SLIDE:
            return slide(self, *move.edges)
    raise ValueError(f"unsupported move kind: {move.kind!r}")


def transitions(self: Diagram) -> Iterator[tuple[Move, Diagram]]:
    """Yield each legal move with the diagram it produces."""
    for move in get_moves(self):
        yield move, apply_move(self, move)


def apply_random_move(
    self: Diagram, beta: float, rng: random.Random | None = None
) -> Diagram:
    """Apply one weighted random Reidemeister move."""
    choose = random.choices if rng is None else rng.choices
    numerical_weights: list[float] = [
        math.e**-beta,
        math.e**beta,
        math.e**(-2*beta),
        math.e**(2*beta),
        1
    ]

    twistables = get_twistables(self)
    untwistables = get_untwistables(self)
    pokables = get_pokables(self)
    unpokables = get_unpokables(self)
    slidables = get_slidables(self)

    options = [twistables, untwistables, pokables, unpokables, slidables]

    weights = [0 if len(l) == 0 else w for w, l in zip(numerical_weights, options)]

    move_decision = choose([1, 2, 3, 4, 5], weights=weights)[0]

    try:
        match move_decision:
            case 1:
                edge = choose(twistables)[0]
                twist_decision = choose([1, 2, 3, 4])[0]
                match twist_decision:
                    case 1:
                        return left_positive_twist(self, edge)
                    case 2:
                        return left_negative_twist(self, edge)
                    case 3:
                        return right_positive_twist(self, edge)
                    case 4:
                        return right_negative_twist(self, edge)
            case 2:
                edge = choose(untwistables)[0]
                return untwist(self, edge)
            case 3:
                edges = choose(pokables)[0]
                return poke(self, *edges)
            case 4:
                edges = choose(unpokables)[0]
                return unpoke(self, *edges)
            case 5:
                edges = choose(slidables)[0]
                return slide(self, *edges)
    except NotImplementedError:
        return apply_random_move(self, beta, rng)
    raise RuntimeError("no Reidemeister move could be applied.")

def randomeister(self: Diagram, moves: int, beta: float, show: bool = False) -> list[Diagram]:
    """Return the diagram sequence produced by repeated random moves."""
    diagrams: list[Diagram] = [self]
    diagram = self
    for _ in range(moves):
        diagram = apply_random_move(diagram, beta)
        diagrams.append(diagram)
        if show: print(len(diagram.pd_code))
    return diagrams

def unknot_solver(self: Diagram, beta: float):
    """Attempt to reduce an unknot diagram to at most two crossings."""
    diagram = self
    i = 0
    t0 = time.time()
    while len(diagram.pd_code) > 2:
        diagram = apply_random_move(diagram, beta)
        # print(len(diagram.pd_code), end=', ')
        assert diagram.is_valid()
        i += 1

        if i > 2000:
            print('Iterations exceeded 2000; given diagram is most likely not an unknot.')
            t1 = time.time()
            print('Time:', t1 - t0)
            return
    t1 = time.time()
    print('Iterations:', i)
    print('Time:', t1 - t0)
