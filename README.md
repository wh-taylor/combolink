# Combolink

Manipulate and analyze knot and link diagrams.

This library requires Python 3.12 or newer and is currently unstable.

## Installation

Install from a source checkout with:

```shell
python -m pip install .
```

Or install directly from Git:

```shell
python -m pip install git+https://github.com/wh-taylor/unknotter.git
```

For example:

```python
import combolink as cl

trefoil = cl.knot(3, 1)
```
