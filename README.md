# ComboLink

**ComboLink** is a lightweight Python library for representing, manipulating, and analyzing oriented knot and link diagrams. It combines a planar-diagram (PD) representation with a framework-neutral **6-tuple combinatorial graph compiler** (`to_graph`).

* **No external runtime dependencies**; Python 3.12 or newer.
* **Combinatorial graph representation** $(V, E, \psi, w, S, \pi)$ with component-wise spherical planarity checks in `to_graph`.
* **Reidemeister move operations** (`left_positive_twist`, `right_positive_twist`, `left_negative_twist`, `right_negative_twist`, `untwist`, `poke`, `unpoke`, `slide`) and candidate enumerators.
* **Polynomial invariants and a bundled prime-knot catalog**, including the Kauffman bracket, Jones polynomial, and writhe.

This is a pre-1.0 project; its public API may change.

---

## Installation

Install from a local source checkout:

```bash
python -m pip install .
```

For development, install the project and its test dependencies in editable
mode with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked --extra dev --inexact
```

Or install directly from GitHub:

```bash
python -m pip install git+https://github.com/wh-taylor/combolink.git
```

---

## Quick Start

### Catalog Lookups & Polynomial Invariants

The bundled catalog currently includes entries through 13 crossings. For
entries above 10 crossings, provide the alternating status (`"a"` or `"n"`).

```python
import combolink as cl

# Look up prime knots by crossing number and catalog index
trefoil = cl.knot(3, 1)
figure_eight = cl.knot(4, 1)

# Select the alternating catalog for this 11-crossing knot
alternating_11_crossing_knot = cl.knot(11, 1, "a")

print("PD code:", trefoil.pd_code)
print("Components:", trefoil.n_components)
print("Writhe:", cl.get_writhe(trefoil))
print("Kauffman bracket:", cl.kauffman_bracket(trefoil).var("A"))
print("Jones polynomial:", cl.jones(trefoil).var("t"))
```

### Torus Links & Custom PD Codes

ComboLink treats links as **oriented by default**. Each crossing in a PD code is a 4-tuple `(under_in, over_first, under_out, over_second)` ordered counter-clockwise starting from the incoming under-strand:

```python
import combolink as cl

# Positive torus links T(p, q) have gcd(p, q) components
torus_trefoil = cl.torus_knot(2, 3)   # enforces 1-component knot
hopf_link = cl.torus_link(2, 2)       # 2-component link

# Construct directly from PD notation
custom_hopf = cl.LinkDiagram([
    (1, 4, 2, 3),
    (3, 2, 4, 1),
])

if custom_hopf.is_valid():
    print("Valid diagram with", custom_hopf.n_components, "components")
```

`LinkDiagram.is_valid()` checks structural validity of the PD code. It does
not verify that the crossing orientations or projection are planar;
`to_graph()` performs those additional checks.

### Reidemeister Moves & Diagram Operations

The examples below show symmetry operations, Reidemeister moves, candidate
discovery, and diagram combinations. Reidemeister moves preserve the
represented link type when applied successfully; reflection, reversal, and
diagram-combination operations have distinct effects. Candidate-discovery
functions return lists of applicable moves:

```python
import combolink as cl

trefoil = cl.knot(3, 1)
figure_eight = cl.knot(4, 1)

# Symmetry operations
mirror = cl.reflect(trefoil)
reversed_orient = cl.reverse(trefoil)

# Reidemeister II poke insertion & invariant verification
poked = cl.poke(trefoil, under_edge=1, over_edge=4)
assert cl.kauffman_bracket(poked) == cl.kauffman_bracket(trefoil)

# Enumerate candidate moves
untwist_candidates = cl.get_untwistables(poked)
poke_candidates = cl.get_pokables(trefoil)

# Combining diagrams
union = cl.disjoint_union(trefoil, figure_eight)
joined = cl.join(trefoil, union, self_edge=1, other_edge=1)
connected = cl.connected_sum(trefoil, figure_eight)
```

### Gauss Code & DT Notation

`gauss_code()` returns one signed sequence per component. Crossing IDs are
one-based PD row indices; positive entries denote overcrossings and negative
entries denote undercrossings. Components follow `LinkDiagram.components`
order; each traversal starts at the earliest PD occurrence of that component's
smallest edge label.

`dt_notation()` returns classical Dowker-Thistlethwaite notation for a
single-component diagram and raises `ValueError` for links. It records the
paired even encounter position for each odd encounter, negating the entry when
the even encounter is an overcrossing:

```python
gauss = cl.gauss_code(trefoil)
dt = cl.dt_notation(trefoil)  # [4, 6, 2]
```

---

## Declarative 6-Tuple Graph Model (`to_graph`)

PD codes compactly encode crossings and edge labels. `cl.to_graph()` makes their incidence, strand succession, crossing writhe, and principal under-edge explicit in a framework-neutral **combinatorial link diagram** $D = (V, E, \psi, w, S, \pi)$ with derived face-boundary cycles $F_D$. It retains source crossing indices and edge labels; it does not canonicalize diagrams up to relabeling.

| Symbol | Field on `CombinatorialLinkDiagram` | Mathematical Meaning |
| :--- | :--- | :--- |
| V | `vertices: tuple[GraphCrossing, ...]` | Crossing vertices (`index`, `writhe`, `principal_edge`). |
| E | `edges: tuple[GraphEdge, ...]` | Directed diagram edges (`label`, `incidence`, `successor`). |
| ψ | `edge.incidence` | Incidence map ψ = (ψ₁, ψ₂) : E → V × V `(tail, head)`. |
| w | `crossing.writhe` | Crossing writhe sign $w(v) \in \{-1, +1\}$. |
| S | `edge.successor` | Oriented strand successor permutation S : E → E. |
| π | `crossing.principal_edge` | Principal incoming under-crossing edge π(v) ∈ E. |
| $F_D$ | `face_cycles` | Boundary walks derived directly from the PD crossing rotations. |

### Example: Compiling & Round-Tripping

```python
import combolink as cl

hopf = cl.torus_link(2, 2)
graph = cl.to_graph(hopf)

print("Crossings |V|:", graph.n_crossings)
print("Edges |E|:", graph.n_edges)
print("Boundary walks |F|:", len(graph.face_cycles))
print("Link components:", graph.n_link_components)
print("Projection components:", len(graph.projection_components))

# Exact lossless round-trip back to PD notation
assert graph.to_pd_code() == hopf.pd_code
```

### Spherical Planarity & Disconnected Projections

`to_graph()` validates spherical planarity component by component. For each connected projection component $i$, it checks $|V_i| - |E_i| + |F_i| = 2$, where $F_i$ counts that component's boundary walks. Summing these equations gives $|V| - |E| + |F_D| = 2c$, where $F_D$ is the total number of boundary walks and $c$ is the number of connected components of the underlying crossing graph $(V, E, \psi)$. In particular, $2c$ is the right-hand side of the Euler equation, not the number of boundary walks. For disconnected projections, the cycles are computed componentwise; because PD codes omit nesting, they need not correspond one-to-one with the geometric faces of the whole projection on $S^2$.

### Using `to_graph` with Graph Neural Networks

`combolink` intentionally avoids ML dependencies (`torch`, `torch_geometric`, `dgl`). A downstream adapter can lift `CombinatorialLinkDiagram` into a model-specific graph representation without changing the framework-neutral core. `face_cycles` are boundary walks, not a precomputed list of Reidemeister-move regions.

---

## API Overview

| Module / Category | Key Functions & Classes |
| :--- | :--- |
| **Core Diagram** | `LinkDiagram`, `is_valid()`, `pd_code`, `components`, `n_components` |
| **Graph Compilation** | `to_graph()`, `CombinatorialLinkDiagram`, `GraphCrossing`, `GraphEdge`, `to_pd_code()` |
| **Catalogs & Constructors** | `knot()`, `first_n_knots()`, `torus_link()`, `torus_knot()` |
| **Reidemeister Moves** | `left_positive_twist()`, `right_positive_twist()`, `left_negative_twist()`, `right_negative_twist()`, `untwist()`, `poke()`, `unpoke()`, `slide()` |
| **Move Discovery** | `get_twistables()`, `get_untwistables()`, `get_pokables()`, `get_unpokables()`, `get_slidables()` |
| **Diagram Algebra** | `reflect()`, `reverse()`, `disjoint_union()`, `join()`, `connected_sum()` |
| **Invariants** | `get_writhe()`, `kauffman_bracket()`, `jones()` |
| **Diagram Notation** | `gauss_code()`, `dt_notation()` (classical DT is single-component only) |

---

## Development & Testing

Run the test suite using the checked-in lockfile:

```bash
uv run --locked --extra dev python -m pytest -q
```

---

## Citation & License

Released under the **MIT License**. If you use `combolink` in academic work, please cite the repository:

```bibtex
@software{taylor_combolink_2026,
  author       = {Taylor, W. Hayden and Kutluay, Deniz},
  title        = {ComboLink: Combinatorial Link Diagrams and Graph Compilation in Python},
  year         = {2026},
  url          = {https://github.com/wh-taylor/combolink}
}
```
