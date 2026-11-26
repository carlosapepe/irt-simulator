"""Um ciclo operacional completo do IRT.

Ordem das etapas (importa para a reprodutibilidade, pois define a
sequencia de numeros aleatorios consumidos):

    1. formacao -> eleicao -> autenticacao -> operacao      => QI_before
    2. falhas + ataques (se o cenario tiver ataque)         => QI_failure, ground truth
    3. deteccao intuitiva (Rintuitive)
    4. decisao (Dual System, regra fixa ou nenhuma)
    5. metricas de deteccao + aprendizado de assinaturas
    6. acoes de resiliencia (se o cenario tiver defesa)      => QI_after
    7. recompensa, atualizacao de Q, L_i e rede de conhecimento
    8. metricas do ciclo (TII, ARF, rho, Eprop_global, ROC-AUC)
"""

import numpy as np

from .attacks import inject_failures_and_attacks
from .config import ATTACK_CONFIG, FN_PENALTY, FP_PENALTY
from .detection import detect_anomalies_intuitive
from .metrics import (
    adaptive_resilience_factor,
    compute_confusion,
    global_efficiency,
    quality_index,
    resilience_activation_coeff,
    roc_auc,
    topology_intuition_index,
)
from .operations import authenticate_leaders, elect_leaders, formation_phase, operation_step
from .resilience import apply_resilience


def single_cycle(G, config, cycle_id, knowledge=None, dl=None, dual=None):
    # 1) Fases operacionais
    formation_phase(G)
    leader, deputy = elect_leaders(G)
    authenticate_leaders(G, leader, deputy)
    operation_step(G)

    qi_before, parts_before = quality_index(G)

    # 2) Falhas e ataques
    if config.get("inject_attacks", True):
        gt = inject_failures_and_attacks(G, leader, ATTACK_CONFIG)
    else:
        gt = set()

    qi_failure, parts_failure = quality_index(G)

    # 3) Deteccao intuitiva
    if config.get("use_intuitive"):
        anomalies, score_map = detect_anomalies_intuitive(G, knowledge)
    else:
        anomalies = set()
        score_map = {}

    # 4) Decisao
    if not config.get("apply_defense", True):
        action = "OK"
        dual_action = None
        system_used = ""
        p_thr = 0.0
        theta_s1 = np.nan
    elif config.get("use_intuitive"):
        ldrs = [v for v in G.nodes if G.nodes[v].get("role") == "leader" and G.nodes[v].get("alive", True)]
        p_thr = dl.threat_probability(G, ldrs)
        knowledge.update_contextual(cycle_id, qi_failure, "HIGH" if p_thr > dual.current_threshold() else "LOW")
        knowledge.update_emergent(cycle_id, anomalies)
        action, dual_action, system_used, theta_s1 = dual.choose(knowledge, dl, qi_failure, p_thr, anomalies)
    else:
        # Regra fixa por limiar de QI (nao usada pelos cenarios atuais;
        # mantida para defesa sem motor intuitivo)
        if qi_failure >= 0.70:
            action = "OK"
        elif qi_failure >= 0.55:
            action = "REINFORCE_MESH"
        else:
            action = "ISOLATE_SUSPECTS_AND_REWIRE"
        dual_action = None
        system_used = ""
        p_thr = 0.0
        theta_s1 = np.nan

    # 5) Metricas de deteccao (antes da mitigacao) + aprendizado supervisionado
    #    das assinaturas com o ground truth do ciclo
    universe = set(G.nodes)
    tp, fp, fn, tn, prec, rec, f1, acc = compute_confusion(universe, gt, anomalies)

    if config.get("use_intuitive"):
        for v in G.nodes:
            if G.nodes[v].get("alive", True):
                knowledge.learn_attack_pattern(v, G, v in gt)

    # 6) Resiliencia
    if config.get("apply_defense", True):
        leader, deputy = apply_resilience(G, leader, deputy, action, anomalies, config)

    qi_after, parts_after = quality_index(G)

    # 7) Recompensa e aprendizado
    reward = (qi_after - qi_failure) - (FP_PENALTY * fp) - (FN_PENALTY * fn)

    if config.get("use_intuitive"):
        dual.update_Q(dual_action, reward)
        dual.decay()
        dl.step(G, anomalies)
        bucket = knowledge.discretize(qi_failure, p_thr)
        knowledge.update_intuitive(bucket, dual_action, reward)
        knowledge.update_historical(cycle_id, dual_action, qi_after - qi_failure)

    # 8) Metricas do ciclo
    tii = (topology_intuition_index(G, dl, score_map, knowledge, cycle_id)
           if config.get("use_intuitive") else None)
    arf = adaptive_resilience_factor(qi_before, qi_failure, qi_after) if config.get("inject_attacks") else None
    rho = resilience_activation_coeff(G)
    eprop_global = global_efficiency(G)
    auc = roc_auc(list(score_map.keys()), gt, score_map)

    return {
        "tii": tii,
        "arf": arf,
        "rho": rho,
        "prop_eff": parts_after["prop_eff"],
        "eprop_global": eprop_global,
        "roc_auc": auc,
        "qi_before": qi_before,
        "qi_failure": qi_failure,
        "qi": qi_after,
        "connectivity": parts_after["connectivity_frac"],
        "delivery": parts_after["delivery_ratio"],
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "accuracy": acc,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "action": action,
        "system": system_used,
        "dual_action": dual_action if dual_action else "",
        "reward": float(reward),
        "p_threat": float(p_thr),
    }
