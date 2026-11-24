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

Generate positive torus links directly with positive parameters. The number of
components is `gcd(p, q)`; use `torus_knot` when you specifically require a
single-component knot:

```python
torus_trefoil = cl.torus_link(2, 3)
hopf_link = cl.torus_link(2, 2)
```

You can also create a diagram directly from its PD code, a list of four-edge
crossings:

```python
hopf_link = cl.LinkDiagram([
    (1, 4, 2, 3),
    (3, 2, 4, 1),
])

if hopf_link.is_valid():
    print(hopf_link.n_components)
    print(cl.jones(hopf_link).var("t"))
```

Edge IDs in a link diagram are integers. Check `is_valid()` before computing
properties; property functions raise `ValueError` for invalid diagrams.

## Graph representation

`to_graph` compiles a valid `LinkDiagram` into the framework-neutral
combinatorial model `(V, E, ψ, w, S, π)`. Crossings
are represented by `GraphCrossing` vertices; directed diagram edges remain
`GraphEdge` edges. Each crossing record contains its writhe and principal edge,
while each edge record contains its incidence and strand successor:

```python
model = cl.to_graph(hopf_link)
edge_incidence = {edge.label: edge.incidence for edge in model.edges}
edge_successors = {edge.label: edge.successor for edge in model.edges}
crossing_under_edges = {
    crossing.index: crossing.principal_edge for crossing in model.vertices
}
```

PD edge labels are retained as edge identities, and `model.to_pd_code()`
reconstructs the original PD code. `face_cycles` are
computed directly from PD crossing rotations as cycles of crossing positions,
avoiding construction of a separate edge-side turn map. For disconnected
projections, these boundary walks need not be distinct geometric faces because
PD codes do not encode nesting. Spherical planarity is checked componentwise
as `|V| - |E| + |F| = 2c`, where `F` counts these boundary cycles.

A node-centric GNN can use a separate adapter that lifts edges into nodes; that
encoding is not the canonical combinatorial model returned by `to_graph`.

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

Combine diagrams with `disjoint_union`, or join the components containing the
selected edges with `join`. For connected sums, use `connected_sum` with
single-component knot diagrams:

```python
figure_eight = cl.knot(4, 1)
union = cl.disjoint_union(trefoil, figure_eight)
joined = cl.join(trefoil, figure_eight, self_edge=1, other_edge=1)
sum_knot = cl.connected_sum(trefoil, figure_eight)
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
