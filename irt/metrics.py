"""Metricas de rede, resiliencia e deteccao (equacoes do artigo)."""

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from .config import BETA_INFLUENCE, EPS, W_CONFIDENCE, W_HISTORY, W_LEARNING


# ----------------------------------------------------------------------
# Qualidade de rede
# ----------------------------------------------------------------------

def quality_index(G):
    """QI = 0.5*C + 0.3*Eprop + 0.2*D.

    C     : fracao de nos no maior componente conexo (Cmax)
    Eprop : eficiencia de propagacao (Eq. 16), media de 1/d(u,v) em Cmax
    D     : entrega, soma de quality*capacity das arestas de Cmax / (10*|E|)
    """
    comps = list(nx.connected_components(G))
    if not comps:
        return 0.0, {"connectivity_frac": 0, "prop_eff": 0, "delivery_ratio": 0}
    giant = max(comps, key=len)
    c = len(giant) / G.number_of_nodes()
    H = G.subgraph(giant).copy()
    if H.number_of_nodes() <= 1:
        return 0.5 * c, {"connectivity_frac": c, "prop_eff": 0, "delivery_ratio": 0}
    lengths = dict(nx.all_pairs_shortest_path_length(H))
    invs = [1 / d for u in H.nodes for v in H.nodes if u != v for d in [lengths[u].get(v)] if d and d > 0]
    p = float(np.mean(invs)) if invs else 0.0
    E = [(u, v) for u, v in G.edges if u in giant and v in giant]
    d_vals = [G.edges[u, v]["quality"] * G.edges[u, v]["capacity"] for u, v in E]
    d = float(np.sum(d_vals) / (10.0 * len(E))) if E else 0.0
    qi_composite = 0.5 * c + 0.3 * p + 0.2 * d
    return qi_composite, {"connectivity_frac": c, "prop_eff": p, "delivery_ratio": d}


def global_efficiency(G):
    """Eficiencia global (Eq. 16 estendida a TODO V): media de 1/d(u,v) sobre
    todos os pares de V, com pares desconectados (inclusive nos mortos)
    contribuindo 0. Diferente do Eprop (restrito a Cmax), penaliza explicitamente
    a fragmentacao e o colapso, sendo comparavel entre cenarios."""
    n = G.number_of_nodes()
    if n <= 1:
        return 0.0
    total = 0.0
    for u, dists in nx.all_pairs_shortest_path_length(G):
        for v, d in dists.items():
            if v != u and d > 0:
                total += 1.0 / d
    return float(total / (n * (n - 1)))


# ----------------------------------------------------------------------
# Resiliencia
# ----------------------------------------------------------------------

def adaptive_resilience_factor(qi_before, qi_failure, qi_after):
    """Eq. (6) ARF = (QIafter - QIfailure) / (QIbefore - QIfailure + eps)."""
    return float((qi_after - qi_failure) / (qi_before - qi_failure + EPS))


def resilience_activation_coeff(G):
    """Eq. (7) rho(i,j) = beta_ij * reliability(i,j) * adaptation_potential(i,j),
    agregado como media sobre as arestas ativas."""
    if G.number_of_edges() == 0:
        return 0.0
    vals = [
        BETA_INFLUENCE * G.edges[u, v]["quality"] * (G.edges[u, v]["capacity"] / 10.0)
        for u, v in G.edges
    ]
    return float(np.mean(vals))


def topology_intuition_index(G, dl, score_map=None, knowledge=None, cycle_id=None):
    """Eq. (5) TII(T) = (1/|V|) * sum_i w_i * phi_i(t).

    w_i   : peso de relevancia (criticidade do no) = grau relativo ao grau MEDIO.
            Com essa normalizacao (1/|V|)*sum_i w_i = 1, logo TII in [0,1] e o
            teto independe da distribuicao de grau -> comparavel entre topologias.
    phi_i : escore de antecipacao, combinando as tres fontes da Definicao 2:
              (a) estado de aprendizado do agente  -> 1 - L_i (vigilancia acumulada;
                  L_i e' saude/confianca, e 1-L_i e' a leitura de ameaca, coerente
                  com threat_probability = 1 - mean(L))
              (b) confianca de deteccao            -> recall intuitivo do Rintuitive
              (c) historico recente de desfecho    -> media movel do ganho de QI
    `cycle_id` e' mantido na assinatura por compatibilidade (nao e' usado).
    """
    if dl is None:
        return None
    n = G.number_of_nodes()
    if n == 0:
        return 0.0

    deg = dict(G.degree())
    mean_deg = float(np.mean(list(deg.values()))) if deg else 0.0
    if mean_deg <= 0:
        return 0.0

    # (c) historico recente: ganho medio de QI nos ultimos ciclos, normalizado
    hist_score = 0.0
    if knowledge is not None and knowledge.historical:
        recentes = sorted(knowledge.historical.keys())[-5:]
        deltas = [knowledge.historical[c]["qi_delta"] for c in recentes]
        if deltas:
            hist_score = float(np.clip(np.mean(deltas) / 0.2, 0.0, 1.0))

    total = 0.0
    for v in G.nodes:
        if not G.nodes[v].get("alive", True):
            continue
        w_i = deg.get(v, 0) / mean_deg
        a = 1.0 - float(dl.L.get(v, 0.0))
        b = float(score_map.get(v, 0.0)) if score_map else 0.0
        phi_i = W_LEARNING * a + W_CONFIDENCE * b + W_HISTORY * hist_score
        total += w_i * float(np.clip(phi_i, 0.0, 1.0))
    return float(total / n)


# ----------------------------------------------------------------------
# Deteccao
# ----------------------------------------------------------------------

def compute_confusion(universe, ground_truth, anomalies):
    """Matriz de confusao e metricas derivadas sobre `universe` (todos os nos)."""
    y_true = [1 if v in ground_truth else 0 for v in universe]
    y_pred = [1 if v in anomalies else 0 for v in universe]
    tp = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 0)
    tn = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 0)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    return tp, fp, fn, tn, precision, recall, f1, accuracy


def roc_auc(alive, ground_truth, score_map):
    """Eq. (14) ROC AUC sobre os escores de confianca do Rintuitive.
    NaN quando nao ha ambas as classes (ex.: cenario sem ataque)."""
    if not alive:
        return np.nan
    y_true = [1 if v in ground_truth else 0 for v in alive]
    if len(set(y_true)) < 2:
        return np.nan
    y_score = [score_map.get(v, 0.0) for v in alive]
    try:
        return float(roc_auc_score(y_true, y_score))
    except ValueError:
        return np.nan


# ----------------------------------------------------------------------
# Estatistica
# ----------------------------------------------------------------------

def ci95(series):
    """Meia-largura do IC 95% (aprox. normal): 1.96 * s / sqrt(n)."""
    series = pd.Series(series).dropna()
    if len(series) <= 1:
        return 0.0
    return 1.96 * series.std(ddof=1) / np.sqrt(len(series))
