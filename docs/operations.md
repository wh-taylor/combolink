# Diagram Operations

ComboLink provides transformations, local Reidemeister moves, move discovery,
and operations for combining diagrams. Functions take diagrams as explicit
arguments and return results as new `LinkDiagram` objects. Edge labels refer
to the input diagram at the time the operation is called.

## Reflection and orientation reversal

`reflect(diagram)` produces a mirror-image diagram. `reverse(diagram)` reverses
the orientations of its components:

`reverse(diagram)` reverses the orientation of `diagram`, and so it results in
a link diagram that is equivalent when regarding unoriented link diagrams. On the
other hand, `reflect(diagram)` produces a mirror-image diagram, which is only
equivalent to `diagram` if it is achiral, such as `4_1`.

```python
import combolink as cl

trefoil = cl.knot(3, 1)
reverse = cl.reverse(trefoil)
mirror = cl.reflect(trefoil)
```

## Apply a specific Reidemeister move

Reidemeister moves change the projection while preserving the represented
link type when successfully applied. The low-level functions accept edge
labels:

| Move | Function | Arguments |
| --- | --- | --- |
| Type I insertion | `left_positive_twist`, `left_negative_twist`, `right_positive_twist`, `right_negative_twist` | One edge |
| Type I removal | `untwist` | An edge that occurs twice at a twist crossing |
| Type II insertion | `poke` | `under_edge`, then `over_edge` |
| Type II removal | `unpoke` | Two edges identifying the crossing pair |
| Type III | `slide` | Three edges in the move's required local pattern |

For example, `poke` places the first selected edge under the second and adds
two crossings:

```python
trefoil = cl.knot(3, 1)
poked = cl.poke(trefoil, under_edge=1, over_edge=4)

assert poked.is_valid()
assert len(poked.pd_code) == len(trefoil.pd_code) + 2
```

The selected edges must form a supported local configuration. Inserting a
poke between edges in separate projection components is supported by the
library's exterior-face convention; within one projection component, they
must border a common face. If a move cannot be applied, the operation raises
`ReidemeisterError`.

`untwist`, `unpoke`, and `slide` likewise require a compatible local pattern.
An edge number alone does not guarantee that a removal or slide is possible.

## Discover candidate moves

Candidate functions return arguments that can be passed to their matching
operation:

| Candidate function | Return values | Matching operation |
| --- | --- | --- |
| `get_twistables(diagram)` | Individual edge labels | One of the four Type I insertion functions |
| `get_untwistables(diagram)` | Individual edge labels | `untwist` |
| `get_pokables(diagram)` | Ordered `(under_edge, over_edge)` pairs | `poke` |
| `get_unpokables(diagram)` | `(edge1, edge2)` pairs | `unpoke` |
| `get_slidables(diagram)` | `(edge1, edge2, edge3)` triples | `slide` |

These functions inspect the current diagram; they do not apply moves. A
candidate list may be empty. Recompute it after changing a diagram, because
operations can add, remove, or relabel edges.

```python
trefoil = cl.knot(3, 1)
poked = cl.poke(trefoil, under_edge=1, over_edge=4)

remove_candidates = cl.get_unpokables(poked)
recovered = cl.unpoke(poked, *remove_candidates[0])

assert recovered == trefoil
```

`get_twistables()` returns all edge labels because a Type I twist can be
inserted along any edge. The other candidate functions search for the local
patterns required by their corresponding operation.

## Work with move objects

For generic enumeration, use the `Move` dataclass and `MoveKind` enum.
`get_moves(diagram)` returns the legal one-step moves, `apply_move()` applies
one move object, and `transitions()` yields `(Move, resulting_diagram)` pairs:

```python
moves = cl.get_moves(trefoil)

if moves:
    first_result = cl.apply_move(trefoil, moves[0])

for move, next_diagram in cl.transitions(trefoil):
    assert next_diagram.is_valid()
```

A `Move` stores its kind and ordered edge arguments. Poke, unpoke, and slide
require two, two, and three distinct edge labels respectively. For example:

```python
move = cl.Move(cl.MoveKind.POKE, (1, 4))
changed = cl.apply_move(trefoil, move)
```

The `MoveKind` values are
`LEFT_POSITIVE_TWIST`, `LEFT_NEGATIVE_TWIST`,
`RIGHT_POSITIVE_TWIST`, `RIGHT_NEGATIVE_TWIST`, `UNTWIST`, `POKE`, `UNPOKE`,
and `SLIDE`.

## Combine diagrams

`disjoint_union(first, *others)` combines diagrams without joining their
components. `join(first, second, self_edge, other_edge)` joins the components
containing the selected edges, one from each input. A successful join reduces
the total number of components by one.

`connected_sum(first, *others)` repeatedly forms connected sums of
single-component diagrams (knots); it rejects link diagrams with more than
one component:

```python
trefoil = cl.knot(3, 1)
figure_eight = cl.knot(4, 1)

union = cl.disjoint_union(trefoil, figure_eight)
joined = cl.join(trefoil, figure_eight, self_edge=1, other_edge=1)
sum_diagram = cl.connected_sum(trefoil, figure_eight)

assert union.n_components == 2
assert joined.n_components == 1
assert sum_diagram.n_components == 1
```

`join` raises `ValueError` if either diagram is invalid, an edge is not in its
diagram, or the selected components cannot be joined as oriented cycles.
`connected_sum` raises `ValueError` for invalid inputs or inputs with more
than one component.

## Related pages

- [Diagrams and construction](diagrams.md)
- [Properties and notation](properties.md)
- [Development and testing](development.md)

