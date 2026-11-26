# Dados emulados

O IRT **não usa nenhum dataset externo**. Toda a rede, o tráfego, as falhas e os ataques são gerados sinteticamente a cada execução, a partir de sementes fixas. Este documento descreve o que é emulado, com quais distribuições e onde está no código.

## 1. Topologias (`irt/topology.py`)

Cada run gera um grafo não direcionado com `N_NODES = 150` nós, em um de três modelos clássicos:

| Rótulo no CSV | Gerador NetworkX | Parâmetros | O que representa |
|---|---|---|---|
| `Barabasi-Albert (BA)` | `barabasi_albert_graph(n, m)` | `m = 2` | Rede livre de escala, com *hubs* (gateways/controladores concentradores) |
| `Erdos-Renyi (ER)` | `gnp_random_graph(n, p)` | `p = 0.08` | Malha aleatória homogênea (grau médio ≈ 12) |
| `Watts-Strogatz (WS)` | `watts_strogatz_graph(n, k, p)` | `k = 6`, `p = 0.2` | Mundo pequeno: vizinhança local com atalhos (células de manufatura ligadas entre si) |

Se o grafo gerado for desconexo, os componentes são ligados em cadeia por uma aresta aleatória entre componentes consecutivos.

## 2. Atributos dos nós

Sorteados uma vez na criação do grafo (e novamente quando um nó morto é reintegrado):

| Atributo | Distribuição inicial | Faixa durante a simulação | Significado |
|---|---|---|---|
| `traffic` | U(0.1, 1.0) | [0.05, 5.0] | Carga de tráfego normalizada |
| `packet_rate` | U(1, 50) | [0.5, 200] | Taxa de pacotes (pacotes/s) |
| `latency` | U(5, 25) | [2, 200] | Latência (ms) |
| `ema_latency` | = `latency` | — | Média móvel exponencial da latência (α = 0.35) |
| `energy` | U(0.8, 1.0) | [0, 1] | Energia/bateria normalizada |
| `hello_count` | inteiro U{3, …, 9} | — | Mensagens HELLO na fase de formação |
| `role` | `member` | `member` / `leader` / `deputy` | Papel no cluster |
| `authenticated` | `False` | bool | Líder/vice aprovado na autenticação |
| `alive` | `True` | bool | Nó operante |
| `under_attack` | `False` | bool | Nó sob DoS (ground truth) |

## 3. Atributos dos enlaces

| Atributo | Distribuição | Significado |
|---|---|---|
| `quality` | U(0.7, 1.0) | Confiabilidade do enlace |
| `capacity` | U(1.0, 10.0) | Capacidade (unidade arbitrária) |

Arestas criadas pelas ações de resiliência recebem atributos das mesmas distribuições.

## 4. Dinâmica de operação normal (`irt/operations.py`)

A cada ciclo, para cada nó vivo:

- fator de carga `lf ~ N(1.0, 0.05)`, recortado em [0.8, 1.2];
- `traffic`, `packet_rate` e `latency` são multiplicados por `lf` (com recorte nas faixas da tabela acima);
- `ema_latency ← 0.35·latency + 0.65·ema_latency`;
- `energy ← max(0, energy − 0.002·lf)`.

Também a cada ciclo: líder e vice são eleitos como os dois nós vivos de maior grau, e autenticados se `energy > 0.3` e `latency < 100 ms`.

## 5. Falhas e ataques (`irt/attacks.py`)

Nos cenários com ataque, **todo ciclo** aplica, nesta ordem (`ATTACK_CONFIG` em `irt/config.py`):

| Evento | Quantidade/ciclo | Efeito |
|---|---|---|
| Falha de nó | 2 nós vivos ao acaso | `alive = False`, `traffic = 0`, todas as arestas removidas |
| Falha de enlace | 3 arestas ao acaso | aresta removida |
| DoS | 3 nós vivos ainda não atacados | `under_attack = True` |
| DoS no líder | desativado (`attack_leader = False`) | — |

Todo nó vivo com `under_attack = True` (inclusive os atacados em ciclos anteriores e ainda não mitigados) recebe a **assinatura de DoS**:

- `traffic ~ U(1.5, 7.0)`
- `latency ~ U(28, 90)` ms

**Ground truth** do ciclo = conjunto de nós vivos com `under_attack = True` após a injeção. É contra ele que precisão, recall, F1, acurácia e ROC-AUC são calculados.

Como não há recuperação espontânea, o dano é cumulativo: sem defesa, a rede perde 2 nós e 3 enlaces por ciclo e acumula nós sob DoS.

## 6. Dados aprendidos (`irt/knowledge.py`, `irt/learning.py`)

Estes dados não são sorteados; são gerados pelo próprio motor intuitivo ao longo da run e descartados ao final dela:

- **Assinaturas Rintuitive** — chave `(traffic arredondado a 0.5, round(latency/30))` → lista de rótulos 0/1. O aprendizado é **supervisionado pelo ground truth do ciclo** (após o cálculo das métricas de detecção daquele ciclo, portanto sem vazamento dentro do ciclo).
- **Estado L_i** de cada nó, inicializado com a energia do nó.
- **Tabela Q** do System 2 e memória intuitiva `(bucket de estado, ação) → recompensas`.
- **Camadas histórica, contextual e emergente** da rede de conhecimento.

## 7. Sementes

- Cada run usa uma semente própria: `59, 76, 93, …` (passo 17; 35 sementes).
- Antes de construir o grafo, `random` e `numpy.random` são re-semeados com essa semente, e a mesma semente é passada ao gerador do NetworkX.
- As mesmas sementes são usadas nos três cenários e nas três topologias, o que torna as comparações pareadas (mesmo grafo inicial).
