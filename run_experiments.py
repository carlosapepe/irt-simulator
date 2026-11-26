"""Ponto de entrada: reproduz o experimento completo do IRT.

Uso:
    python run_experiments.py                    # experimento do artigo (35 runs x 35 ciclos)
    python run_experiments.py --runs 3 --cycles 5   # execucao rapida de teste

Artefatos gerados em --outdir (padrao: results/):
    resultados_modelo_irt.csv   uma linha por (cenario, topologia, run)
    relatorio_comparativo.txt   tabelas comparativas impressas no terminal
    metadados_execucao.json     parametros, versoes e tempo de execucao
"""

import argparse
import json
import platform
import time
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import sklearn

from irt import __version__, config
from irt.experiment import run_experiments
from irt.report import build_report


def parse_args():
    ap = argparse.ArgumentParser(description="Experimento IRT (Intuitive Resilient Topologies)")
    ap.add_argument("--runs", type=int, default=config.N_RUNS, help=f"runs por topologia/cenario (padrao {config.N_RUNS})")
    ap.add_argument("--cycles", type=int, default=config.N_CYCLES, help=f"ciclos por run (padrao {config.N_CYCLES})")
    ap.add_argument("--nodes", type=int, default=config.N_NODES, help=f"nos por grafo (padrao {config.N_NODES})")
    ap.add_argument("--outdir", default="results", help="pasta de saida (padrao results/)")
    return ap.parse_args()


def main():
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    seeds = config.make_seeds(args.runs)
    configs = config.CONFIGS
    n_lines = args.runs * len(config.TOPO_DEFS) * len(configs)
    print(f"Experimento (modelo IRT): {args.runs} runs x {len(config.TOPO_DEFS)} topologias x "
          f"{len(configs)} cenarios = {n_lines} linhas\n")

    t0 = time.time()
    all_rows = []
    for cfg in configs:
        print(f"  Executando cenario: {cfg['label']}...")
        rows = run_experiments(cfg, seeds=seeds, n_cycles=args.cycles, n_nodes=args.nodes)
        all_rows.extend(rows)
        print(f"  OK: {len(rows)} linhas prontas.\n")
    elapsed = time.time() - t0

    df = pd.DataFrame(all_rows)
    csv_path = outdir / "resultados_modelo_irt.csv"
    df.to_csv(csv_path, index=False)

    report = build_report(df)
    (outdir / "relatorio_comparativo.txt").write_text(report + "\n", encoding="utf-8")

    meta = {
        "irt_version": __version__,
        "runs": args.runs,
        "cycles": args.cycles,
        "nodes": args.nodes,
        "seeds": seeds,
        "topologies": [t for t, _ in config.TOPO_DEFS],
        "scenarios": configs,
        "attack_config": config.ATTACK_CONFIG,
        "elapsed_s": round(elapsed, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "libs": {"networkx": nx.__version__, "numpy": np.__version__,
                 "pandas": pd.__version__, "scikit-learn": sklearn.__version__},
    }
    (outdir / "metadados_execucao.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Concluido em {elapsed:.1f}s | artefatos em: {outdir}/\n")
    print(report)


if __name__ == "__main__":
    main()
