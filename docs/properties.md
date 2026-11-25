# Properties and Notation

This page covers diagram properties and encodings exposed by
`combolink.properties`. For the full `Polynomial` API, see
[Working with polynomials](polynomials.md).

## Writhe

`get_writhe(diagram)` returns the sum of the signed crossings for the oriented
diagram:

```python
import combolink as cl

trefoil = cl.knot(3, 1)
writhe = cl.get_writhe(trefoil)
```

Writhe depends on crossing signs and is a diagram property, not an invariant
under all Reidemeister moves. For example, a Type I move changes writhe.

## Kauffman bracket and Jones polynomial

`kauffman_bracket(diagram)` returns the Kauffman bracket as a Laurent
polynomial in `A`. The bracket is invariant under Type II and Type III moves,
but changes under Type I moves. `jones(diagram)` applies writhe normalization
to return the Jones polynomial in the library's `t` variable:

```python
trefoil = cl.knot(3, 1)

bracket = cl.kauffman_bracket(trefoil)
jones = cl.jones(trefoil)

print(bracket.var("A"))
print(jones.var("t"))
```

The bracket implementation enumerates smoothing choices at every crossing,
so the number of states grows exponentially with the crossing count. It is
most suitable for small and moderate diagrams rather than large-scale
computation.

## Gauss code

`gauss_code(diagram)` returns a list containing one signed sequence per
component:

- Each crossing ID is the one-based row number of that crossing in `pd_code`.
- A positive ID marks an overcrossing; a negative ID marks an undercrossing.
- The result has one sequence per component.
- Component order follows `LinkDiagram.components`; traversal begins from a
  deterministic PD occurrence for each component.

```python
trefoil = cl.knot(3, 1)
gauss = cl.gauss_code(trefoil)

assert gauss == [[2, -1, 3, -2, 1, -3]]
```

IDs refer to PD row order, so reordering crossing rows can change the code.
The representation is deterministic for a given PD code, but is not a
canonical identifier for a knot or link.

## Dowker-Thistlethwaite notation

`dt_notation(diagram)` returns classical Dowker-Thistlethwaite notation for a
single-component diagram. It numbers encounters in traversal order and stores
one paired even position for each odd position. An entry is negative when the
even encounter is an overcrossing:

```python
dt = cl.dt_notation(cl.knot(3, 1))
assert dt == [4, 6, 2]
```

The function raises `ValueError` for a multi-component diagram or when the
encounters do not have the odd/even pairing required by classical DT
notation. Use `gauss_code()` for links with multiple components.

## Plain-text PD code

`get_plaintext_code(diagram)` serializes the current crossing list using
semicolon delimiters:

```python
text = cl.get_plaintext_code(cl.knot(3, 1))
print(text)
```

This is a compact representation for display or storage. It is not a
canonical form, and ComboLink does not currently expose a parser for this
string format.

## Related pages

- [Working with polynomials](polynomials.md)
- [Diagrams and construction](diagrams.md)
- [Diagram operations](operations.md)
- [Combinatorial graph model](graph-model.md)

