"""Parametros globais do experimento IRT (Intuitive Resilient Topologies).

Todos os valores aqui sao os usados para gerar os resultados do artigo.
Alterar qualquer um deles muda os resultados; registre a alteracao no
commit e no arquivo de metadados gerado em results/.
"""

# ----------------------------------------------------------------------
# Reprodutibilidade
# ----------------------------------------------------------------------
RANDOM_SEED = 42          # semente "de import" (cada run e' re-semeada abaixo)
EPS = 1e-9                # evita divisao por zero no ARF (Eq. 6)

# ----------------------------------------------------------------------
# Escala do experimento
# ----------------------------------------------------------------------
N_NODES = 150             # nos por grafo
N_RUNS = 35               # repeticoes independentes por (topologia, cenario)
N_CYCLES = 35             # ciclos operacionais por run

SEED_START = 59
SEED_STEP = 17


def make_seeds(n_runs=N_RUNS):
    """Sementes por run: 59, 76, 93, ... (passo 17).

    Cada run re-semeia `random` e `numpy.random` com a sua semente, de modo
    que qualquer run pode ser reproduzida isoladamente.
    """
    return list(range(SEED_START, SEED_START + n_runs * SEED_STEP, SEED_STEP))


SEEDS = make_seeds()

# ----------------------------------------------------------------------
# Modelo de falhas e ataques (aplicado a CADA ciclo nos cenarios com ataque)
# ----------------------------------------------------------------------
ATTACK_CONFIG = {
    "num_node_failures": 2,   # nos que morrem (perdem todas as arestas)
    "num_link_failures": 3,   # arestas removidas ao acaso
    "num_dos_nodes": 3,       # novos nos sob DoS (trafego/latencia elevados)
    "attack_leader": False,   # se True, o lider tambem entra em DoS
}

# ----------------------------------------------------------------------
# Cenarios comparados
# ----------------------------------------------------------------------
NO_ATTACK_CFG = {
    "label": "Baseline",
    "use_intuitive": False,
    "inject_attacks": False,
    "apply_defense": False,
    "add_mesh_edges": 0,
    "promote_deputy": False,
    "reform_nodes": 0,
}

BASELINE_CFG = {
    "label": "Baseline+Ataque",
    "use_intuitive": False,
    "inject_attacks": True,
    "apply_defense": False,
    "add_mesh_edges": 0,
    "promote_deputy": False,
    "reform_nodes": 0,
}

IMPROVED_CFG = {
    "label": "Ataque+Protecao",
    "use_intuitive": True,
    "inject_attacks": True,
    "apply_defense": True,
    "add_mesh_edges": 3,           # orcamento de arestas por ciclo
    "promote_deputy": True,
    "mitigate_anomalies": True,
    "max_mitigate_per_cycle": 5,
    "reform_nodes": 2,             # nos mortos reintegrados por ciclo
    "max_reconnect_edges": 2,      # arestas p/ religar componentes isolados
}

CONFIGS = [NO_ATTACK_CFG, BASELINE_CFG, IMPROVED_CFG]
CONFIG_ORDER = [c["label"] for c in CONFIGS]

# Acoes de resiliencia executaveis (mapeadas a partir das acoes do Dual System)
ACTIONS = ["OK", "REINFORCE_MESH", "ISOLATE_SUSPECTS_AND_REWIRE", "PROMOTE_DEPUTY_AND_REWIRE"]

# ----------------------------------------------------------------------
# Topologias: (rotulo usado no CSV, codigo interno)
# ----------------------------------------------------------------------
TOPO_DEFS = [
    ("Barabasi-Albert (BA)", "BA"),
    ("Erdos-Renyi (ER)", "ER"),
    ("Watts-Strogatz (WS)", "WS"),
]

ER_P = 0.08       # probabilidade de aresta no G(n, p)
WS_K = 6          # vizinhos no anel inicial
WS_P = 0.2        # probabilidade de religacao
BA_M = 2          # arestas por novo no (ligacao preferencial)

# ----------------------------------------------------------------------
# Motor intuitivo (Dual System + aprendizado distribuido)
# ----------------------------------------------------------------------
THRESHOLD_S1 = 0.15          # limiar inicial p_threat para acionar o System 1
THRESHOLD_S2 = 0.60          # QI abaixo disso penaliza DO_NOTHING no System 2
DETECTION_THRESHOLD = 0.15   # confianca Rintuitive acima disso -> no anomalo
ALPHA_LEARN = 0.2            # taxa de aprendizado de L_i
BETA_INFLUENCE = 0.05        # influencia dos vizinhos em L_i (e beta_ij da Eq. 7)

# Pesos dos tres componentes de phi_i na Eq. (5) - devem somar 1.0
W_LEARNING = 1 / 3    # estado de aprendizado do agente (1 - L_i)
W_CONFIDENCE = 1 / 3  # confianca de deteccao (recall Rintuitive)
W_HISTORY = 1 / 3     # historico recente de desfecho

ALPHA_Q = 0.2         # taxa de aprendizado do Q-learning (System 2)
GAMMA_Q = 0.9         # fator de desconto do Q-learning

# Penalidades da recompensa: r = dQI - FP_PENALTY*FP - FN_PENALTY*FN
FP_PENALTY = 0.04
FN_PENALTY = 0.08
