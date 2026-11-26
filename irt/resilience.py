"""Acoes de resiliencia: mitigacao de suspeitos, reintegracao de nos,
promocao do vice-lider e reforco/religacao da malha."""

import random

import networkx as nx
import numpy as np


def reconnect_components(G, max_edges=2):
    """Liga ate `max_edges` componentes vivos isolados ao componente principal."""
    alive_comps = []
    for c in nx.connected_components(G):
        alive_nodes = [v for v in c if G.nodes[v].get("alive", True)]
        if alive_nodes:
            alive_comps.append(alive_nodes)
    if len(alive_comps) <= 1:
        return 0
    alive_comps.sort(key=len, reverse=True)
    main = list(alive_comps[0])
    added = 0
    for comp in alive_comps[1:]:
        if added >= max_edges:
            break
        u = random.choice(main)
        v = random.choice(comp)
        if not G.has_edge(u, v):
            G.add_edge(u, v, quality=np.random.uniform(0.7, 1.0), capacity=np.random.uniform(1.0, 10.0))
            main.append(v)
            added += 1
    return added


def reinforce_largest_component(G, max_edges):
    """Adiciona ate `max_edges` arestas novas (aleatorias) dentro do Cmax."""
    if max_edges <= 0 or G.number_of_nodes() <= 1:
        return 0
    comp = max(nx.connected_components(G), key=len)
    sub = G.subgraph(comp)
    pairs = list(nx.non_edges(sub))
    if not pairs:
        return 0
    random.shuffle(pairs)
    added = 0
    for u, v in pairs:
        if added >= max_edges:
            break
        G.add_edge(u, v, quality=np.random.uniform(0.7, 1.0), capacity=np.random.uniform(1.0, 10.0))
        added += 1
    return added


def mitigate_suspects(G, anomalies, max_mitigate=5):
    """Restaura trafego/latencia normais de ate `max_mitigate` nos suspeitos
    e encerra o DoS neles (under_attack = False)."""
    if max_mitigate <= 0:
        return 0
    mitigated = 0
    for v in anomalies:
        if mitigated >= max_mitigate:
            break
        if v not in G.nodes or not G.nodes[v].get("alive", True):
            continue
        G.nodes[v]["traffic"] = float(np.clip(np.random.uniform(0.1, 1.0), 0.05, 5.0))
        G.nodes[v]["latency"] = float(np.clip(np.random.uniform(5, 25), 2, 200))
        G.nodes[v]["ema_latency"] = G.nodes[v]["latency"]
        G.nodes[v]["under_attack"] = False
        mitigated += 1
    return mitigated


def reform_nodes(G, max_reform=2):
    """Reintegra ate `max_reform` nos mortos com estado inicial novo,
    ligando cada um a ate 2 nos do maior componente."""
    dead = [v for v in G.nodes if not G.nodes[v].get("alive", True)]
    if not dead or max_reform <= 0:
        return 0
    if G.number_of_edges() > 0:
        giant = list(max(nx.connected_components(G), key=len))
    else:
        giant = [v for v in G.nodes if G.nodes[v].get("alive", True)]
    reformed = 0
    for v in random.sample(dead, min(max_reform, len(dead))):
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
        for t in (random.sample(giant, min(2, len(giant))) if giant else []):
            if t != v and not G.has_edge(v, t):
                G.add_edge(v, t, quality=np.random.uniform(0.7, 1.0), capacity=np.random.uniform(1.0, 10.0))
        reformed += 1
    return reformed


def apply_resilience(G, leader, deputy, action, anomalies, config):
    """Aplica, nesta ordem: mitigacao -> reintegracao -> promocao do vice ->
    religacao de componentes -> reforco da malha (se a acao pedir)."""
    if config.get("mitigate_anomalies") and anomalies:
        mitigate_suspects(G, anomalies, max_mitigate=config.get("max_mitigate_per_cycle", 5))
    if config.get("reform_nodes", 0) > 0:
        reform_nodes(G, max_reform=config.get("reform_nodes", 0))
    if config.get("promote_deputy") and ("PROMOTE" in action or leader not in G.nodes or not G.nodes[leader].get("alive", True)):
        if deputy in G.nodes and G.nodes[deputy].get("alive", True):
            for v in G.nodes:
                if G.nodes[v]["role"] == "leader":
                    G.nodes[v]["role"] = "member"
            G.nodes[deputy]["role"] = "leader"
            leader = deputy
            alive_candidates = [(cand, G.degree(cand)) for cand in G.nodes if cand != leader and G.nodes[cand].get("alive", True)]
            for cand, _ in sorted(alive_candidates, key=lambda x: x[1], reverse=True):
                G.nodes[cand]["role"] = "deputy"
                deputy = cand
                break
    if config.get("add_mesh_edges", 0) > 0:
        budget = config.get("add_mesh_edges", 0)
        added = reconnect_components(G, max_edges=config.get("max_reconnect_edges", 2))
        if "REINFORCE" in action or "REWIRE" in action:
            reinforce_largest_component(G, max_edges=max(0, budget - added))
    return leader, deputy
