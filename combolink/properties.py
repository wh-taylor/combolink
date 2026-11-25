from itertools import product
from combolink.diagram import LinkDiagram, Edge
from combolink.catalog import UNKNOT
from combolink.polynomial import Polynomial

def _require_valid_diagram(self: LinkDiagram) -> None:
    """Raise an error unless ``self`` is a structurally valid diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to validate.

    Raises
    ------
    ValueError
        If ``self`` is not a valid diagram.
    """
    if not self.is_valid():
        raise ValueError("cannot compute link properties for an invalid diagram.")


def _component_encounters(self: LinkDiagram) -> list[list[tuple[int, bool]]]:
    """Return ``(crossing_id, is_over)`` encounters in component order."""
    _require_valid_diagram(self)
    components = self.components
    ports_by_edge: dict[Edge, list[tuple[int, int]]] = {}
    for crossing_index, crossing in enumerate(self.pd_code):
        for position, edge in enumerate(crossing):
            ports_by_edge.setdefault(edge, []).append((crossing_index, position))

    other_port: dict[tuple[int, int], tuple[int, int]] = {}
    for edge, ports in ports_by_edge.items():
        if len(ports) != 2:
            raise ValueError(f"PD edge {edge} must occur at exactly two positions.")
        first, second = ports
        other_port[first] = second
        other_port[second] = first

    next_port = {
        (crossing_index, position): other_port[
            (crossing_index, (position + 2) % 4)
        ]
        for crossing_index in range(len(self.pd_code))
        for position in range(4)
    }

    component_encounters: list[list[tuple[int, bool]]] = []
    for component in components:
        start = min(ports_by_edge[component[0]])
        port = start
        visited_ports: set[tuple[int, int]] = set()
        visited_edges: list[Edge] = []
        encounters: list[tuple[int, bool]] = []

        while port not in visited_ports:
            visited_ports.add(port)
            crossing_index, position = port
            visited_edges.append(self.pd_code[crossing_index][position])
            encounters.append((crossing_index + 1, position in (1, 3)))
            port = next_port[port]

        if (
            port != start
            or len(encounters) != len(component)
            or set(visited_edges) != set(component)
        ):
            raise ValueError("PD positions do not form one traversal per component.")
        component_encounters.append(encounters)

    return component_encounters


def gauss_code(self: LinkDiagram) -> list[list[int]]:
    """Return the Gauss code of a diagram.

    Components follow ``LinkDiagram.components`` order. Each traversal starts
    at the earliest PD occurrence of the component's smallest edge label and
    follows crossing strands and matching edge labels. Crossing IDs are
    one-based PD row indices; positive IDs denote overcrossings and negative
    IDs denote undercrossings.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to encode.

    Returns
    -------
    list of list of int
        One signed crossing-ID sequence per component.

    Raises
    ------
    ValueError
        If the diagram is invalid or its PD positions do not form one
        traversal per component.
    """
    return [
        [crossing_id if is_over else -crossing_id for crossing_id, is_over in visits]
        for visits in _component_encounters(self)
    ]


def dt_notation(self: LinkDiagram) -> list[int]:
    """Return classical Dowker-Thistlethwaite notation for a knot diagram.

    Encounters are numbered in the deterministic component traversal order.
    For each odd-numbered encounter, the notation records its paired even
    position, negated when that even encounter is an overcrossing.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to encode.

    Returns
    -------
    list of int
        One signed even partner position per crossing.

    Raises
    ------
    ValueError
        If the diagram is invalid, has multiple components, or its crossing
        encounters do not satisfy the odd-even pairing required by classical
        DT notation.
    """
    encounters = _component_encounters(self)
    if len(encounters) != 1:
        raise ValueError("DT notation is only defined for single-component diagrams.")

    visits = encounters[0]
    if len(visits) % 2:
        raise ValueError("DT notation requires an even number of crossing encounters.")

    positions_by_crossing: dict[int, list[int]] = {}
    for position, (crossing_id, _) in enumerate(visits, start=1):
        positions_by_crossing.setdefault(crossing_id, []).append(position)

    partner_by_position: dict[int, int] = {}
    for crossing_id, positions in positions_by_crossing.items():
        if len(positions) != 2:
            raise ValueError(
                f"crossing {crossing_id} must have exactly two encounters."
            )
        first, second = positions
        if first % 2 == second % 2:
            raise ValueError(
                "crossing encounters must have opposite parity for classical "
                "DT notation."
            )
        partner_by_position[first] = second
        partner_by_position[second] = first

    return [
        -partner_by_position[position]
        if visits[partner_by_position[position] - 1][1]
        else partner_by_position[position]
        for position in range(1, len(visits) + 1, 2)
    ]

def kauffman_bracket(self: LinkDiagram) -> Polynomial:
    """Compute the Kauffman bracket polynomial of a diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose bracket is computed.

    Returns
    -------
    Polynomial
        The Kauffman bracket in the library's Laurent-polynomial format.

    Raises
    ------
    ValueError
        If ``self`` is not a valid diagram.
    """
    _require_valid_diagram(self)
    if self == UNKNOT: return Polynomial({-3: -1})
    if self == ~UNKNOT: return Polynomial({3: -1})

    factored_poly = [(((a, d), (b, c)), ((a, b), (c, d))) for a, b, c, d in self.pd_code]

    distributed_poly = [(sum(1-2*i for i in ii), [factor for term in terms for factor in term]) for ii, terms in zip(product(*(range(2) for _ in factored_poly)), product(*factored_poly))]

    for power, term in distributed_poly:
        matched_at_all = True
        while matched_at_all:
            matched_at_all = False
            i = 0
            if len(term) == 1: break
            while i < len(term):
                j = i + 1
                while j < len(term):
                    x1, x2 = term[i], term[j]
                    a1, b1 = x1
                    a2, b2 = x2

                    matched = True

                    if a1 == b2 and a2 == b1 or a1 == a2 and b1 == b2:
                        term.append((a1, a1))
                    elif a1 == a2:
                        term.append((b1, b2))
                    elif a1 == b2:
                        term.append((b1, a2))
                    elif b1 == a2:
                        term.append((a1, b2))
                    elif b1 == b2:
                        term.append((a1, a2))
                    else:
                        matched = False

                    if matched: del term[j], term[i]
                    if matched: matched_at_all = True
                    j += 1
                i += 1

    newlist = [(power, len(term)-1) for power, term in distributed_poly]

    disjoint_unknot_poly = Polynomial({2: -1, -2: -1})

    return sum((Polynomial({power1: 1}) * disjoint_unknot_poly**power2 for power1, power2 in newlist), Polynomial.zero())

def get_writhe(self: LinkDiagram) -> int:
    """Compute the writhe of an oriented diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose crossing signs are summed.

    Returns
    -------
    int
        The sum of the signed crossings.

    Raises
    ------
    ValueError
        If ``self`` is not a valid diagram.
    """
    _require_valid_diagram(self)
    if self == UNKNOT: return 1
    if self == ~UNKNOT: return -1

    writhe = 0
    for _, b, _, d in self.pd_code:
        if self._next(b) == d:
            writhe -= 1
        else:
            writhe += 1
    return writhe

def jones(self: LinkDiagram) -> Polynomial:
    """Compute the Jones polynomial of a diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose Jones polynomial is computed.

    Returns
    -------
    Polynomial
        The Jones polynomial in the library's Laurent-polynomial format.

    Raises
    ------
    ValueError
        If ``self`` is not a valid diagram.
    """
    writhe = get_writhe(self)
    bracket = kauffman_bracket(self)
    raw_jones_polynomial = bracket * Polynomial({3*writhe: 1 if writhe % 2 == 0 else -1})
    coefficients = {powers[0]/4: coefficients for powers, coefficients in raw_jones_polynomial.coefficients.items()}
    return Polynomial(coefficients)

def get_edges(self: LinkDiagram) -> list[Edge]:
    """Return the edge labels used by a diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram whose edge labels are enumerated.

    Returns
    -------
    list of Edge
        The integer labels from one through twice the crossing count.
    """
    return [i + 1 for i in range(2 * len(self.pd_code))]

def get_plaintext_code(self: LinkDiagram) -> str:
    """Serialize a diagram as a compact semicolon-delimited PD code.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to serialize.

    Returns
    -------
    str
        The crossing list in the library's plaintext format.
    """
    output = '['
    for i, (a, b, c, d) in enumerate(self.pd_code):
        output += f'[{a};{b};{c};{d}]'
        if i != len(self.pd_code) - 1:
            output += ';'
    output += ']'
    return output
