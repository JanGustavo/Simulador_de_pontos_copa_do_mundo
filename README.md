# World Cup Simulator

Este projeto é um simulador estatístico para a Copa do Mundo FIFA de 48 seleções utilizando simulações de Monte Carlo. Ele calcula a probabilidade de cada pontuação na fase de grupos resultar em classificação para a fase de mata-mata.

🚀 **Experimente online**: O simulador possui uma versão web interativa executada no Streamlit. Você pode acessar e realizar suas próprias simulações diretamente em: [simuladordepontoscopadomundo.streamlit.app](https://simuladordepontoscopadomundo.streamlit.app/)

---

## Estrutura do Projeto

*   **`world_cup_simulator/main.py`**: O orquestrador da aplicação (UI e CLI).
*   **`world_cup_simulator/engine/simulator.py`**: Motor de simulação de partidas vetorizado e eficiente.
*   **`world_cup_simulator/engine/group_resolver.py`**: Algoritmo de classificação dos grupos e repescagem dos terceiros colocados.
*   **`world_cup_simulator/models/match_model.py`**: Modelo matemático para os confrontos.
*   **`world_cup_simulator/ui/display.py`**: Camada de visualização (terminal / Streamlit).

## Como Executar Localmente

Para executar a versão CLI:

```bash
cd world_cup_simulator
python3 main.py
```

Para rodar a versão interativa web localmente:

```bash
streamlit run world_cup_simulator/main.py
```

---

## Modelo Matemático (Explicação Moderada)

O simulador utiliza o método de **Monte Carlo**, que consiste em rodar o torneio inteiro milhares ou milhões de vezes para obter estimativas estatísticas precisas das probabilidades de classificação de cada equipe.

### 1. Geração de Gols (Distribuição de Poisson)
O número de gols marcados por uma equipe em uma partida é modelado seguindo a **Distribuição de Poisson**, que é a distribuição estatística padrão para contagem de eventos independentes em um intervalo fixo (como gols em um jogo de futebol):

$$P(k \text{ gols}) = \frac{\lambda^k e^{-\lambda}}{k!}$$

Onde $\lambda$ (lambda) representa a taxa esperada de gols de uma equipe. A taxa base utilizada é de $1.35$ gols por jogo.

### 2. Ajuste de Força (Fator Ponderado)
Para tornar os jogos realistas, o simulador usa a diferença de **Rating FIFA** entre as duas equipes como fator de ponderação:

*   Se `weight_factor = 0.0` (Modelo Ortogonal): As forças de todas as equipes são consideradas idênticas ($\lambda_{casa} = \lambda_{fora} = 1.35$). Todas as partidas têm chances simétricas de vitória/empate.
*   Se `weight_factor > 0.0` (Modelo Ponderado): A taxa esperada de gols de cada equipe é ajustada exponencialmente com base na diferença de força. Se a Equipe A é mais forte que a Equipe B:
    $$\lambda_A = 1.35 \cdot e^{\text{weight\_factor} \cdot (S_A - S_B)}$$
    $$\lambda_B = 1.35 \cdot e^{-\text{weight\_factor} \cdot (S_A - S_B)}$$
    Onde $S$ é a força normalizada do país (entre $0.0$ e $1.0$) baseada no seu ranking FIFA.

### 3. Classificação e Repescagem
Após simular as 72 partidas da fase de grupos, o simulador ordena as equipes de cada grupo seguindo os critérios oficiais de desempate (Pontos, Saldo de Gols, Gols Pró). Em seguida, agrupa os 12 terceiros colocados e classifica os 8 melhores para a fase de mata-mata.

---

## Resultados de Referência (1.000.000 de Simulações)

Estes são os resultados estatísticos obtidos com **1 milhão de simulações** utilizando o modelo ponderado padrão (`weight_factor = 1.0`).

### Probabilidade de Classificação por Pontos

Esta tabela demonstra a chance histórica de classificação para o mata-mata a partir dos pontos somados por uma seleção na fase de grupos (3 partidas):

| Pontos obtidos | Total de Aparições | Classificações de Sucesso | Chance de Classificação |
|:---:|:---:|:---:|:---:|
| **0** | 4.069.422 | 0 | **0.00%** |
| **1** | 5.477.363 | 199 | **0.00%** |
| **2** | 2.702.082 | 106.503 | **3.94%** |
| **3** | 7.944.300 | 4.133.741 | **52.03%** |
| **4** | 8.274.519 | 8.227.243 | **99.43%** |
| **5** | 2.622.539 | 2.622.539 | **100.00%** |
| **6** | 7.327.309 | 7.327.309 | **100.00%** |
| **7** | 5.384.136 | 5.384.136 | **100.00%** |
| **8** | 0 | 0 | **0.00%** |
| **9** | 4.198.330 | 4.198.330 | **100.00%** |

*Nota: Alcançar 8 pontos na fase de grupos é matematicamente impossível em 3 rodadas.*

### Top 15 Seleções Mais Favoritas à Classificação

Ao considerarmos o peso da força baseada no Rating FIFA real de cada país, as seleções mais tradicionais e fortes têm chances significativamente maiores de avançar:

| Posição | Seleção | Rating FIFA | Chance de Classificação |
|:---:|:---|:---:|:---:|
| **1** | Argentina | 1855 | **98.35%** |
| **2** | Brasil | 1784 | **97.01%** |
| **3** | França | 1840 | **96.82%** |
| **4** | Espanha | 1820 | **96.72%** |
| **5** | Bélgica | 1795 | **96.22%** |
| **6** | Alemanha | 1690 | **95.81%** |
| **7** | Portugal | 1745 | **94.89%** |
| **8** | Inglaterra | 1800 | **94.82%** |
| **9** | Suíça | 1610 | **90.00%** |
| **10** | Marrocos | 1663 | **89.96%** |
| **11** | Croácia | 1725 | **89.63%** |
| **12** | Países Baixos | 1740 | **89.23%** |
| **13** | Colômbia | 1655 | **88.18%** |
| **14** | Estados Unidos | 1661 | **87.87%** |
| **15** | México | 1650 | **87.43%** |
