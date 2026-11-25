from __future__ import annotations
from types import NotImplementedType
from combolink.polynomial import *

Edge = int
SignedEdge = int
Crossing = tuple[Edge, Edge, Edge, Edge]
PDNotation = list[Crossing]

class ReidemeisterError(Exception):
    """Raised when a requested Reidemeister move cannot be performed."""

    pass

class LinkDiagram:
    """A link diagram represented by planar-diagram (PD) crossings.

    Each crossing is a four-edge tuple. Edge labels identify edges between
    crossings, and a diagram's structure can be checked with :meth:`is_valid`.
    """

    def __init__(self, pd_code):
        """Create a diagram from a PD code without validating it.

        Parameters
        ----------
        pd_code : PDNotation
            Crossing tuples describing the diagram.
        """
        self.pd_code: PDNotation = pd_code
    
    def __repr__(self) -> str:
        """Return a constructor-like representation of the diagram.

        Returns
        -------
        str
            The diagram represented as ``LinkDiagram(pd_code)``.
        """
        return f'LinkDiagram({repr(self.pd_code)})'
    
    def __eq__(self, other: object) -> bool | NotImplementedType:
        """Compare oriented link diagrams.

        Parameters
        ----------
        other : object
            Value to compare with this diagram.

        Returns
        -------
        bool or NotImplementedType
            Whether the valid diagrams have the same oriented PD crossings,
            allowing cyclic shifts of edge labels. Returns ``NotImplemented``
            for values that are not diagrams.
        """
        if not isinstance(other, LinkDiagram):
            return NotImplemented
        if not self.is_valid() or not other.is_valid():
            return False
        if self.pd_code == other.pd_code:
            return True
        for n in range(2*len(self.pd_code)):
            if self.shift(n).identical(other):
                return True
        return False
    
    def _shiftmod(self, edge: Edge, n: int) -> Edge:
        """Shift an edge within its oriented component cycle."""
        for component in self.components:
            if edge in component:
                index = component.index(edge)
                return component[(index + n) % len(component)]
        raise ValueError(f"edge {edge} does not belong to this diagram.")

    def shift(self, n: int) -> LinkDiagram:
        """Cyclically shift edge labels within their oriented components.

        Parameters
        ----------
        n : int
            Number of positions by which to shift each component's edge labels.
            Negative values shift in the opposite direction.

        Returns
        -------
        LinkDiagram
            A new diagram with the shifted edge labels.

        Raises
        ------
        ValueError
            If this diagram is invalid.
        """
        return LinkDiagram(
            [
                tuple(self._shiftmod(edge, n) for edge in crossing)
                for crossing in self.pd_code
            ]
        )

    def identical(self, other: LinkDiagram) -> bool:
        """Compare link diagrams including edge labeling (stronger than
        diagram equivalence).

        Parameters
        ----------
        other : LinkDiagram
            LinkDiagram to compare with this one.

        Returns
        -------
        bool
            Whether both valid diagrams have the same crossings, independent
            of crossing-list order and with edge labels unchanged.
        """
        if not self.is_valid() or not other.is_valid(): return False
        if len(self.pd_code) != len(other.pd_code): return False
        return {tuple(crossing) for crossing in self.pd_code} == {
            tuple(crossing) for crossing in other.pd_code
        }

    def _calculate_components(self) -> tuple[tuple[Edge, ...], ...] | None:
        """Infer components from the opposite-edge connections in the PD code.

        Returns
        -------
        tuple of tuple of Edge or None
            Sorted edge labels grouped by component, or ``None`` if the PD code
            is structurally invalid.
        """
        if not self.pd_code:
            return None

        edge_count = 2 * len(self.pd_code)
        edge_counts = [0] * edge_count
        adjacent_edges = [set() for _ in range(edge_count)]

        for crossing in self.pd_code:
            if not isinstance(crossing, (tuple, list)) or len(crossing) != 4:
                return None
            for edge in crossing:
                if type(edge) is not int or not 1 <= edge <= edge_count:
                    return None
                edge_counts[edge - 1] += 1
            for first, second in ((crossing[0], crossing[2]), (crossing[1], crossing[3])):
                adjacent_edges[first - 1].add(second)
                adjacent_edges[second - 1].add(first)

        if any(count != 2 for count in edge_counts):
            return None

        remaining = set(range(1, edge_count + 1))
        components = []
        while remaining:
            component = []
            stack = [min(remaining)]
            while stack:
                edge = stack.pop()
                if edge not in remaining:
                    continue
                remaining.remove(edge)
                component.append(edge)
                stack.extend(adjacent_edges[edge - 1] & remaining)
            components.append(tuple(sorted(component)))

        result = tuple(sorted(components))
        for component in result:
            if component != tuple(range(component[0], component[-1] + 1)):
                return None
            for index, edge in enumerate(component):
                next_edge = component[(index + 1) % len(component)]
                if next_edge not in adjacent_edges[edge - 1]:
                    return None
        return result

    @property
    def components(self) -> tuple[tuple[Edge, ...], ...]:
        """Return edge labels grouped by link component.

        Returns
        -------
        tuple of tuple of Edge
            Each inner tuple contains the labels in one component.

        Raises
        ------
        ValueError
            If the diagram is invalid.
        """
        components = self._calculate_components()
        if components is None:
            raise ValueError("cannot determine components of an invalid diagram.")
        return components

    @property
    def n_components(self) -> int:
        """Return the number of link components.

        Returns
        -------
        int
            Number of components in the diagram.

        Raises
        ------
        ValueError
            If the diagram is invalid.
        """
        return len(self.components)

    @property
    def n_crossings(self) -> int:
        """Return the number of crossings.
        
        Returns
        -------
        int
            Number of crossings in the diagram.

        Raises
        ------
        ValueError
            If the diagram is invalid.
        """
        return len(self.pd_code)

    def is_valid(self) -> bool:
        """Check the structural validity of the PD code.

        Returns
        -------
        bool
            Whether every edge occurs twice and the opposite-edge connections
            form contiguous link components.
        """
        return self._calculate_components() is not None

    def _get_crossings_with_edge(self, edge: Edge) -> list[Crossing]:
        """Get a list of all crossings that are adjacent to a given edge."""
        return [crossing for crossing in self.pd_code if edge in crossing]

    def _next(self, edge: Edge) -> Edge:
        """Get the edge after a given edge (+1 with wraparound)."""
        return self._shiftmod(edge, 1)

    def _prev(self, edge: Edge) -> Edge:
        """Get the edge before a given edge (-1 with wraparound)."""
        return self._shiftmod(edge, -1)

    def _get_friend_index(self, crossing_index: int, edge_index: int) -> tuple[int, int]:
        """Given the index of an edge, get the index of its friend.

        Say we have two crossings: (_, _, _, 2), (_, _, 2, _).
        The first 2 is in the first crossing in the fourth position, so it has the index (1, 4).
        The second 2 is in the second crossing in the third position, so it has the index (2, 3).
        Thus, diagram._get_friend_index(1, 4) = (2, 3) and diagram._get_friend_index(2, 3) = (1, 4).
        """
        edge = self.pd_code[crossing_index][edge_index]
        crossings_with_edge = self._get_crossings_with_edge(edge)
        
        if len(crossings_with_edge) == 1:
            pos = [i for i, row in enumerate(self.pd_code[crossing_index]) if row == edge]
            return (crossing_index, pos[1] if pos[0] == edge_index else pos[0])
        
        if crossings_with_edge[0] == self.pd_code[crossing_index]:
            return (next(i for i, row in enumerate(self.pd_code) if row == crossings_with_edge[1]), next(i for i, x in enumerate(crossings_with_edge[1]) if x == edge))

        return (next(i for i, row in enumerate(self.pd_code) if row == crossings_with_edge[0]), next(i for i, x in enumerate(crossings_with_edge[0]) if x == edge))

    def _shift_unbounded(self, n: int) -> LinkDiagram:
        """Return a diagram with all of its edge values shifted up by `n` without wrapping around.

        This method is meant for adjusting a diagram to be combined with another.
        """
        return LinkDiagram([tuple(edge + n for edge in crossing) for crossing in self.pd_code])

    def _index_is_facing(self, crossing_index: int, edge_index: int) -> bool:
        """Returns whether or not the given index represents an edge that is facing its crossing."""
        if edge_index == 0: return True
        if edge_index == 1:
            return self.pd_code[crossing_index][3] == self._next(self.pd_code[crossing_index][1])
        if edge_index == 3:
            return self.pd_code[crossing_index][1] == self._next(self.pd_code[crossing_index][3])
        return False

    def _get_forth_index(self, edge: Edge) -> tuple[int, int]:
        """Get the index of the given edge in the crossing it faces toward.

        Note: the edge index is never 2, since the edge would then be
        facing away from the crossing.
        """
        for crossing_index, crossing in enumerate(self.pd_code):
            if crossing[0] == edge:
                return crossing_index, 0
            if crossing[1] == edge and crossing[3] == self._next(edge):
                return crossing_index, 1
            if crossing[3] == edge and crossing[1] == self._next(edge):
                return crossing_index, 3
        raise NotImplementedError

    def _get_adjacent_faces(self, edge: Edge) -> tuple[list[SignedEdge], list[SignedEdge]]:
        """Get the two faces adjacent to the given edge.
        
        Following the direction the given edge is pointing, two faces can be extracted.
        One by only going counterclockwise and one by only going clockwise.
        Each face is given as a list of edges that are signed. Since we generate faces
        based on a specific direction, the edge is negative if it goes against the direction
        of the path we follow in generating the face.
        """
        face_ccw: list[SignedEdge] = [edge]
        face_cw: list[SignedEdge] = [edge]

        # Generate the counterclockwise face.
        crossing_index, edge_index = self._get_forth_index(edge)
        edge_index = (edge_index - 1) % 4
        while self.pd_code[crossing_index][edge_index] != edge:
            sign = -1 if self._index_is_facing(crossing_index, edge_index) else 1
            face_ccw.append(sign * self.pd_code[crossing_index][edge_index])
            crossing_index, edge_index = self._get_friend_index(crossing_index, edge_index)
            edge_index = (edge_index - 1) % 4
        
        # Generate the clockwise face.
        crossing_index, edge_index = self._get_forth_index(edge)
        edge_index = (edge_index + 1) % 4
        while self.pd_code[crossing_index][edge_index] != edge:
            sign = -1 if self._index_is_facing(crossing_index, edge_index) else 1
            face_cw.append(sign * self.pd_code[crossing_index][edge_index])
            crossing_index, edge_index = self._get_friend_index(crossing_index, edge_index)
            edge_index = (edge_index + 1) % 4

        return (face_ccw, face_cw)

    def _is_closed(self, edge: Edge) -> bool:
        """Check if an edge on a diagram is closed.
        
        An edge is closed if, on both of the crossings it connects to, it crosses underneath.
        """
        adj_crossings = [crossing for crossing in self.pd_code if edge in crossing]
        return all(edge in [crossing[0], crossing[2]] for crossing in adj_crossings)

    def _is_open(self, edge: Edge) -> bool:
        """Check if an edge on a diagram is open.
        
        An edge is open if, on both of the crossings it connects to, it crosses over.
        """
        adj_crossings = [crossing for crossing in self.pd_code if edge in crossing]
        return all(edge in [crossing[1], crossing[3]] for crossing in adj_crossings)

    def _is_half_open(self, edge: Edge) -> bool:
        """Check if an edge on a diagram is half-open.
        
        An edge is half-open if it crosses over one of its crossings and under the other.
        """
        return not self._is_open(edge) and not self._is_closed(edge)

    def _mathematica_format(self) -> str:
        """Format the PD code using Mathematica's ``PD[X[...], ...]`` syntax.

        Returns
        -------
        str
            The diagram in Mathematica planar-diagram notation.
        """
        return 'PD[' + ','.join(['X[' + ','.join([str(edge) for edge in crossing]) + ']' for crossing in self.pd_code]) + ']'
