"""Geracao das topologias e dos dados emulados de nos e enlaces.

Nenhum dado real e' carregado: todos os atributos sao sinteticos, sorteados
de distribuicoes uniformes (ver docs/DADOS_EMULADOS.md).
"""

import random

import networkx as nx
import numpy as np

from .config import BA_M, ER_P, N_NODES, RANDOM_SEED, WS_K, WS_P


def build_topology(kind="ER", n=N_NODES, seed=RANDOM_SEED):
    """Cria um grafo ER, WS ou BA, garante conectividade e emula atributos.

    Atributos de no (estado inicial):
        traffic      U(0.1, 1.0)   carga normalizada
        packet_rate  U(1, 50)      pacotes/s
        latency      U(5, 25)      ms
        ema_latency  = latency     media movel exponencial da latencia
        energy       U(0.8, 1.0)   bateria/energia normalizada
        role         "member"      | "leader" | "deputy"
        authenticated, alive, under_attack  (booleanos)

    Atributos de aresta:
        quality      U(0.7, 1.0)   confiabilidade do enlace
        capacity     U(1.0, 10.0)  capacidade (unidade arbitraria)
    """
    if kind == "ER":
        G = nx.gnp_random_graph(n, ER_P, seed=seed)
    elif kind == "WS":
        G = nx.watts_strogatz_graph(n, WS_K, WS_P, seed=seed)
    elif kind == "BA":
        G = nx.barabasi_albert_graph(n, BA_M, seed=seed)
    else:
        raise ValueError(kind)

    # Liga componentes desconexos em cadeia (uma aresta entre componentes vizinhos)
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            G.add_edge(
                random.choice(list(comps[i])),
                random.choice(list(comps[i + 1])),
            )

    for v in G.nodes:
        latency_init = np.random.uniform(5, 25)
        G.nodes[v].update({
            "traffic": np.random.uniform(0.1, 1.0),
            "packet_rate": np.random.uniform(1, 50),
            "latency": latency_init,
            "ema_latency": latency_init,
            "energy": np.random.uniform(0.8, 1.0),
            "role": "member",
            "authenticated": False,
            "alive": True,
            "under_attack": False,
        })

    for u, v in G.edges:
        G.edges[u, v]["quality"] = np.random.uniform(0.7, 1.0)
        G.edges[u, v]["capacity"] = np.random.uniform(1.0, 10.0)

    return G
