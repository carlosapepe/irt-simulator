"""Aprendizado distribuido: cada no mantem um estado L_i in [0, 1]
(saude/confianca) influenciado pelos vizinhos e por estimulos locais."""

import numpy as np

from .config import ALPHA_LEARN, BETA_INFLUENCE


class DistributedLearning:
    """Avaliacao de ameaca via estado local dos nos.

    L_i(t+1) = clip(L_i + alpha * [ sum_j beta*(L_j - L_i) + s_i ], 0, 1)
    s_i = -0.04 se a EMA media de latencia dos vizinhos > 80 ms ou i foi
          detectado como anomalo; caso contrario +0.01.
    """

    def __init__(self, G):
        self.alpha = ALPHA_LEARN
        self.beta = BETA_INFLUENCE
        self.L = {v: G.nodes[v].get("energy", 0.9) for v in G.nodes}

    def step(self, G, detected_anomalies):
        delta = {}
        for i in G.nodes:
            if not G.nodes[i].get("alive", True):
                delta[i] = 0.0
                continue
            nbrs = [j for j in G.neighbors(i) if G.nodes[j].get("alive", True)]
            infl = sum(self.beta * (self.L.get(j, 0.5) - self.L.get(i, 0.5)) for j in nbrs)
            avg_nbr_ema_latency = np.mean([G.nodes[j]["ema_latency"] for j in nbrs]) if nbrs else 200.0
            stimulus = -0.04 if (avg_nbr_ema_latency > 80.0 or i in detected_anomalies) else 0.01
            delta[i] = infl + stimulus
        self.L = {i: float(np.clip(self.L.get(i, 0.5) + self.alpha * delta.get(i, 0.0), 0.0, 1.0)) for i in G.nodes}

    def threat_probability(self, G, leaders):
        """p_threat = 1 - media(L) dos lideres vivos (1.0 se nao houver lider vivo)."""
        alive = [v for v in leaders if v in G.nodes and G.nodes[v].get("alive", True)]
        if not alive:
            return 1.0
        return float(np.clip(1.0 - np.mean([self.L.get(v, 0.5) for v in alive]), 0.0, 1.0))

    def network_learning_mean(self):
        return float(np.mean(list(self.L.values()))) if self.L else 0.0
