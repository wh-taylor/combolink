from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
import math
import random
import time
from combolink.diagram import LinkDiagram, Edge, Crossing, PDNotation, ReidemeisterError
from combolink.properties import get_edges
from combolink.catalog import UNKNOT


class MoveKind(str, Enum):
    """Kinds of supported Reidemeister moves."""

    LEFT_POSITIVE_TWIST = "left_positive_twist"
    LEFT_NEGATIVE_TWIST = "left_negative_twist"
    RIGHT_POSITIVE_TWIST = "right_positive_twist"
    RIGHT_NEGATIVE_TWIST = "right_negative_twist"
    UNTWIST = "untwist"
    POKE = "poke"
    UNPOKE = "unpoke"
    SLIDE = "slide"

    def __str__(self) -> str:
        """Return the move kind in constructor-style display form.

        Returns
        -------
        str
            The title-cased move name.
        """
        return "".join(part.title() for part in self.name.split("_"))

    def __repr__(self) -> str:
        """Return the user-facing string representation of the move kind.

        Returns
        -------
        str
            The title-cased move name.
        """
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
    """A Reidemeister move and its ordered edge arguments.

    Parameters
    ----------
    kind : MoveKind
        Operation to perform.
    edges : tuple of Edge
        Ordered edge labels used as arguments to the move.

    Raises
    ------
    TypeError
        If ``kind`` is not a ``MoveKind``, ``edges`` is not a tuple, or an edge
        is not a positive integer.
    ValueError
        If the number of edges is wrong or a move requiring distinct edges
        receives duplicates.
    """

    kind: MoveKind
    edges: tuple[Edge, ...]

    def __post_init__(self) -> None:
        """Validate the move kind and its edge arguments.

        Raises
        ------
        TypeError
            If the kind or edge argument types are invalid.
        ValueError
            If the edge count is incorrect or required edges are not distinct.
        """
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
        """Return the constructor-style representation of the move.

        Returns
        -------
        str
            The move kind and ordered edge tuple.
        """
        return f"Move({self.kind}, {self.edges!r})"

    def __repr__(self) -> str:
        """Return the string representation of the move.

        Returns
        -------
        str
            The constructor-style move representation.
        """
        return str(self)


def _is_unpokable(self: LinkDiagram, edge1: Edge, edge2: Edge) -> bool:
    """Return whether the edges have the crossing pattern for an R2 removal."""
    return any((
        self._is_open(edge1) and self._is_closed(edge2),
        self._is_open(edge2) and self._is_closed(edge1),
    ))

def _is_slidable(self: LinkDiagram, edge1: Edge, edge2: Edge, edge3: Edge) -> bool:
    """Return whether the edges have the crossing pattern for an R3 move."""
    return any((
        self._is_open(edge1) and self._is_closed(edge2) and self._is_half_open(edge3),
        self._is_open(edge1) and self._is_closed(edge3) and self._is_half_open(edge2),
        self._is_open(edge2) and self._is_closed(edge1) and self._is_half_open(edge3),
        self._is_open(edge2) and self._is_closed(edge3) and self._is_half_open(edge1),
        self._is_open(edge3) and self._is_closed(edge1) and self._is_half_open(edge2),
        self._is_open(edge3) and self._is_closed(edge2) and self._is_half_open(edge1),
    ))


def _projection_component_ids(self: LinkDiagram) -> dict[Edge, int]:
    """Map each edge to its connected component in the crossing projection."""
    crossing_indices_by_edge: dict[Edge, set[int]] = {}
    for crossing_index, crossing in enumerate(self.crossings):
        for edge in crossing:
            crossing_indices_by_edge.setdefault(edge, set()).add(crossing_index)

    crossing_component_ids: dict[int, int] = {}
    component_id = 0
    for start in range(len(self.crossings)):
        if start in crossing_component_ids:
            continue
        crossing_component_ids[start] = component_id
        stack = [start]
        while stack:
            crossing_index = stack.pop()
            for edge in self.crossings[crossing_index]:
                for adjacent in crossing_indices_by_edge[edge]:
                    if adjacent not in crossing_component_ids:
                        crossing_component_ids[adjacent] = component_id
                        stack.append(adjacent)
        component_id += 1

    return {
        edge: crossing_component_ids[next(iter(indices))]
        for edge, indices in crossing_indices_by_edge.items()
    }

def _is_infinity_unknot(self: LinkDiagram) -> bool:
    return self == UNKNOT or self == ~UNKNOT


def get_twistables(self: LinkDiagram) -> list[Edge]:
    """Return edges on which a Reidemeister I twist can be applied.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose edges are enumerated.

    Returns
    -------
    list of Edge
        All edge labels in the diagram.
    """
    return get_edges(self)

def get_untwistables(self: LinkDiagram) -> list[Edge]:
    """Return edges adjacent to removable Reidemeister I twists.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to inspect.

    Returns
    -------
    list of Edge
        Edge labels that can be untwisted. One-crossing infinity-unknot
        encodings return an empty list.
    """
    if _is_infinity_unknot(self):
        return []

    untwistables = []
    for crossing in self.crossings:
        if len(set(crossing)) == 3:
            untwistables.append(max(set(crossing), key=crossing.count))
        elif len(set(crossing)) == 2 and all(
            crossing.count(edge) == 2 for edge in set(crossing)
        ):
            untwistables.extend(dict.fromkeys(crossing))
    return untwistables

def get_pokables(self: LinkDiagram) -> list[tuple[Edge, Edge]]:
    """Return ordered edge pairs for Reidemeister II insertions.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to inspect.

    Returns
    -------
    list of tuple of Edge
        Ordered ``(under_edge, over_edge)`` pairs that can be poked.
    """
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

def get_unpokables(self: LinkDiagram) -> list[tuple[Edge, Edge]]:
    """Return edge pairs at removable Reidemeister II crossings.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to inspect.

    Returns
    -------
    list of tuple of Edge
        Sorted pairs of edge labels that can be unpoked.
    """
    unpokables = []
    for edge in get_edges(self):
        if any(edge in pair for pair in unpokables):
            continue
        face_ccw, face_cw = self._get_adjacent_faces(edge)
        if len(face_ccw) == 2 and _is_unpokable(self, *[abs(n) for n in face_ccw]):
            candidate = tuple(sorted(abs(n) for n in face_ccw))
            if (
                sum(all(part in crossing for part in candidate) for crossing in self.crossings) == 2
                and candidate not in unpokables
            ):
                unpokables.append(candidate)
        if len(face_cw) == 2 and _is_unpokable(self, *[abs(n) for n in face_cw]):
            candidate = tuple(sorted(abs(n) for n in face_cw))
            if (
                sum(all(part in crossing for part in candidate) for crossing in self.crossings) == 2
                and candidate not in unpokables
            ):
                unpokables.append(candidate)
    return unpokables

def get_slidables(self: LinkDiagram) -> list[tuple[Edge, Edge, Edge]]:
    """Return edge triples that support a Reidemeister III slide.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to inspect.

    Returns
    -------
    list of tuple of Edge
        Sorted triples of edge labels that can be slid.
    """
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

def _has_oriented_edge_cycles(self: LinkDiagram) -> bool:
    """Return whether every edge has an oriented crossing it faces toward."""
    if not self.is_valid():
        return False
    try:
        for edge in range(1, 2 * len(self.crossings) + 1):
            self._get_forth_index(edge)
    except NotImplementedError:
        return False
    return True


def _preserve_component_count(crossings: PDNotation, component_count: int) -> LinkDiagram:
    """Restore missing components with single-crossing unknot diagrams."""
    current_count = 0
    if crossings:
        candidate = LinkDiagram(crossings)
        if not candidate.is_valid():
            raise ReidemeisterError("move produced an invalid PD code.")
        current_count = candidate.n_components
    if current_count > component_count:
        raise ReidemeisterError("move changed the number of link components.")
    while current_count < component_count:
        first_edge = 2 * len(crossings) + 1
        crossings.append(
            (first_edge, first_edge + 1, first_edge + 1, first_edge)
        )
        current_count += 1
    return LinkDiagram(crossings)


def _relabel_after_contractions(
    crossings: PDNotation,
    components: tuple[tuple[Edge, ...], ...],
    merged_edges: dict[Edge, Edge],
    removed_edges: set[Edge],
) -> PDNotation:
    """Relabel edges after removing crossings and merging adjacent edges."""
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
            for a, b, c, d in crossings
        ]
    except KeyError as error:
        raise ReidemeisterError("removed crossing left an unmatched PD edge.") from error


def _prepare_twist(
    self: LinkDiagram,
    target_edge: Edge,
    retained_occurrence: tuple[int, int],
) -> PDNotation:
    """Readjust the edge values of `diagram` with the expectation of a twist at `target_edge`."""
    crossings: PDNotation = []
    target_occurrences = [
        (crossing_index, edge_index)
        for crossing_index, crossing in enumerate(self.crossings)
        for edge_index, edge in enumerate(crossing)
        if edge == target_edge
    ]
    if len(target_occurrences) != 2:
        raise ReidemeisterError("given edge does not occur twice in the diagram.")

    # Map over each edge in each crossing of `diagram`.
    for crossing_index, crossing in enumerate(self.crossings):
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
        crossings.append(new_crossing)
    
    return crossings


def _twist(self: LinkDiagram, edge: Edge, crossing: Crossing) -> LinkDiagram:
    """Apply a specified crossing pattern as a Reidemeister I move."""
    occurrences = [
        (crossing_index, edge_index)
        for crossing_index, row in enumerate(self.crossings)
        for edge_index, crossing_edge in enumerate(row)
        if crossing_edge == edge
    ]
    fallback = None
    for retained_occurrence in occurrences:
        crossings = _prepare_twist(self, edge, retained_occurrence)
        candidate = LinkDiagram(crossings + [crossing])
        if fallback is None and candidate.is_valid():
            fallback = candidate
        if _has_oriented_edge_cycles(candidate):
            return candidate
    if self.n_components == 1 and fallback is not None:
        return fallback
    raise ReidemeisterError("could not orient the resulting twist.")

def left_positive_twist(self: LinkDiagram, edge: Edge) -> LinkDiagram:
    """Apply a positive left-handed Reidemeister I twist.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    edge : Edge
        Edge along which to insert the twist.

    Returns
    -------
    LinkDiagram
        The diagram with the twist inserted.

    Raises
    ------
    ReidemeisterError
        If the resulting crossing pattern cannot be oriented.
    """
    if _is_infinity_unknot(self):
        if edge == 1:
            return LinkDiagram([(1, 2, 2, 3), (3, 1, 4, 4)])
        if edge == 2:
            return LinkDiagram([(1, 4, 2, 1), (3, 2, 4, 3)])
    if edge == 1 or edge == 2*len(self.crossings):
        return left_positive_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge, edge + 2, edge + 1, edge + 1))

def left_negative_twist(self: LinkDiagram, edge: Edge) -> LinkDiagram:
    """Apply a negative left-handed Reidemeister I twist.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    edge : Edge
        Edge along which to insert the twist.

    Returns
    -------
    LinkDiagram
        The diagram with the twist inserted.

    Raises
    ------
    ReidemeisterError
        If the resulting crossing pattern cannot be oriented.
    """
    if _is_infinity_unknot(self):
        if edge == 1:
            return LinkDiagram([(1, 2, 2, 3), (4, 3, 1, 4)])
        if edge == 2:
            return LinkDiagram([(1, 4, 2, 1), (2, 4, 3, 3)])
    if edge == 1 or edge == 2*len(self.crossings):
        return left_negative_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge + 1, edge, edge + 2, edge + 1))

def right_positive_twist(self: LinkDiagram, edge: Edge) -> LinkDiagram:
    """Apply a positive right-handed Reidemeister I twist.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    edge : Edge
        Edge along which to insert the twist.

    Returns
    -------
    LinkDiagram
        The diagram with the twist inserted.

    Raises
    ------
    ReidemeisterError
        If the resulting crossing pattern cannot be oriented.
    """
    if _is_infinity_unknot(self):
        if edge == 1:
            return LinkDiagram([(1, 2, 2, 3), (3, 4, 4, 1)])
        if edge == 2:
            return LinkDiagram([(1, 4, 2, 1), (3, 3, 4, 2)])
    if edge == 1 or edge == 2*len(self.crossings):
        return right_positive_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge + 1, edge + 1, edge + 2, edge))

def right_negative_twist(self: LinkDiagram, edge: Edge) -> LinkDiagram:
    """Apply a negative right-handed Reidemeister I twist.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    edge : Edge
        Edge along which to insert the twist.

    Returns
    -------
    LinkDiagram
        The diagram with the twist inserted.

    Raises
    ------
    ReidemeisterError
        If the resulting crossing pattern cannot be oriented.
    """
    if _is_infinity_unknot(self):
        if edge == 1:
            return LinkDiagram([(1, 2, 2, 3), (4, 4, 1, 3)])
        if edge == 2:
            return LinkDiagram([(1, 4, 2, 1), (2, 3, 3, 4)])
    if edge == 1 or edge == 2*len(self.crossings):
        return right_negative_twist(self.shift(1), self._next(edge))
    return _twist(self, edge, (edge, edge + 1, edge + 1, edge + 2))

def untwist(self: LinkDiagram, edge: Edge) -> LinkDiagram:
    """Remove the Reidemeister I twist adjacent to an edge.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to simplify.
    edge : Edge
        Edge appearing twice at the twist crossing.

    Returns
    -------
    LinkDiagram
        LinkDiagram with the twist removed.

    Raises
    ------
    ReidemeisterError
        If the edge is not on a valid twist or its edges cannot be reconnected.
    """
    crossing_index = next(
        (index for index, crossing in enumerate(self.crossings) if crossing.count(edge) == 2),
        None,
    )
    if crossing_index is None:
        raise ReidemeisterError("given edge is not on a twist, so it cannot be untwisted.")
    crossing = self.crossings[crossing_index]
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
            for component in self.components_edges
        ):
            raise ReidemeisterError("twist edges belong to different components.")
        merged_edges[max(other_edges)] = min(other_edges)

    crossings = [
        row for index, row in enumerate(self.crossings)
        if index != crossing_index
    ]
    crossings = _relabel_after_contractions(
        crossings,
        self.components_edges,
        merged_edges,
        removed_edges,
    )
    return _preserve_component_count(crossings, self.n_components)

def _prepare_poke(
    self: LinkDiagram,
    lower_edge: Edge,
    higher_edge: Edge,
    retained_occurrences: dict[Edge, tuple[int, int]],
) -> PDNotation:
    """Readjust edge labels before a poke using the selected retained endpoints."""
    crossings: PDNotation = []

    # Map over each edge in each crossing of `diagram`.
    for crossing_index, crossing in enumerate(self.crossings):
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
        crossings.append(new_crossing)

    return crossings


def _append_poke_crossings(
    crossings: PDNotation,
    lower_edge: Edge,
    higher_edge: Edge,
    under_edge: Edge,
    face_orientation: str,
) -> None:
    """Append the two crossings for a selected R2 face orientation."""
    if face_orientation == "negative_cw":
        if under_edge == lower_edge:
            crossings.extend([
                (lower_edge, higher_edge + 2, lower_edge + 1, higher_edge + 3),
                (lower_edge + 1, higher_edge + 4, lower_edge + 2, higher_edge + 3),
            ])
        else:
            crossings.extend([
                (higher_edge + 2, lower_edge + 1, higher_edge + 3, lower_edge),
                (higher_edge + 3, lower_edge + 1, higher_edge + 4, lower_edge + 2),
            ])
    elif face_orientation == "negative_ccw":
        if under_edge == lower_edge:
            crossings.extend([
                (lower_edge, higher_edge + 3, lower_edge + 1, higher_edge + 2),
                (lower_edge + 1, higher_edge + 3, lower_edge + 2, higher_edge + 4),
            ])
        else:
            crossings.extend([
                (higher_edge + 2, lower_edge, higher_edge + 3, lower_edge + 1),
                (higher_edge + 3, lower_edge + 2, higher_edge + 4, lower_edge + 1),
            ])
    elif face_orientation == "positive_cw":
        if under_edge == lower_edge:
            crossings.extend([
                (lower_edge, higher_edge + 4, lower_edge + 1, higher_edge + 3),
                (lower_edge + 1, higher_edge + 2, lower_edge + 2, higher_edge + 3),
            ])
        else:
            crossings.extend([
                (higher_edge + 2, lower_edge + 1, higher_edge + 3, lower_edge + 2),
                (higher_edge + 3, lower_edge + 1, higher_edge + 4, lower_edge),
            ])
    elif face_orientation == "positive_ccw":
        if under_edge == lower_edge:
            crossings.extend([
                (lower_edge, higher_edge + 3, lower_edge + 1, higher_edge + 4),
                (lower_edge + 1, higher_edge + 3, lower_edge + 2, higher_edge + 2),
            ])
        else:
            crossings.extend([
                (higher_edge + 2, lower_edge + 2, higher_edge + 3, lower_edge + 1),
                (higher_edge + 3, lower_edge, higher_edge + 4, lower_edge + 1),
            ])


def poke(self: LinkDiagram, under_edge: Edge, over_edge: Edge) -> LinkDiagram:
    """Insert a Reidemeister II pair by passing one edge under another.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    under_edge : Edge
        Edge that passes underneath the new crossings.
    over_edge : Edge
        Edge that passes over the new crossings.

    Returns
    -------
    LinkDiagram
        LinkDiagram with two crossings inserted.

    Raises
    ------
    ReidemeisterError
        If the same edge is selected twice, the edges cannot be poked, or the
        resulting crossing pattern cannot be oriented.
    """
    if under_edge == over_edge:
        raise ReidemeisterError("cannot poke an edge underneath itself.")

    # Handle infinity unknots as special cases.
    if self == LinkDiagram([(1, 2, 2, 1)]):
        if under_edge == 1 and over_edge == 2:
            return LinkDiagram([(1, 4, 2, 5), (2, 6, 3, 5), (3, 6, 4, 1)])
        else:
            return LinkDiagram([(4, 2, 5, 1), (5, 2, 6, 3), (3, 6, 4, 1)])
    elif self == LinkDiagram([(2, 2, 1, 1)]):
        if under_edge == 1 and over_edge == 2:
            return LinkDiagram([(1, 4, 2, 5), (2, 6, 3, 5), (6, 4, 1, 3)])
        else:
            return LinkDiagram([(4, 2, 5, 1), (5, 2, 6, 3), (6, 4, 1, 3)])
    
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
            for crossing_index, crossing in enumerate(self.crossings)
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
                crossings = _prepare_poke(
                    self,
                    lower_edge,
                    higher_edge,
                    {
                        lower_edge: lower_occurrence,
                        higher_edge: higher_occurrence,
                    },
                )
                _append_poke_crossings(
                    crossings,
                    lower_edge,
                    higher_edge,
                    under_edge,
                    face_orientation,
                )
                candidate = LinkDiagram(crossings)
                if _has_oriented_edge_cycles(candidate):
                    return candidate

    raise ReidemeisterError("could not orient the resulting poke.")

def unpoke(self: LinkDiagram, edge1: Edge, edge2: Edge) -> LinkDiagram:
    """Remove a Reidemeister II pair between two edges.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to simplify.
    edge1, edge2 : Edge
        Edge labels identifying the two crossings to remove.

    Returns
    -------
    LinkDiagram
        LinkDiagram with the poke removed.

    Raises
    ------
    ReidemeisterError
        If the edges do not identify exactly two crossings or the remaining
        edges cannot be reconnected.
    """
    removed_crossings = [
        crossing
        for crossing in self.crossings
        if edge1 in crossing and edge2 in crossing
    ]
    if len(removed_crossings) != 2:
        raise ReidemeisterError("given edge is not on a poke, so it cannot be unpoked.")
    removed_indices = {
        index
        for index, crossing in enumerate(self.crossings)
        if edge1 in crossing and edge2 in crossing
    }
    crossings = [
        crossing
        for index, crossing in enumerate(self.crossings)
        if index not in removed_indices
    ]

    edge_counts: dict[Edge, int] = {
        edge: sum(crossing.count(edge) for crossing in crossings)
        for component in self.components_edges
        for edge in component
    }
    merged_edges: dict[Edge, Edge] = {}
    removed_edges: set[Edge] = set()
    for component in self.components_edges:
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

    crossings = _relabel_after_contractions(
        crossings,
        self.components_edges,
        merged_edges,
        removed_edges,
    )
    return _preserve_component_count(crossings, self.n_components)

def slide(self: LinkDiagram, edge1: Edge, edge2: Edge, edge3: Edge) -> LinkDiagram:
    """Apply a Reidemeister III move across a triangular face.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    edge1, edge2, edge3 : Edge
        Ordered edge labels forming the face and satisfying the required
        over-under pattern.

    Returns
    -------
    LinkDiagram
        LinkDiagram after the slide.

    Raises
    ------
    ReidemeisterError
        If the edges do not form a suitable triangular face or have the wrong
        crossing pattern.
    """
    edges = [edge1, edge2, edge3]

    # Check if edges all lie on the same face
    face_ccw, face_cw = self._get_adjacent_faces(edge1)
    if not (all(edge in face_ccw or -edge in face_ccw for edge in edges) and len(face_ccw) == 3 or all(edge in face_cw or -edge in face_cw for edge in edges) and len(face_cw) == 3):
        raise ReidemeisterError("can only slide three edges along the same face.")
    
    # Check if edges are layered properly
    if not _is_slidable(self, edge1, edge2, edge3):
        raise ReidemeisterError("given edges do not follow the correct pattern for a slide.")

    # Initialize three crossings to be updated while iterating over the relevant crossings.
    crossings = [[0, 0, 0, 0] for _ in range(len(self.crossings))]

    # Map over each edge in each relevant crossing by index.
    # The crossing index is the index of a crossing in the PD notation as a list.
    for crossing_index in range(len(self.crossings)):
        # The edge index is the index of an edge in a crossing.
        for edge_index in range(4):
            # Shift the relevant crossings down two. However, if the edge is one of the three edges forming the face of the slide, use the edge shifted down two from its friend instead.
            # See `_get_friend_index` for the definition of a friend.
            if any(edge in self.crossings[crossing_index] for edge in edges) and self.crossings[crossing_index][edge_index] in [edge1, edge2, edge3]:
                friend_crossing_index, friend_edge_index = self._get_friend_index(crossing_index, edge_index)
                crossings[crossing_index][edge_index] = (
                    self.crossings[friend_crossing_index][(friend_edge_index + 2) % 4]
                )
            elif any(edge in self.crossings[crossing_index] for edge in edges):
                crossings[crossing_index][edge_index] = self.crossings[crossing_index][(edge_index + 2) % 4]
            else:
                crossings[crossing_index][edge_index] = self.crossings[crossing_index][edge_index]
    
    crossings = [tuple(crossing) for crossing in crossings]

    return LinkDiagram(crossings)


def get_moves(self: LinkDiagram) -> list[Move]:
    """Enumerate legal Reidemeister moves in a deterministic order.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to inspect.

    Returns
    -------
    list of Move
        Legal twists, untwists, pokes, unpokes, and slides.

    Raises
    ------
    ValueError
        If the diagram is invalid.
    """
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


def apply_move(self: LinkDiagram, move: Move) -> LinkDiagram:
    """Apply a specified Reidemeister move.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    move : Move
        Move kind and ordered edge arguments.

    Returns
    -------
    LinkDiagram
        The diagram after applying the move.

    Raises
    ------
    TypeError
        If ``move`` is not a ``Move`` instance.
    ValueError
        If the diagram is invalid or a move edge is outside it.
    ReidemeisterError
        If the requested move is not legal for the selected edges.
    """
    if not isinstance(move, Move):
        raise TypeError("move must be a Move.")
    if not self.is_valid():
        raise ValueError("cannot apply a move to an invalid diagram.")
    if any(edge > 2 * len(self.crossings) for edge in move.edges):
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


def transitions(self: LinkDiagram) -> Iterator[tuple[Move, LinkDiagram]]:
    """Iterate over legal moves and their resulting diagrams.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose transitions are generated.

    Yields
    ------
    tuple of Move and LinkDiagram
        Each legal move paired with the diagram produced by that move.

    Raises
    ------
    ValueError
        If the input diagram is invalid.
    """
    for move in get_moves(self):
        yield move, apply_move(self, move)


def apply_random_move(
    self: LinkDiagram, beta: float, rng: random.Random | None = None
) -> LinkDiagram:
    """Apply one randomly selected Reidemeister move.

    The move categories are weighted by ``exp(-beta)``, ``exp(beta)``,
    ``exp(-2 * beta)``, ``exp(2 * beta)``, and ``1`` for twists, untwists,
    pokes, unpokes, and slides, respectively.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to modify.
    beta : float
        Parameter controlling the relative weights of move categories.
    rng : random.Random, optional
        Random-number generator to use. The module-level generator is used by
        default.

    Returns
    -------
    LinkDiagram
        The diagram after one move.
    """
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

def randomeister(self: LinkDiagram, moves: int, beta: float, show: bool = False) -> list[LinkDiagram]:
    """Generate a sequence of diagrams by repeatedly applying random moves.

    Parameters
    ----------
    self : LinkDiagram
        Initial diagram.
    moves : int
        Number of moves to apply.
    beta : float
        Parameter passed to :func:`apply_random_move`.
    show : bool, default=False
        If True, print the crossing count after each move.

    Returns
    -------
    list of LinkDiagram
        The initial diagram followed by each successive diagram.
    """
    diagrams: list[LinkDiagram] = [self]
    diagram = self
    for _ in range(moves):
        diagram = apply_random_move(diagram, beta)
        diagrams.append(diagram)
        if show: print(len(diagram.crossings))
    return diagrams

def unknot_solver(self: LinkDiagram, beta: float):
    """Try random Reidemeister moves until at most two crossings remain.

    This heuristic does not prove that the input is an unknot. It stops after
    2,000 moves if the diagram has not reached the crossing-count target.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to simplify.
    beta : float
        Parameter passed to :func:`apply_random_move`.

    Returns
    -------
    None
        Progress and termination information are printed.
    """
    diagram = self
    i = 0
    t0 = time.time()
    while len(diagram.crossings) > 2:
        diagram = apply_random_move(diagram, beta)
        # print(len(diagram.crossings), end=', ')
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
