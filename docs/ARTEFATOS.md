# Artefatos gerados

`python run_experiments.py` grava três arquivos em `results/` (ou na pasta indicada em `--outdir`). Eles não são versionados (ver `.gitignore`); para publicar os resultados exatos do artigo, anexe-os a uma *release* do GitHub ou deposite-os no Zenodo.

## 1. `resultados_modelo_irt.csv`

Uma linha por **(cenário, topologia, run)**: 3 × 3 × 35 = **315 linhas**. Cada valor é a média (ou soma, nas colunas `_sum`) dos 35 ciclos da run.

| Coluna | Tipo | Descrição |
|---|---|---|
| `run_id` | int | 1 a 35 |
| `seed` | int | semente da run (59, 76, …) |
| `config` | str | `Baseline`, `Baseline+Ataque`, `Ataque+Protecao` |
| `topology` | str | `Barabasi-Albert (BA)`, `Erdos-Renyi (ER)`, `Watts-Strogatz (WS)` |
| `qi_mean` | float | QI após a defesa |
| `qi_before_mean` | float | QI antes do ataque |
| `qi_failure_mean` | float | QI logo após o ataque |
| `connectivity_mean` | float | fração no maior componente |
| `prop_eff_mean` | float | Eprop (Eq. 16), restrito a Cmax |
| `eprop_global_mean` | float | eficiência global sobre todo V |
| `delivery_mean` | float | entrega D |
| `rho_mean` | float | ρ (Eq. 7) |
| `arf_mean` | float | ARF (Eq. 6); NaN em `Baseline` |
| `tii_mean` | float | TII (Eq. 5); vazio fora de `Ataque+Protecao` |
| `precision_mean`, `recall_mean`, `f1_mean`, `accuracy_mean` | float | detecção; NaN em `Baseline` |
| `roc_auc_mean` | float | ROC-AUC (Eq. 14); NaN quando não há escores |
| `tp_sum`, `fp_sum`, `fn_sum`, `tn_sum` | int | matriz de confusão somada nos ciclos |
| `n_s1`, `n_s2` | int | ciclos decididos por System 1 / System 2 |
| `reward_s1_mean`, `reward_s2_mean` | float | recompensa média por sistema; NaN se o sistema não foi usado |

Definições completas em [`METRICAS.md`](METRICAS.md).

## 2. `relatorio_comparativo.txt`

As mesmas tabelas impressas no terminal, para cada topologia:

- **Qualidade de Rede**: QI, IC95, Cfrac, Eprop, Eprop_g, Delivery, ARF, TII;
- **Detecção de Anomalias**: Precisão, Recall, F1, Acurácia, ROC-AUC;
- **Mecanismo Dual**: % de ciclos e recompensa média de cada sistema.

## 3. `metadados_execucao.json`

Registro da execução: versão do código, número de runs/ciclos/nós, sementes, topologias, parâmetros completos de cada cenário e do ataque, tempo de execução, versão do Python, plataforma e versões das bibliotecas. Serve para conferir se uma execução foi feita nas mesmas condições da do artigo.

## Reproduzindo tabelas do artigo

```python
import pandas as pd
df = pd.read_csv("results/resultados_modelo_irt.csv")
df.groupby(["topology", "config"])[["qi_mean", "eprop_global_mean", "f1_mean", "roc_auc_mean"]].mean()
```
