from itertools import islice
from math import gcd
from pathlib import Path

from combolink.diagram import Diagram, Edge, PDNotation

# Load the catalog of predefined prime knot diagrams.
_knot_catalog: dict[str, str] = {}
with Path(__file__).with_name("knotinfo.csv").open() as f:
    for line in f.readlines():
        parts = line.split(",")
        name, raw_pd = parts[0], parts[1]
        _knot_catalog[name] = raw_pd


def _raw_pd_to_pd(raw_pd: str) -> PDNotation:
    """Parse the catalog's compact representation of a PD code.

    Parameters
    ----------
    raw_pd : str
        Crossing labels separated by semicolons.

    Returns
    -------
    PDNotation
        The parsed list of four-edge crossings. An empty input represents the
        unknot and produces an empty list.
    """
    str_ns = raw_pd.replace("[", "").replace("]", "").strip().split(";")
    if str_ns == [""]:
        return []  # Handle the unknot (no crossings)
    ns = list(map(int, str_ns))
    pd_code = []
    for i in range(int(len(ns) / 4)):
        pd_code.append((ns[4 * i], ns[4 * i + 1], ns[4 * i + 2], ns[4 * i + 3]))
    return pd_code


def knot(crossings: int, index: int, alt_status: str = "") -> Diagram:
    """Look up a prime knot diagram in the bundled catalog.

    Parameters
    ----------
    crossings : int
        Number of crossings in the catalog entry.
    index : int
        One-based catalog index for the knot.
    alt_status : str, default=""
        Alternating status for entries above ten crossings. Use ``"a"`` for
        alternating or ``"n"`` for non-alternating entries.

    Returns
    -------
    Diagram
        The knot diagram associated with the requested catalog entry.

    Raises
    ------
    KeyError
        If the requested entry does not exist or the alternating status is
        required or disallowed for the given crossing count.
    """
    if alt_status == "" and crossings > 10:
        raise KeyError(
            "knots with greater than 10 crossings require an argument 'a' or 'n'."
        )
    if alt_status != "" and crossings <= 10:
        raise KeyError(
            "knots with crossings 10 or fewer are not distinguished by alternating or non-alternating."
        )

    name = f"{crossings}{alt_status}_{index}"

    try:
        raw_pd = _knot_catalog[name]
    except KeyError:
        raise KeyError(f"knot {name} does not exist.")

    return Diagram(_raw_pd_to_pd(raw_pd))


def _relabel_oriented_pd_code(pd_code: PDNotation) -> PDNotation:
    """Relabel a PD code using its oriented edge cycles.

    Parameters
    ----------
    pd_code : PDNotation
        Crossings whose input-to-output edge mapping forms disjoint cycles.

    Returns
    -------
    PDNotation
        The same crossings with edge labels assigned consecutively by cycle.

    Raises
    ------
    RuntimeError
        If the crossing edges do not form oriented cycles.
    """
    successors: dict[Edge, Edge] = {}
    for first, second, third, fourth in pd_code:
        successors[first] = third
        successors[second] = fourth

    if len(successors) != 2 * len(pd_code) or set(successors.values()) != set(
        successors
    ):
        raise RuntimeError("could not construct oriented braid edge cycles.")

    relabeling: dict[Edge, Edge] = {}
    next_label = 1
    unvisited = set(successors)
    while unvisited:
        start = min(unvisited)
        edge = start
        while edge in unvisited:
            unvisited.remove(edge)
            relabeling[edge] = next_label
            next_label += 1
            edge = successors[edge]
        if edge != start:
            raise RuntimeError("could not construct oriented braid edge cycles.")

    return [
        (
            relabeling[first],
            relabeling[second],
            relabeling[third],
            relabeling[fourth],
        )
        for first, second, third, fourth in pd_code
    ]


def _validate_torus_parameters(p: int, q: int) -> None:
    """Validate positive integer parameters for a torus diagram.

    Parameters
    ----------
    p, q : int
        Meridional and longitudinal winding counts.

    Raises
    ------
    ValueError
        If either parameter is not a positive integer.
    """
    if type(p) is not int or type(q) is not int or p < 1 or q < 1:
        raise ValueError("p and q must be positive integers.")


def _generate_torus_link_diagram(p: int, q: int) -> Diagram:
    """Generate an oriented PD diagram for the positive torus link T(p, q).

    Parameters
    ----------
    p, q : int
        Positive winding counts.

    Returns
    -------
    Diagram
        A diagram with ``gcd(p, q)`` components.
    """
    if p == 1 or q == 1:
        return Diagram([(1, 2, 2, 1)])

    strand_count = min(p, q)
    repetitions = max(p, q)
    next_edge = strand_count + 1
    active_edges = list(range(1, strand_count + 1))
    top_edges = active_edges.copy()
    crossings: PDNotation = []

    for _ in range(repetitions):
        for left_position in range(strand_count - 1):
            left_in, right_in = active_edges[left_position : left_position + 2]
            left_out, right_out = next_edge, next_edge + 1
            next_edge += 2
            crossings.append((left_in, right_in, left_out, right_out))
            active_edges[left_position] = right_out
            active_edges[left_position + 1] = left_out

    closure = dict(zip(active_edges, top_edges))
    closed_crossings: PDNotation = [
        (
            closure.get(first, first),
            closure.get(second, second),
            closure.get(third, third),
            closure.get(fourth, fourth),
        )
        for first, second, third, fourth in crossings
    ]
    diagram = Diagram(_relabel_oriented_pd_code(closed_crossings))
    if not diagram.is_valid() or diagram.n_components != gcd(p, q):
        raise RuntimeError("could not generate a valid torus link diagram.")
    return diagram


def torus_link(p: int, q: int) -> Diagram:
    """Generate the positive torus link T(p, q).

    Parameters
    ----------
    p, q : int
        Positive winding counts. The resulting link has ``gcd(p, q)``
        components.

    Returns
    -------
    Diagram
        An oriented PD diagram of the torus link.

    Raises
    ------
    ValueError
        If either parameter is not a positive integer.
    """
    _validate_torus_parameters(p, q)
    return _generate_torus_link_diagram(p, q)


def torus_knot(p: int, q: int) -> Diagram:
    """Generate the positive torus knot T(p, q).

    Parameters
    ----------
    p, q : int
        Positive, coprime winding counts.

    Returns
    -------
    Diagram
        An oriented PD diagram of the torus knot.

    Raises
    ------
    ValueError
        If either parameter is not a positive integer or if they are not
        coprime.
    """
    _validate_torus_parameters(p, q)
    if gcd(p, q) != 1:
        raise ValueError("p and q must be coprime to define a torus knot.")
    return _generate_torus_link_diagram(p, q)


# Generator of all prime knot diagrams in the catalog.
PRIME_KNOTS = ((name, Diagram(_raw_pd_to_pd(value))) for name, value in _knot_catalog.items())


def first_n_knots(n: int) -> list[tuple[str, Diagram]]:
    """Return the first ``n`` entries from the prime-knot catalog.

    Parameters
    ----------
    n : int
        Maximum number of catalog entries to return.

    Returns
    -------
    list of tuple of str and Diagram
        Catalog names paired with freshly constructed knot diagrams.

    Raises
    ------
    ValueError
        If ``n`` is negative.
    """
    return [
        (name, Diagram(_raw_pd_to_pd(value)))
        for name, value in islice(_knot_catalog.items(), n)
    ]


# https://en.m.wikipedia.org/wiki/File:Thistlethwaite_unknot.svg
THISTLETHWAITE_UNKNOT = Diagram(
    [
        (22, 2, 23, 1),
        (3, 27, 4, 26),
        (5, 21, 6, 20),
        (7, 18, 8, 19),
        (9, 25, 10, 24),
        (11, 2, 12, 3),
        (4, 13, 5, 14),
        (15, 6, 16, 7),
        (30, 17, 1, 18),
        (19, 14, 20, 15),
        (28, 22, 29, 21),
        (23, 11, 24, 10),
        (25, 9, 26, 8),
        (27, 12, 28, 13),
        (16, 29, 17, 30),
    ]
)

# https://en.m.wikipedia.org/wiki/File:Ochiai_unknot.svg
OCHIAI_UNKNOT = Diagram(
    [
        (12, 2, 13, 1),
        (3, 6, 4, 7),
        (5, 24, 6, 25),
        (7, 15, 8, 14),
        (16, 10, 17, 9),
        (26, 12, 1, 11),
        (13, 20, 14, 21),
        (22, 15, 23, 16),
        (10, 18, 11, 17),
        (19, 3, 20, 2),
        (21, 8, 22, 9),
        (23, 4, 24, 5),
        (25, 19, 26, 18),
    ]
)
