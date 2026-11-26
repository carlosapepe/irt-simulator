# Métricas e correspondência com o artigo

Todas as métricas são calculadas por ciclo em `irt/metrics.py` e agregadas (média) por run em `irt/experiment.py`.

## Qualidade de rede

| Métrica | Coluna no CSV | Definição | Função |
|---|---|---|---|
| Índice de Qualidade (QI) | `qi_mean` (após a defesa), `qi_before_mean`, `qi_failure_mean` | `QI = 0.5·C + 0.3·Eprop + 0.2·D` | `quality_index` |
| Fração conectada C | `connectivity_mean` | \|Cmax\| / \|V\| | `quality_index` |
| Eficiência de propagação Eprop (Eq. 16) | `prop_eff_mean` | média de 1/d(u,v) sobre pares de Cmax | `quality_index` |
| Entrega D | `delivery_mean` | Σ quality·capacity das arestas de Cmax / (10·\|E_Cmax\|) | `quality_index` |
| Eficiência global Eprop_g | `eprop_global_mean` | média de 1/d(u,v) sobre **todos** os pares de V (desconectados = 0) | `global_efficiency` |

> Eprop é restrito ao maior componente e pode **subir** quando a rede colapsa (o componente fica pequeno e denso). Para comparar cenários sob fragmentação, use Eprop_g.

Três medições de QI por ciclo:

- `qi_before`: após a operação normal, antes do ataque;
- `qi_failure`: logo após falhas e ataques;
- `qi`: após as ações de resiliência (igual a `qi_failure` nos cenários sem defesa).

## Resiliência

| Métrica | Coluna | Definição | Função |
|---|---|---|---|
| ARF (Eq. 6) | `arf_mean` | (QI_after − QI_failure) / (QI_before − QI_failure + ε) | `adaptive_resilience_factor` |
| ρ (Eq. 7) | `rho_mean` | média sobre as arestas de β·quality·(capacity/10), β = 0.05 | `resilience_activation_coeff` |
| TII (Eq. 5) | `tii_mean` | (1/\|V\|)·Σ_i w_i·φ_i, com w_i = grau_i / grau médio | `topology_intuition_index` |

Componentes de φ_i no TII (pesos iguais, 1/3 cada):

1. estado de aprendizado: `1 − L_i`;
2. confiança de detecção: escore Rintuitive do nó;
3. histórico: média do ganho de QI nos últimos 5 ciclos, dividida por 0.2 e recortada em [0, 1].

ARF e TII só são reportados no relatório para o cenário `Ataque+Protecao`. O ARF existe no CSV também para `Baseline+Ataque`, mas ali vale 0 (nenhuma recuperação).

## Detecção

Calculadas sobre todos os nós do grafo (vivos e mortos), contra o ground truth do ciclo (ver `DADOS_EMULADOS.md`, seção 5), **antes** da mitigação.

| Métrica | Coluna | Observação |
|---|---|---|
| Precisão, Recall, F1, Acurácia | `precision_mean`, `recall_mean`, `f1_mean`, `accuracy_mean` | nó anômalo ⇔ escore Rintuitive > 0.15 |
| ROC-AUC (Eq. 14) | `roc_auc_mean` | `sklearn.metrics.roc_auc_score` sobre os escores dos nós vivos; ciclos com uma só classe são ignorados |
| Matriz de confusão | `tp_sum`, `fp_sum`, `fn_sum`, `tn_sum` | soma nos ciclos da run |

Nos cenários sem motor intuitivo nada é detectado, então recall = 0 e precisão = 0 por definição.

## Mecanismo dual

| Coluna | Significado |
|---|---|
| `n_s1`, `n_s2` | ciclos decididos pelo System 1 / System 2 |
| `reward_s1_mean`, `reward_s2_mean` | recompensa média por sistema |

Recompensa por ciclo: `r = (QI_after − QI_failure) − 0.04·FP − 0.08·FN`.

O System 1 é acionado quando `p_threat > θ`, sendo `p_threat = 1 − média(L)` dos líderes vivos e `θ` o quantil de 75% do histórico de `p_threat`, recortado em [0.05, 0.40] (valor inicial 0.15).

## Intervalo de confiança

`IC95` no relatório = 1.96·s/√n sobre as médias por run (n = 35), aproximação normal.
