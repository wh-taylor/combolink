# Diagrams and Construction

The central object in ComboLink is `LinkDiagram`. It stores an oriented
diagram as a list of planar-diagram (PD) crossing tuples. Use this page when
you need to understand the edge-label conventions, build diagrams, or decide
whether an input is structurally valid.

## PD crossing convention

Each crossing is represented by four edge labels:

```text
(under_in, over_first, under_out, over_second)
```

The labels are listed counter-clockwise starting at the incoming under-strand.
The opposite-position pairs are `(0, 2)` for the under-strand and `(1, 3)` for
the over-strand. Orientation follows the tuple: the first edge continues to
the third, and the second continues to the fourth.

For `n` crossings, valid edge labels are the integers `1` through `2n`. Each
label occurs exactly twice in the crossing list, representing the two ends of
one diagram edge. The repeated label need not occur at different crossings;
one-crossing unknot encodings are supported by this representation.

```python
import combolink as cl

hopf = cl.LinkDiagram([
    (1, 4, 2, 3),
    (3, 2, 4, 1),
])

assert hopf.is_valid()
assert hopf.n_components == 2
```

The constructor stores the supplied code without validating it. This lets you
construct a candidate PD code and then check it explicitly.

## Structural validation and components

`is_valid()` verifies the structural rules that `LinkDiagram` uses:

- The PD code is nonempty.
- Every crossing has four integer edge labels in the expected range.
- Every edge label occurs exactly twice.
- Opposite crossing positions form contiguous oriented edge cycles.

It does **not** validate that the crossing rotations form a spherical planar
projection. Use [`to_graph()`](graph-model.md) when you need that additional
check.

`components` returns a tuple of components, each represented by its edge
labels. `n_components` is the number of those groups. Accessing either
property on an invalid diagram raises `ValueError`.

```python
print(hopf.components)
print(hopf.n_components)

if not hopf.is_valid():
    raise ValueError("the supplied PD code is structurally invalid")
```

Components are groups of labels, not a canonical diagram traversal or a
crossing ordering. For the traversal convention used by the Gauss-code
encoder, see [Properties and notation](properties.md#gauss-code).

## Look up catalog knots

`knot(crossings, index, alt_status="")` looks up a prime knot in the bundled
catalog. `index` is one-based. For entries above ten crossings, select the
alternating (`"a"`) or non-alternating (`"n"`) catalog:

```python
trefoil = cl.knot(3, 1)
figure_eight = cl.knot(4, 1)
alternating_eleven_crossing = cl.knot(11, 1, "a")

# A list of (catalog name, LinkDiagram) pairs.
first_entries = cl.first_n_knots(5)
```

The catalog currently contains entries through 13 crossings. A request for a
missing entry, or an incompatible alternating-status argument, raises
`KeyError`. `first_n_knots(n)` returns a list of the first `n` catalog entries.

## Generate torus knots and links

`torus_link(p, q)` builds the positive torus link `T(p, q)` for positive
integer winding counts. Its number of components is `gcd(p, q)`.
`torus_knot(p, q)` uses the same construction but requires coprime parameters:

```python
trefoil = cl.torus_knot(2, 3)
hopf = cl.torus_link(2, 2)

assert trefoil.n_components == 1
assert hopf.n_components == 2
```

Both functions raise `ValueError` if either parameter is not a positive
integer. `torus_knot` also raises `ValueError` if the parameters are not
coprime.

## Prepare and inspect custom input

Build a `LinkDiagram` directly when a PD code comes from another program or
from your own construction:

```python
custom = cl.LinkDiagram([
    (1, 4, 2, 3),
    (3, 2, 4, 1),
])

if custom.is_valid():
    print(custom.pd_code)
    print(custom.components)
```

`pd_code` is a public mutable list. If you edit it directly, call
`is_valid()` again before using operations that assume a valid diagram.
ComboLink operations generally return new diagram objects rather than
modifying the input; see [Diagram operations](operations.md).

`get_edges(diagram)` returns the labels `1` through `2n` for a structurally
valid diagram. `get_plaintext_code(diagram)` serializes the crossing list in
the library's semicolon-delimited format, for example:

```python
text = cl.get_plaintext_code(custom)
print(text)  # [[1;4;2;3];[3;2;4;1]]
```

This is a compact output format; the library does not currently provide a
matching parser for it.

## Diagram equality

`diagram_a == diagram_b` tests for equality between oriented knot diagrams up
to spherical isotopy. It compares valid diagrams while allowing cyclic
edge-label shifts through the diagram's `shift()` operation.

`diagram_a.identical(diagram_b)` functions similarly, but it also considers
how edges are labeled internally, and so it is stronger than usual equivalence.
It is worth noting that these comparisons do not test whether arbitrary diagrams
represent the same knot or link.

## Related pages

- [Diagram operations](operations.md)
- [Properties and notation](properties.md)
- [Combinatorial graph model](graph-model.md)

