"""Injecao de falhas e ataques (falha de no, falha de enlace, DoS).

Devolve o ground truth do ciclo: o conjunto de nos vivos sob DoS, usado
para calcular precisao/recall/F1/ROC-AUC da deteccao.
"""

import random

import numpy as np

from .config import ATTACK_CONFIG


def inject_failures_and_attacks(G, leader, config=ATTACK_CONFIG):
    alive_nodes = [v for v in G.nodes if G.nodes[v].get("alive", True)]

    # 1) Falha de no: o no morre e perde todas as arestas
    for v in random.sample(alive_nodes, min(config["num_node_failures"], len(alive_nodes))):
        G.nodes[v]["alive"] = False
        G.nodes[v]["under_attack"] = False
        G.nodes[v]["traffic"] = 0.0
        for nbr in list(G.neighbors(v)):
            if G.has_edge(v, nbr):
                G.remove_edge(v, nbr)

    # 2) Falha de enlace: remove arestas ao acaso
    for _ in range(config["num_link_failures"]):
        if G.number_of_edges() == 0:
            break
        G.remove_edge(*random.choice(list(G.edges)))

    # 3) DoS: marca novos nos e (opcionalmente) o lider
    candidates = [v for v in G.nodes if G.nodes[v].get("alive", True) and not G.nodes[v].get("under_attack", False)]
    for v in random.sample(candidates, min(config["num_dos_nodes"], len(candidates))):
        G.nodes[v]["under_attack"] = True
    if config.get("attack_leader") and leader in G.nodes and G.nodes[leader].get("alive", True):
        G.nodes[leader]["under_attack"] = True

    # Assinatura do DoS: trafego U(1.5, 7.0) e latencia U(28, 90) ms
    # (reaplicada a todo no ainda sob ataque, inclusive de ciclos anteriores)
    for v in G.nodes:
        if G.nodes[v].get("alive", True) and G.nodes[v].get("under_attack", False):
            G.nodes[v]["traffic"] = float(np.clip(np.random.uniform(1.5, 7.0), 1.0, 7.0))
            G.nodes[v]["latency"] = float(np.clip(np.random.uniform(28.0, 90.0), 28.0, 90.0))

    gt = set(v for v in G.nodes if G.nodes[v].get("alive", True) and G.nodes[v].get("under_attack", False))
    return gt
