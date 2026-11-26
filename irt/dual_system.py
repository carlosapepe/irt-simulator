"""Mecanismo de decisao dual: System 1 (intuitivo, rapido) vs
System 2 (deliberativo, Q-learning com exploracao epsilon-greedy)."""

import random

import numpy as np

from .config import ALPHA_Q, GAMMA_Q, THRESHOLD_S1, THRESHOLD_S2


class DualSystemResponse:
    # Acao do Dual System -> acao de resiliencia executada
    _MAP = {
        "REINFORCE_LEADER_MESH": "REINFORCE_MESH",
        "ISOLATE_ANOMALOUS": "ISOLATE_SUSPECTS_AND_REWIRE",
        "REPAIR_EDGE_QUALITY": "REINFORCE_MESH",
        "REPAIR_AP_LINKS": "PROMOTE_DEPUTY_AND_REWIRE",
        "DO_NOTHING": "OK",
    }
    _DA = list(_MAP.keys())

    def __init__(self):
        self.Q = {
            "REINFORCE_LEADER_MESH": 0.05,
            "REPAIR_EDGE_QUALITY": 0.03,
            "ISOLATE_ANOMALOUS": 0.02,
            "REPAIR_AP_LINKS": 0.01,
            "DO_NOTHING": -0.05,
        }
        self.epsilon = 0.05
        self.eps_min = 0.01
        self.eps_decay = 0.98
        self.threat_history = []

    def current_threshold(self):
        """Limiar adaptativo theta: quantil 75% do historico de p_threat,
        recortado em [0.05, 0.40]; THRESHOLD_S1 nos 3 primeiros ciclos."""
        if len(self.threat_history) < 3:
            return THRESHOLD_S1
        q = float(np.quantile(self.threat_history, 0.75))
        return float(np.clip(q, 0.05, 0.40))

    def update_threshold(self, p_threat):
        self.threat_history.append(float(p_threat))

    def system1(self, knowledge, qi, p_threat, anomalous):
        """Resposta intuitiva: melhor acao memorizada no bucket; senao regras rapidas."""
        bucket = knowledge.discretize(qi, p_threat)
        best = knowledge.best_intuitive_action(bucket)
        if best and best != "ISOLATE_ANOMALOUS":
            return best
        if qi < 0.40:
            return "REPAIR_EDGE_QUALITY"
        if anomalous:
            return "ISOLATE_ANOMALOUS"
        return "REINFORCE_LEADER_MESH"

    def system2(self, qi, dl):
        """Resposta deliberativa: argmax de Q ajustado pelo aprendizado da rede."""
        if random.random() < self.epsilon:
            return random.choice(self._DA)
        net_l = dl.network_learning_mean()
        adj = {a: self.Q[a] + 0.1 * net_l * (0 if a == "DO_NOTHING" else 1) for a in self._DA}
        if qi < THRESHOLD_S2:
            adj["DO_NOTHING"] -= 0.4
        return max(adj, key=adj.get)

    def choose(self, knowledge, dl, qi, p_threat, anomalous):
        """System 1 se p_threat > theta; caso contrario System 2."""
        theta = self.current_threshold()
        if p_threat > theta:
            da = self.system1(knowledge, qi, p_threat, anomalous)
            system = "S1"
        else:
            da = self.system2(qi, dl)
            system = "S2"
        self.update_threshold(p_threat)
        return self._MAP[da], da, system, theta

    def update_Q(self, da, reward):
        self.Q[da] = (1 - ALPHA_Q) * self.Q[da] + ALPHA_Q * (reward + GAMMA_Q * max(self.Q.values()))

    def decay(self):
        self.epsilon = max(self.eps_min, self.epsilon * self.eps_decay)
