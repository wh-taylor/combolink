from __future__ import annotations
from types import NotImplementedType
from typing import Concatenate, cast
from collections.abc import Callable, Iterator
from collections import defaultdict
from itertools import permutations, product, combinations

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
        self._pd_code: PDNotation = pd_code
    
    def __repr__(self) -> str:
        """Return a constructor-like representation of the diagram.

        Returns
        -------
        str
            The diagram represented as ``LinkDiagram(pd_code)``.
        """
        return f'LinkDiagram({repr(self._pd_code)})'

    def pipe[**P, R](self, f: Callable[Concatenate[LinkDiagram, P], R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Apply a function to the diagram.
        
        Parameters
        ----------
        f : Callable[Concatenate[LinkDiagram, P], R]
            Function to apply to diagram.
        *args : P.args
            Arguments for the function `f`.
        *kwargs : P.kwargs
            Keyword arguments for the function `f`.
        
        Returns
        -------
        R
            The return type of `f`.
        """
        return f(self, *args, **kwargs)

    # Bring identifiers in from other namespaces without breaking circular dependencies

    def _reflect(self) -> LinkDiagram:
        from combolink.transformations import reflect
        return cast(Callable[[LinkDiagram], LinkDiagram], reflect)(self)

    def _reverse(self) -> LinkDiagram:
            from combolink.transformations import reverse
            return cast(Callable[[LinkDiagram], LinkDiagram], reverse)(self)

    def _disjoint_union(self, other: LinkDiagram) -> LinkDiagram:
        from combolink.transformations import disjoint_union
        return cast(Callable[[LinkDiagram, LinkDiagram], LinkDiagram], disjoint_union)(self, other)

    def _connected_sum(self, other: LinkDiagram) -> LinkDiagram:
        from combolink.transformations import connected_sum
        return cast(Callable[[LinkDiagram, LinkDiagram], LinkDiagram], connected_sum)(self, other)

    @property
    def _UNKNOT(self) -> LinkDiagram:
        from combolink.catalog import UNKNOT
        return cast(LinkDiagram, UNKNOT)

    @property
    def _EMPTY_LINK(self) -> LinkDiagram:
        from combolink.catalog import EMPTY_LINK
        return cast(LinkDiagram, EMPTY_LINK)

    # Dunder methods

    def __eq__(self, other: object) -> bool:
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
            return False
        try:
            return self.normalize().crossings == other.normalize().crossings
        except ValueError:
            return False

    def __invert__(self) -> LinkDiagram:
        return self._reflect()

    def __neg__(self) -> LinkDiagram:
        return self._reverse()

    def __add__(self, other: object) -> LinkDiagram:
        if not isinstance(other, LinkDiagram): return NotImplemented

        return self._disjoint_union(other)

    def __mul__(self, other: object) -> LinkDiagram:
        if not isinstance(other, int): return NotImplemented

        if other == 0: return self._EMPTY_LINK
        if other < 0:
            self = -self
            other = -other

        diagram = self
        for _ in range(other-1):
            diagram = diagram + self
        return diagram

    def __rmul__(self, other: object) -> LinkDiagram:
        return self * other

    def __matmul__(self, other: object) -> LinkDiagram:
        if not isinstance(other, LinkDiagram): return NotImplemented
        return self._connected_sum(other)

    def __pow__(self, other: object) -> LinkDiagram:
        if not isinstance(other, int): return NotImplemented

        if other == 0: return self._UNKNOT
        if other < 0:
            self = ~-self
            other = -other
        
        diagram = self
        for _ in range(other-1): diagram = diagram @ self
        return diagram

    def __rtruediv__(self, other: object) -> LinkDiagram:
        if not isinstance(other, int): return NotImplemented
        return other * ~-self

    def __truediv__(self, other: object) -> LinkDiagram:
        if not isinstance(other, LinkDiagram): return NotImplemented
        return self @ ~-other

    def __len__(self) -> int:
        return self.n_crossings

    def __bool__(self) -> bool:
        return self.n_crossings > 0

    def __iter__(self) -> Iterator[LinkDiagram]:
        return (component for component in self.components)

    def __getitem__(self, key: int | slice) -> LinkDiagram | tuple[LinkDiagram, ...]:
        return self.components[key]

    def __contains__(self, other: LinkDiagram) -> bool:
        return any(other == sublink for sublink in self.sublinks)

    def __le__(self, other: LinkDiagram) -> bool:
        return all(sublink in other for sublink in self.sublinks)

    def __lt__(self, other: LinkDiagram) -> bool:
        return self <= other and self != other

    def __ge__(self, other: LinkDiagram) -> bool:
        return other <= self
    
    def __gt__(self, other: LinkDiagram) -> bool:
        return other < self

    def __hash__(self) -> int:
        try:
            return hash(self.normalize().crossings)
        except ValueError:
            return hash(self.crossings)

    def __rshift__(self, n: int) -> LinkDiagram:
        return self.shift(n)

    def __lshift__(self, n: int) -> LinkDiagram:
        return self.shift(-n)

    def __pos__(self) -> LinkDiagram:
        return self.normalize()

    def normalize(self) -> LinkDiagram:
        """Return a canonical tuple of crossings for knots and multi-component links.

        Invariant under crossing order, component order, and independent
        cyclic edge shifts within each oriented component.
        """
        comp_edges = self._calculate_components()
        if comp_edges is None:
            raise ValueError('cannot normalize an invalid link diagram.')
        if not self._pd_code:
            return LinkDiagram([])

        by_size: dict[int, list[int]] = defaultdict(list)
        for idx, comp in enumerate(comp_edges):
            by_size[len(comp)].append(idx)

        size_groups = [by_size[size] for size in sorted(by_size)]
        comp_orderings = [
            tuple(idx for group in perm_tuple for idx in group)
            for perm_tuple in product(*(permutations(g) for g in size_groups))
        ]

        best: tuple[Crossing, ...] | None = None

        for order in comp_orderings:
            reorder_map: dict[Edge, Edge] = {}
            curr = 1
            for comp_idx in order:
                for edge in comp_edges[comp_idx]:
                    reorder_map[edge] = curr
                    curr += 1

            reordered = LinkDiagram([
                (
                    reorder_map[c[0]],
                    reorder_map[c[1]],
                    reorder_map[c[2]],
                    reorder_map[c[3]],
                )
                for c in self._pd_code
            ])

            shift_ranges = [range(len(comp_edges[i])) for i in order]
            for shift_tuple in product(*shift_ranges):
                shifted = reordered.shift(*shift_tuple)
                candidate = tuple(((e1, e2, e3, e4) for e1, e2, e3, e4 in sorted(shifted.crossings)))
                if best is None or candidate < best:
                    best = candidate

        if best is None:
            raise NotImplementedError

        diagram = LinkDiagram(list(best))
        if not diagram.is_valid():
            raise ValueError('cannot normalize an invalid link diagram.')
        
        return diagram
    
    def _shiftmod(self, edge: Edge, n: int) -> Edge:
        """Shift an edge within its oriented component cycle."""
        for component in self.components_edges:
            if edge in component:
                index = component.index(edge)
                return component[(index + n) % len(component)]
        raise ValueError(f"edge {edge} does not belong to this diagram.")

    def shift(self, *shifts: int) -> LinkDiagram:
        """Cyclically shift edge labels within their oriented components.

        Parameters
        ----------
        *shifts : int
            If a single integer is provided, all components are shifted by that
            amount. Otherwise, one integer per component must be provided to
            shift each component independently.

        Returns
        -------
        LinkDiagram
            A new diagram with the shifted edge labels.

        Raises
        ------
        ValueError
            If this diagram is invalid or the number of shifts does not match
            the number of components.
        """
        comp_edges = self.components_edges  # Raises ValueError if invalid
        if not comp_edges:
            return LinkDiagram([])

        if len(shifts) == 1:
            per_comp_shifts = (shifts[0],) * len(comp_edges)
        elif len(shifts) == len(comp_edges):
            per_comp_shifts = shifts
        else:
            raise ValueError(
                f"Expected 1 shift or {len(comp_edges)} per-component shifts, "
                f"got {len(shifts)}."
            )

        mapping: dict[Edge, Edge] = {}
        for comp, n in zip(comp_edges, per_comp_shifts):
            m = len(comp)
            for i, edge in enumerate(comp):
                mapping[edge] = comp[(i + n) % m]

        return LinkDiagram([
            (
                mapping[crossing[0]],
                mapping[crossing[1]],
                mapping[crossing[2]],
                mapping[crossing[3]],
            )
            for crossing in self._pd_code
        ])

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
        if len(self._pd_code) != len(other._pd_code): return False
        return {tuple(crossing) for crossing in self._pd_code} == {
            tuple(crossing) for crossing in other._pd_code
        }

    def _calculate_components(self) -> tuple[tuple[Edge, ...], ...] | None:
        """Infer components from the opposite-edge connections in the PD code.

        Returns
        -------
        tuple of tuple of Edge or None
            Sorted edge labels grouped by component, or ``None`` if the PD code
            is structurally invalid.
        """
        if self._pd_code == []:
            return ()

        if not self._pd_code:
            return None

        edge_count = 2 * len(self._pd_code)
        edge_counts = [0] * edge_count
        adjacent_edges = [set() for _ in range(edge_count)]

        for crossing in self._pd_code:
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
    def components_edges(self) -> tuple[tuple[Edge, ...], ...]:
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
    def components(self) -> tuple[LinkDiagram, ...]:
        """Return link diagrams per link component.
        
        Returns
        -------
        tuple of LinkDiagram
            Link diagram of each link component.

        Raises
        ------
        ValueError
            If the diagram is invalid.
        """
        if self == self._UNKNOT: return (self._UNKNOT,)
        
        subdiagrams: list[LinkDiagram] = []

        for desired_edges in self.components_edges:
            edge_set = set(desired_edges)
            self_crossings = [
                v for v in self.crossings if all(e in edge_set for e in v)
            ]

            if not self_crossings:
                subdiagrams.append(self._UNKNOT)
                continue

            # Collect every edge that *enters* a self-crossing:
            # - c[0] is always the incoming under-strand
            # - For the over-strand (c[1], c[3]), whichever edge satisfies
            #   _next(edge) == other is the incoming over-strand.
            self_incoming: set[Edge] = set()
            for c in self_crossings:
                self_incoming.add(c[0])
                self_incoming.add(c[1] if self._next(c[1]) == c[3] else c[3])

            # Start at the edge immediately after an incoming edge (guaranteed exit)
            start = self._next(next(iter(self_incoming)))

            edge_map: dict[Edge, Edge] = {}
            curr = start
            label = 1
            for _ in range(len(desired_edges)):
                edge_map[curr] = label
                if curr in self_incoming:
                    label += 1
                curr = self._next(curr)

            comp_pd = [
                (
                    edge_map[c[0]],
                    edge_map[c[1]],
                    edge_map[c[2]],
                    edge_map[c[3]],
                )
                for c in self_crossings
            ]
            subdiagrams.append(LinkDiagram(comp_pd).normalize())

        return tuple(subdiagrams)

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
        return len(self.components_edges)

    @property
    def pd_code(self) -> PDNotation:
        """Return the internally stored planar diagram code.
        
        Returns
        -------
        PDNotation
            The planar diagram code..
        """
        return self._pd_code

    @property
    def crossings(self) -> tuple[Crossing, ...]:
        """Return edge labels grouped by crossing incidence.

        Returns
        -------
        tuple of tuple of Edge
            Each inner tuple contains the labels incident to one crossing.
        """
        return tuple(self._pd_code)

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
        return len(self._pd_code)

    def sublink(self, *component_indices: int) -> LinkDiagram:
        """Extract a sublink consisting of the components at ``component_indices``.

        Crossings internal to the selected components are preserved, while
        crossings involving unselected components are smoothed/removed and
        the surviving edges are re-indexed contiguously starting from 1.
        """
        comp_edges = self.components_edges
        n_comps = len(comp_edges)

        if not component_indices:
            return self._EMPTY_LINK

        selected_indices = sorted(set(component_indices))
        for idx in selected_indices:
            if not 0 <= idx < n_comps:
                raise IndexError(
                    f"Component index {idx} out of range for {n_comps} components."
                )

        if len(selected_indices) == n_comps:
            return self.normalize()

        # Gather all edges belonging to the selected components
        selected_comp_tuples = [comp_edges[i] for i in selected_indices]
        allowed_edges = {e for comp in selected_comp_tuples for e in comp}

        # Keep only crossings where all 4 strands belong to the selected sublink
        kept_crossings = [
            c for c in self.crossings if all(e in allowed_edges for e in c)
        ]

        # Build a fast next-edge lookup across all components
        next_edge: dict[Edge, Edge] = {}
        for comp in comp_edges:
            m = len(comp)
            for i, e in enumerate(comp):
                next_edge[e] = comp[(i + 1) % m]

        # Edges that enter a kept crossing (increment points for new labels)
        kept_incoming: set[Edge] = set()
        for c in kept_crossings:
            kept_incoming.add(c[0])
            kept_incoming.add(c[1] if next_edge[c[1]] == c[3] else c[3])

        # Re-index each selected component contiguously (1..m_1, m_1+1..m_2, ...)
        edge_map: dict[Edge, Edge] = {}
        label = 1
        unknot_count = 0

        for comp in selected_comp_tuples:
            comp_incoming = [e for e in comp if e in kept_incoming]
            if not comp_incoming:
                # This component has no crossings left in the sublink -> unknot
                unknot_count += 1
                continue

            start = next_edge[comp_incoming[0]]
            curr = start
            for _ in range(len(comp)):
                edge_map[curr] = label
                if curr in kept_incoming:
                    label += 1
                curr = next_edge[curr]

        sub_pd: PDNotation = [
            (edge_map[c[0]], edge_map[c[1]], edge_map[c[2]], edge_map[c[3]])
            for c in kept_crossings
        ]

        result = LinkDiagram(sub_pd).normalize() if sub_pd else self._EMPTY_LINK
        for _ in range(unknot_count):
            result = result + self._UNKNOT

        return result

    @property
    def sublinks(self) -> list[LinkDiagram]:
        """Return all sublinks (the powerset of components) ordered by size.

        Parameters
        ----------
        include_empty : bool, default=True
            Whether to include the 0-component empty link as the first element.
        """
        n_comps = self.n_components
        start_size = 0
        return [
            self.sublink(*indices)
            for k in range(start_size, n_comps + 1)
            for indices in combinations(range(n_comps), k)
        ]

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
        return [crossing for crossing in self._pd_code if edge in crossing]

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
        edge = self._pd_code[crossing_index][edge_index]
        crossings_with_edge = self._get_crossings_with_edge(edge)
        
        if len(crossings_with_edge) == 1:
            pos = [i for i, row in enumerate(self._pd_code[crossing_index]) if row == edge]
            return (crossing_index, pos[1] if pos[0] == edge_index else pos[0])
        
        if crossings_with_edge[0] == self._pd_code[crossing_index]:
            return (next(i for i, row in enumerate(self._pd_code) if row == crossings_with_edge[1]), next(i for i, x in enumerate(crossings_with_edge[1]) if x == edge))

        return (next(i for i, row in enumerate(self._pd_code) if row == crossings_with_edge[0]), next(i for i, x in enumerate(crossings_with_edge[0]) if x == edge))

    def _shift_unbounded(self, n: int) -> LinkDiagram:
        """Return a diagram with all of its edge values shifted up by `n` without wrapping around.

        This method is meant for adjusting a diagram to be combined with another.
        """
        return LinkDiagram([tuple(edge + n for edge in crossing) for crossing in self._pd_code])

    def _index_is_facing(self, crossing_index: int, edge_index: int) -> bool:
        """Returns whether or not the given index represents an edge that is facing its crossing."""
        if edge_index == 0: return True
        if edge_index == 1:
            return self._pd_code[crossing_index][3] == self._next(self._pd_code[crossing_index][1])
        if edge_index == 3:
            return self._pd_code[crossing_index][1] == self._next(self._pd_code[crossing_index][3])
        return False

    def _get_forth_index(self, edge: Edge) -> tuple[int, int]:
        """Get the index of the given edge in the crossing it faces toward.

        Note: the edge index is never 2, since the edge would then be
        facing away from the crossing.
        """
        for crossing_index, crossing in enumerate(self._pd_code):
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
        while self._pd_code[crossing_index][edge_index] != edge:
            sign = -1 if self._index_is_facing(crossing_index, edge_index) else 1
            face_ccw.append(sign * self._pd_code[crossing_index][edge_index])
            crossing_index, edge_index = self._get_friend_index(crossing_index, edge_index)
            edge_index = (edge_index - 1) % 4
        
        # Generate the clockwise face.
        crossing_index, edge_index = self._get_forth_index(edge)
        edge_index = (edge_index + 1) % 4
        while self._pd_code[crossing_index][edge_index] != edge:
            sign = -1 if self._index_is_facing(crossing_index, edge_index) else 1
            face_cw.append(sign * self._pd_code[crossing_index][edge_index])
            crossing_index, edge_index = self._get_friend_index(crossing_index, edge_index)
            edge_index = (edge_index + 1) % 4

        return (face_ccw, face_cw)

    def _is_closed(self, edge: Edge) -> bool:
        """Check if an edge on a diagram is closed.
        
        An edge is closed if, on both of the crossings it connects to, it crosses underneath.
        """
        adj_crossings = [crossing for crossing in self._pd_code if edge in crossing]
        return all(edge in [crossing[0], crossing[2]] for crossing in adj_crossings)

    def _is_open(self, edge: Edge) -> bool:
        """Check if an edge on a diagram is open.
        
        An edge is open if, on both of the crossings it connects to, it crosses over.
        """
        adj_crossings = [crossing for crossing in self._pd_code if edge in crossing]
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
        return 'PD[' + ','.join(['X[' + ','.join([str(edge) for edge in crossing]) + ']' for crossing in self._pd_code]) + ']'
