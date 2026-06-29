import numpy as np

"""Registra estatísticas de simulações."""


def consolidate(array: np.ndarray) -> dict:
    """"""
    summary = {}
    for pontos in range(10):
        appearances = len(array[array[:,1] == pontos])
        classifications =  len(array[(array[:, 1] == pontos) & (array[:, 2] == 1.0)])
        probability = classifications / appearances if appearances > 0 else 0
        summary[pontos] = {
            "appearances": appearances,
            "classifications": classifications,
            "probability": probability
        }
    return summary


def consolidate_teams(array: np.ndarray) -> list[dict]:
    """Calcula a probabilidade de classificação de cada seleção de forma vetorizada."""
    from models.teams import TEAMS
    
    # O array tem formato linearizado (N * 48, 3). Reshaping a coluna 'passed' (índice 2) para (N, 48)
    passed_matrix = array[:, 2].reshape(-1, 48)
    rates = np.mean(passed_matrix, axis=0) # Média vertical fornece a taxa de passagem de cada time
    
    team_stats = []
    for t in range(48):
        team_stats.append({
            "name": TEAMS[t]["name"],
            "rating": TEAMS[t]["rating"],
            "probability": float(rates[t])
        })
        
    # Ordena pela maior probabilidade de classificação
    team_stats.sort(key=lambda x: (x["probability"], x["rating"]), reverse=True)
    return team_stats