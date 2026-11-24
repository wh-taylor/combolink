# Combolink

Combolink is a Python library for working with knot and link diagrams. It
provides a catalog of prime knots, planar-diagram (PD) codes, diagram
transformations, and several link properties and polynomial invariants.

The project is under active development, so its API may change. It requires
Python 3.12 or newer.

## Installation

Install from a source checkout:

```shell
python -m pip install .
```

Or install directly from Git:

```shell
python -m pip install git+https://github.com/wh-taylor/unknotter.git
```

## Quick start

Look up a knot by its crossing number and catalog index, then inspect its
diagram and compute some properties:

```python
import combolink as cl

trefoil = cl.knot(3, 1)

print(trefoil.pd_code)
print(trefoil.n_components)
print(cl.get_writhe(trefoil))
print(cl.kauffman_bracket(trefoil).var("A"))
```

The function `knot(crossings, index)` looks up knots with up to 10 crossings. For knots
above 10 crossings, provide the alternating status as `"a"` or `"n"`:

```python
alternating_knot = cl.knot(11, 1, "a")
```

You can also create a diagram directly from its PD code, a list of four-edge
crossings:

```python
hopf_link = cl.Diagram([
    (1, 4, 2, 3),
    (3, 2, 4, 1),
])

if hopf_link.is_valid():
    print(hopf_link.n_components)
    print(cl.jones(hopf_link).var("t"))
```

Diagram edge IDs are integers. Check `is_valid()` before computing properties;
property functions raise `ValueError` for invalid diagrams.

## Working with diagrams

The top-level `combolink` module exports the main API. For example, diagrams
can be reflected or reversed, and Reidemeister moves can be applied directly:

```python
import combolink as cl

trefoil = cl.knot(3, 1)

reflected = cl.reflect(trefoil)
reversed_diagram = cl.reverse(trefoil)

poked = cl.poke(trefoil, under_edge=1, over_edge=4)
same_bracket = cl.kauffman_bracket(poked) == cl.kauffman_bracket(trefoil)
```

Available move functions include `poke`, `unpoke`, `slide`, `untwist`, and
the four positive/negative left/right twist functions. Helpers such as
`get_pokables` and `get_untwistables` list candidate edges for moves.

The catalog can also be explored with `first_n_knots(n)`, which returns a
list of `(name, diagram)` pairs.

## Running the tests

From the repository root, run the test suite with
[uv](https://docs.astral.sh/uv/):

```shell
uv run --with pytest pytest
```
