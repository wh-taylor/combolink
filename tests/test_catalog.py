import os
from pathlib import Path
import subprocess
import sys

from combolink.catalog import first_n_knots


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
