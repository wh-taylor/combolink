import os
from pathlib import Path
import subprocess
import sys

import pytest

from combolink import torus_knot
from combolink.catalog import first_n_knots, knot


def test_catalog_loads_outside_repository_directory(tmp_path):
    repository_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repository_root), env.get("PYTHONPATH", "")]
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            "from combolink.catalog import knot; assert knot(3, 1)",
        ],
        cwd=tmp_path,
        env=env,
        check=True,
    )


def test_first_n_knots_returns_repeatable_list():
    first = first_n_knots(3)
    second = first_n_knots(3)

    assert isinstance(first, list)
    assert [name for name, _ in first] == ["0_1", "3_1", "4_1"]
    assert [name for name, _ in second] == ["0_1", "3_1", "4_1"]


def test_torus_knot_generates_standard_knot_diagrams():
    trefoil = torus_knot(2, 3)
    five_torus = torus_knot(3, 5)

    assert trefoil == knot(3, 1)
    assert torus_knot(3, 2) == trefoil
    assert len(five_torus.pd_code) == 10
    for diagram in (trefoil, five_torus):
        assert diagram.is_valid()
        assert diagram.n_components == 1
        for edge in range(1, 2 * len(diagram.pd_code) + 1):
            diagram._get_forth_index(edge)


def test_torus_knot_generates_the_unknot_when_parameter_is_one():
    assert torus_knot(1, 5).n_components == 1
    assert torus_knot(5, 1).n_components == 1


def test_torus_knot_requires_positive_coprime_integers():
    with pytest.raises(ValueError, match="positive integers"):
        torus_knot(0, 3)
    with pytest.raises(ValueError, match="coprime"):
        torus_knot(2, 4)
