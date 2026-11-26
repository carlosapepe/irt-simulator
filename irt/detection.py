"""Deteccao intuitiva de anomalias (sem regras if/else fixas: apenas
recuperacao de assinaturas aprendidas no Rintuitive)."""

from .config import DETECTION_THRESHOLD


def detect_anomalies_intuitive(G, knowledge):
    """System 1 recall: detecta intuitivamente com base no Rintuitive.

    Devolve (anomalias, score_map); o score e' a confianca em [0, 1] usada
    no ROC-AUC. Um no e' anomalo se confianca > DETECTION_THRESHOLD.
    """
    anomalies = set()
    score_map = {}
    for v in G.nodes:
        if not G.nodes[v]["alive"]:
            continue
        conf_intuitive = knowledge.recall_attack_intuitive(v, G)
        score_map[v] = float(conf_intuitive)
        if conf_intuitive > DETECTION_THRESHOLD:
            anomalies.add(v)
    return anomalies, score_map
