# ComboLink Documentation

ComboLink is a Python library for constructing, analyzing, and transforming
oriented knot and link diagrams. This documentation is organized as a set of
focused pages so you can start with a short example and then explore the
details you need.

ComboLink requires Python 3.12 or newer and has no external runtime
dependencies. It is pre-1.0, so its public API may change.

## Start here

Install the latest version from GitHub:

```bash
python -m pip install git+https://github.com/wh-taylor/combolink.git
```

Then create a diagram and inspect a few properties:

```python
import combolink as cl

trefoil = cl.knot(3, 1)

print(trefoil.pd_code)
print("components:", trefoil.n_components)
print("writhe:", cl.get_writhe(trefoil))
print("Jones polynomial:", cl.jones(trefoil).var("t"))
```

## Documentation pages

| Page | What it covers |
| --- | --- |
| [Diagrams and construction](diagrams.md) | PD-code conventions, structural validity, components, catalog knots, torus links, and custom inputs. |
| [Diagram operations](operations.md) | Reflection, orientation reversal, Reidemeister moves, candidate discovery, and diagram combinations. |
| [Properties and notation](properties.md) | Writhe, Laurent polynomials, Kauffman bracket, Jones polynomial, Gauss codes, DT notation, and compact PD text. |
| [Working with polynomials](polynomials.md) | Construct, format, evaluate, compare, and combine `Polynomial` objects. |
| [Combinatorial graph model](graph-model.md) | The six-tuple compiled by `to_graph`, face-boundary cycles, spherical planarity, round-tripping, and ML adapters. |
| [Development and testing](development.md) | Editable installation, tests, and contributor-oriented checks. |

## Project links

- [Project overview and quick start](../README.md)
- [Public package exports](../combolink/__init__.py)
- [MIT License](../LICENSE)

