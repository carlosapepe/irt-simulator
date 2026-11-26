"""Teste de reprodutibilidade.

`reference_small.csv` foi gerado pelo script monolitico original
(2 runs x 4 ciclos x 3 topologias x 3 cenarios). A versao modular deve
produzir exatamente os mesmos numeros. Rode com:

    python -m pytest tests/
"""

from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from irt import config
from irt.experiment import run_experiments

REF = Path(__file__).with_name("reference_small.csv")


def _run_small():
    seeds = config.make_seeds(2)
    rows = []
    for cfg in config.CONFIGS:
        rows += run_experiments(cfg, seeds=seeds, n_cycles=4)
    return pd.DataFrame(rows)


def test_matches_reference():
    got = _run_small()
    ref = pd.read_csv(REF)
    # passa pelo mesmo caminho de serializacao CSV da referencia
    got = pd.read_csv(pd.io.common.StringIO(got.to_csv(index=False)))
    assert_frame_equal(got, ref, check_exact=False, rtol=1e-12, atol=1e-12)


def test_deterministic():
    a = _run_small()
    b = _run_small()
    assert_frame_equal(a, b)
