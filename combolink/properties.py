from itertools import product
from combolink.diagram import *


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


def gauss_code(self: LinkDiagram) -> list[int]:
    """Return the Gauss code of a diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to encode.

    Returns
    -------
    list of int
        Crossing encounters in traversal order.

    Raises
    ------
    NotImplementedError
        This function is not implemented yet.
    """
    raise NotImplementedError

def dt_notation(self: LinkDiagram) -> list[int]:
    """Return the Dowker-Thistlethwaite notation of a diagram.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to encode.

    Returns
    -------
    list of int
        The Dowker-Thistlethwaite sequence.

    Raises
    ------
    NotImplementedError
        This function is not implemented yet.
    """
    raise NotImplementedError

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
    if self == LinkDiagram([(1, 1, 2, 2)]): return Polynomial({3: -1})

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

def is_infinity_unknot(self: LinkDiagram) -> bool:
    """Check whether ``self`` uses a recognized one-crossing unknot encoding.

    Parameters
    ----------
    self : LinkDiagram
        LinkDiagram to check.

    Returns
    -------
    bool
        Whether the diagram matches either of the library's one-crossing
        unknot encodings, up to cyclic edge-label shifts.
    """
    return self == LinkDiagram([(1, 2, 2, 1)]) or self == LinkDiagram([(2, 2, 1, 1)])

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
