# Combinatorial Graph Model

`to_graph(diagram)` compiles a `LinkDiagram` into the framework-neutral
`CombinatorialLinkDiagram` model. The six core structures encode
`(V, E, psi, w, S, pi)`; derived face-boundary cycles are also included.
Source crossing order and PD edge labels are retained.

## Compile a diagram

```python
import combolink as cl

hopf = cl.torus_link(2, 2)
graph = cl.to_graph(hopf)

print("crossings:", graph.n_crossings)
print("edges:", graph.n_edges)
print("link components:", graph.n_link_components)
print("projection components:", graph.projection_components)
print("face-boundary cycles:", graph.face_cycles)
```

`to_graph()` raises `TypeError` if its argument is not a `LinkDiagram` and
`ValueError` if the diagram is structurally invalid or cannot be compiled as a
spherical planar oriented diagram.

## Meaning of the fields

| Mathematical object | Field | Description |
| --- | --- | --- |
| `V` | `vertices` | A tuple of `GraphCrossing` records in PD row order. |
| `E` | `edges` | A tuple of directed `GraphEdge` records, sorted by original edge label. |
| `psi` | `edge.incidence` | For each edge, `(tail_crossing, head_crossing)`. Crossing indices are zero-based. |
| `w` | `crossing.writhe` | The crossing sign, `-1` or `+1`. |
| `S` | `edge.successor` | The next edge label along the oriented strand. |
| `pi` | `crossing.principal_edge` | The incoming under-crossing edge selected for the crossing. |
| Derived | `face_cycles` | Boundary walks traced from the PD crossing rotations. |
| Derived | `link_components` | Cycles of the strand-successor permutation, as edge labels. |
| Derived | `projection_components` | Connected components of the underlying crossing graph, as crossing indices. |

`GraphCrossing.index` is the zero-based crossing index in the source PD row
order. `GraphEdge.label` is the original one-based PD edge label.
`GraphEdge.incidence` and `GraphEdge.successor` encode different structure:
incidence connects a directed diagram edge to its endpoint crossings, while
successor follows the oriented strand to the next diagram edge.

Each `face_cycles` item is a tuple of `(crossing_index, crossing_position)`
pairs. Both values are zero-based; crossing positions range from 0 to 3.
These cycles are boundary walks derived from the crossing rotations, not a
canonical list of geometric regions.

## Round-trip to PD notation

The graph model reconstructs the original PD code, including its labels and
crossing row order:

```python
diagram = cl.knot(3, 1)
graph = cl.to_graph(diagram)

assert graph.to_pd_code() == diagram.pd_code
```

The model is lossless with respect to the source PD data represented by the
compiler. It does not canonicalize diagrams up to relabeling or knot
equivalence.

## Spherical planarity and disconnected projections

`LinkDiagram.is_valid()` checks PD structure and oriented component cycles.
`to_graph()` adds checks that crossing positions are consistent with oriented
strands and that each connected projection component satisfies the spherical
Euler equation

```text
V_i - E_i + F_i = 2
```

Here, `F_i` counts the face-boundary cycles assigned to projection component
`i`. Summing the component equations gives `V - E + F = 2c`, with `c` the
number of connected projection components. The right-hand side depends on
the number of projection components; it is not the number of cycles.

For disconnected projections, boundary cycles are computed componentwise.
PD codes do not encode how disconnected components are nested in the plane,
so these cycles need not correspond one-to-one with the geometric faces of
the complete projection on the sphere.

## Using the model with graph-learning libraries

ComboLink deliberately has no PyTorch, PyTorch Geometric, or DGL dependency.
An application can adapt the records into its chosen tensor or graph format.
For example, this framework-neutral extraction keeps crossing indices and
edge labels explicit:

```python
crossing_features = [
    (crossing.writhe, crossing.principal_edge)
    for crossing in graph.vertices
]
edge_index = [
    edge.incidence
    for edge in graph.edges
]
edge_features = [
    (edge.label, edge.successor)
    for edge in graph.edges
]
face_walks = graph.face_cycles
```

The example is only an extraction sketch, not a model-specific encoding.
Before building tensors, decide how to represent one-based edge labels,
zero-based crossing indices, principal-edge labels, and variable-length
boundary walks for your application. `face_cycles` are not a precomputed set
of Reidemeister-move regions.

## Related pages

- [Diagrams and construction](diagrams.md)
- [Properties and notation](properties.md)
- [Project overview](../README.md)

