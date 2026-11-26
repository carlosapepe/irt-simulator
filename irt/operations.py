"""Fases operacionais de cada ciclo: formacao, eleicao, autenticacao e
operacao normal (evolucao estocastica do estado dos nos)."""

import numpy as np


def formation_phase(G):
    """Formacao: cada no troca entre 3 e 9 mensagens HELLO (contador emulado)."""
    for v in G.nodes:
        G.nodes[v]["hello_count"] = np.random.randint(3, 10)


def elect_leaders(G):
    """Elege lider e vice (deputy) como os dois nos vivos de maior grau."""
    alive_nodes = [v for v in G.nodes if G.nodes[v].get("alive", True)]
    if len(alive_nodes) < 2:
        return alive_nodes[0] if alive_nodes else None, None
    ordered = sorted([(v, G.degree(v)) for v in alive_nodes], key=lambda x: x[1], reverse=True)
    leader, deputy = ordered[0][0], ordered[1][0]
    for v in G.nodes:
        G.nodes[v]["role"] = "member"
    G.nodes[leader]["role"] = "leader"
    G.nodes[deputy]["role"] = "deputy"
    return leader, deputy


def authenticate_leaders(G, leader, deputy):
    """Autentica lider/vice se energia > 0.3 e latencia < 100 ms."""
    if leader is None or deputy is None:
        return False
    ok_l = G.nodes[leader]["energy"] > 0.3 and G.nodes[leader]["latency"] < 100
    ok_d = G.nodes[deputy]["energy"] > 0.3 and G.nodes[deputy]["latency"] < 100
    G.nodes[leader]["authenticated"] = bool(ok_l)
    G.nodes[deputy]["authenticated"] = bool(ok_d)
    return bool(ok_l and ok_d)


def operation_step(G):
    """Operacao normal: fator de carga lf ~ N(1, 0.05) recortado em [0.8, 1.2]
    multiplica trafego, taxa de pacotes e latencia; atualiza a EMA de latencia
    (alpha = 0.35) e drena energia (0.002 * lf por ciclo)."""
    alpha_ema = 0.35
    for v in G.nodes:
        if not G.nodes[v].get("alive", True):
            continue
        lf = np.clip(np.random.normal(1.0, 0.05), 0.8, 1.2)
        G.nodes[v]["traffic"] = np.clip(G.nodes[v]["traffic"] * lf, 0.05, 5.0)
        G.nodes[v]["packet_rate"] = np.clip(G.nodes[v]["packet_rate"] * lf, 0.5, 200)
        G.nodes[v]["latency"] = np.clip(G.nodes[v]["latency"] * lf, 2, 200)
        current_ema = G.nodes[v].get("ema_latency", G.nodes[v]["latency"])
        G.nodes[v]["ema_latency"] = alpha_ema * G.nodes[v]["latency"] + (1 - alpha_ema) * current_ema
        G.nodes[v]["energy"] = max(0.0, G.nodes[v]["energy"] - 0.002 * lf)
