# Development and Testing

This page describes the supported local workflow for running the project
tests from a source checkout.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) for the checked-in development environment

ComboLink has no external runtime dependencies. The `dev` optional dependency
group includes pytest.

## Install for development

From the repository root, synchronize the project and its development
dependencies using the lockfile:

```bash
uv sync --locked --extra dev --inexact
```

`--locked` asks uv to use the current lockfile without updating it.
`--inexact` allows the environment to retain packages that are not declared
by the project, which can be useful in an existing development environment.

## Run tests

Run the complete test suite with:

```bash
uv run --locked --extra dev python -m pytest -q
```

To run one test module or a focused test, pass pytest's normal path and
selection arguments:

```bash
uv run --locked --extra dev python -m pytest -q tests/test_graph.py
uv run --locked --extra dev python -m pytest -q tests/test_graph.py -k encodes
```

## Before submitting documentation changes

- Check that Markdown links point to files that exist.
- Run code examples against the current package when practical.
- Keep user-facing descriptions consistent with the exported API in
  [`combolink/__init__.py`](../combolink/__init__.py).

## Related pages

- [Documentation hub](guide.md)
- [Project overview](../README.md)

