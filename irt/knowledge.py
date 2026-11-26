"""Rede de conhecimento (camadas historica, intuitiva, contextual e emergente)
e memoria de assinaturas de ataque (Rintuitive)."""

from collections import defaultdict, deque
from typing import Optional

import numpy as np


def _signature(G, v):
    """Assinatura discretizada do no: (trafego em passos de 0.5, latencia em faixas de 30 ms)."""
    traffic = G.nodes[v]["traffic"]
    latency = G.nodes[v]["latency"]
    traffic_b = round(traffic * 2) / 2
    latency_b = round(latency / 30)
    return (traffic_b, latency_b)


class KnowledgeNetworks:
    """Deteccao baseada em Rintuitive: aprende assinaturas de ataque.

    Camadas:
        attack_signatures : assinatura -> lista de rotulos (1 = atacado)
        intuitive         : (bucket de estado, acao) -> recompensas observadas
        historical        : ciclo -> {acao, qi_delta, reward}
        contextual        : ultimo contexto {ciclo, qi, ameaca}
        emergent          : ultimos 50 ciclos com anomalias detectadas
    """

    def __init__(self):
        self.historical = {}
        self.attack_signatures = defaultdict(list)  # (traffic_bucket, latency_bucket) -> [was_attacked]
        self.intuitive = defaultdict(list)
        self.contextual = {}
        self.emergent = deque(maxlen=50)

    def learn_attack_pattern(self, v, G, was_attacked):
        """Registra a assinatura atual do no v com o rotulo do ground truth."""
        self.attack_signatures[_signature(G, v)].append(1 if was_attacked else 0)

    def recall_attack_intuitive(self, v, G) -> float:
        """Confianca intuitiva de que v esta sob ataque: taxa historica de
        ataque observada para a assinatura atual (0.0 se nunca vista)."""
        sig = _signature(G, v)
        if sig not in self.attack_signatures or not self.attack_signatures[sig]:
            return 0.0
        hits = sum(self.attack_signatures[sig])
        total = len(self.attack_signatures[sig])
        return float(hits / total)

    def update_intuitive(self, bucket, action, reward):
        self.intuitive[(bucket, action)].append(reward)

    def update_historical(self, cycle, action, qi_delta):
        self.historical[cycle] = {"action": action, "qi_delta": qi_delta, "reward": 0.3 * qi_delta}

    def update_contextual(self, cycle, qi, threat):
        self.contextual = {"cycle": cycle, "qi": qi, "threat": threat}

    def update_emergent(self, cycle, anomalies):
        if anomalies:
            self.emergent.append({"cycle": cycle, "anomalies": len(anomalies)})

    def best_intuitive_action(self, bucket) -> Optional[str]:
        """Acao com maior recompensa media ja observada neste bucket."""
        cands = {a: np.mean(r) for (b, a), r in self.intuitive.items() if b == bucket and r}
        return max(cands, key=cands.get) if cands else None

    @staticmethod
    def discretize(qi: float, p_threat: float = 0.0) -> str:
        """Bucket de estado: QI (low <0.45 | mid <0.65 | high) x ameaca (hi >0.35 | lo)."""
        qi_b = "low" if qi < 0.45 else "mid" if qi < 0.65 else "high"
        th_b = "hi" if p_threat > 0.35 else "lo"
        return f"qi_{qi_b}_th_{th_b}"
