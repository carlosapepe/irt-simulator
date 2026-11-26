"""Pipeline de experimentos: topologia x run x ciclo, agregado por run."""

import random

import numpy as np

from .config import N_CYCLES, N_NODES, SEEDS, TOPO_DEFS
from .cycle import single_cycle
from .dual_system import DualSystemResponse
from .knowledge import KnowledgeNetworks
from .learning import DistributedLearning
from .topology import build_topology


def run_experiments(config, seeds=SEEDS, n_cycles=N_CYCLES, n_nodes=N_NODES, topo_defs=TOPO_DEFS):
    """Executa um cenario em todas as topologias e sementes.

    Devolve uma lista de dicionarios, uma linha por (topologia, run), com as
    metricas medias dos `n_cycles` ciclos (ver docs/ARTEFATOS.md).
    """
    rows = []
    for topo_name, topo_kind in topo_defs:
        for run_id, seed in enumerate(seeds, start=1):
            np.random.seed(seed)
            random.seed(seed)
            G = build_topology(topo_kind, n_nodes, seed=seed)

            if config.get("use_intuitive"):
                knowledge = KnowledgeNetworks()
                dl = DistributedLearning(G)
                dual = DualSystemResponse()
            else:
                knowledge = dl = dual = None

            results = []
            for c in range(1, n_cycles + 1):
                results.append(single_cycle(G, config, c, knowledge=knowledge, dl=dl, dual=dual))

            def _mean(key, attack_only=False):
                if attack_only and not config.get("inject_attacks"):
                    return np.nan
                vals = [r[key] for r in results if r[key] is not None and not (isinstance(r[key], float) and np.isnan(r[key]))]
                return float(np.mean(vals)) if vals else np.nan

            sys_list = [r["system"] for r in results]
            rew_list = [r["reward"] for r in results]
            rew_s1 = [rw for s, rw in zip(sys_list, rew_list) if s == "S1"]
            rew_s2 = [rw for s, rw in zip(sys_list, rew_list) if s == "S2"]

            rows.append({
                "run_id": run_id, "seed": seed, "config": config["label"], "topology": topo_name,
                "qi_mean": _mean("qi"),
                "tii_mean": _mean("tii"),
                "arf_mean": _mean("arf", attack_only=True),
                "rho_mean": _mean("rho"),
                "prop_eff_mean": _mean("prop_eff"),
                "eprop_global_mean": _mean("eprop_global"),
                "roc_auc_mean": _mean("roc_auc", attack_only=True),
                "qi_before_mean": _mean("qi_before"),
                "qi_failure_mean": _mean("qi_failure"),
                "connectivity_mean": _mean("connectivity"),
                "delivery_mean": _mean("delivery"),
                "precision_mean": _mean("precision", attack_only=True),
                "recall_mean": _mean("recall", attack_only=True),
                "f1_mean": _mean("f1", attack_only=True),
                "accuracy_mean": _mean("accuracy", attack_only=True),
                "tp_sum": np.sum([r["tp"] for r in results]),
                "fp_sum": np.sum([r["fp"] for r in results]),
                "fn_sum": np.sum([r["fn"] for r in results]),
                "tn_sum": np.sum([r["tn"] for r in results]),
                "n_s1": len(rew_s1),
                "n_s2": len(rew_s2),
                "reward_s1_mean": float(np.mean(rew_s1)) if rew_s1 else np.nan,
                "reward_s2_mean": float(np.mean(rew_s2)) if rew_s2 else np.nan,
            })
    return rows
