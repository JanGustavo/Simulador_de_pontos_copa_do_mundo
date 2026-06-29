import numpy as np
from models.teams import TEAMS
from models.match_model import MatchModel

# Chaveamento oficial fornecido
LADO_ESQUERDO = [
    ("Alemanha", "Paraguai"),                  # J1
    ("França", "Suécia"),                      # J2
    ("África do Sul", "Canadá"),                # J3
    ("Países Baixos", "Marrocos"),              # J4
    ("Portugal", "Croácia"),                    # J5
    ("Espanha", "Áustria"),                    # J6
    ("Estados Unidos", "Bósnia e Herzegovina"),# J7
    ("Bélgica", "Senegal")                      # J8
]

LADO_DIREITO = [
    ("Brasil", "Japão"),                       # J9
    ("Costa do Marfim", "Noruega"),            # J10
    ("México", "Equador"),                     # J11
    ("Inglaterra", "República Democrática do Congo"), # J12
    ("Argentina", "Cabo Verde"),               # J13
    ("Austrália", "Egito"),                     # J14
    ("Suíça", "Argélia"),                       # J15
    ("Colômbia", "Gana")                       # J16
]

# Normalizar nomes para mapeamento de IDs
TEAM_NAME_TO_ID = {}
for tid, info in TEAMS.items():
    TEAM_NAME_TO_ID[info["name"].strip()] = tid

def get_team_id(name: str) -> int:
    name_clean = name.strip().replace("Básnia", "Bósnia")
    if name_clean in TEAM_NAME_TO_ID:
        return TEAM_NAME_TO_ID[name_clean]
    raise ValueError(f"Time não encontrado: {name}")

def simulate_matches_vectorized(model: MatchModel, strengths_arr: np.ndarray, t1: np.ndarray, t2: np.ndarray) -> np.ndarray:
    """Simula M confrontos de mata-mata em paralelo para N iterações."""
    N, M = t1.shape
    s1 = strengths_arr[t1]
    s2 = strengths_arr[t2]
    
    # Gerar lambdas com base no MatchModel
    lam1 = 1.35 * np.exp(model.weight_factor * (s1 - s2))
    lam2 = 1.35 * np.exp(model.weight_factor * (s2 - s1))
    
    # Gerar gols da partida
    g1 = np.random.poisson(lam1)
    g2 = np.random.poisson(lam2)
    
    # Vencedores no tempo regulamentar
    winners = np.where(g1 > g2, t1, t2)
    
    # Decisão por pênaltis em caso de empate
    ties = (g1 == g2)
    if np.any(ties):
        prob1 = 0.5 + 0.1 * (s1 - s2)
        prob1 = np.clip(prob1, 0.1, 0.9)
        rand_vals = np.random.random(size=(N, M))
        penalty_winners = np.where(rand_vals < prob1, t1, t2)
        winners = np.where(ties, penalty_winners, winners)
        
    return winners

def run_knockout_simulation(iterations: int, model: MatchModel = None) -> list[dict]:
    """Executa a simulação de Monte Carlo para o chaveamento de mata-mata completo."""
    if model is None:
        model = MatchModel(weight_factor=1.0)
        
    strengths_arr = np.array([model.strengths.get(i, 0.5) for i in range(48)])
    
    # Preparar IDs dos times iniciais
    left_t1_init = np.array([get_team_id(pair[0]) for pair in LADO_ESQUERDO], dtype=np.uint8)
    left_t2_init = np.array([get_team_id(pair[1]) for pair in LADO_ESQUERDO], dtype=np.uint8)
    
    right_t1_init = np.array([get_team_id(pair[0]) for pair in LADO_DIREITO], dtype=np.uint8)
    right_t2_init = np.array([get_team_id(pair[1]) for pair in LADO_DIREITO], dtype=np.uint8)
    
    # Broadcast para as N iterações
    left_t1 = np.tile(left_t1_init, (iterations, 1))
    left_t2 = np.tile(left_t2_init, (iterations, 1))
    right_t1 = np.tile(right_t1_init, (iterations, 1))
    right_t2 = np.tile(right_t2_init, (iterations, 1))
    
    # 1. Rodada de 32 (16vos de final)
    left_r32_winners = simulate_matches_vectorized(model, strengths_arr, left_t1, left_t2)
    right_r32_winners = simulate_matches_vectorized(model, strengths_arr, right_t1, right_t2)
    
    # 2. Rodada de 16 (Oitavas de final)
    left_r16_t1 = left_r32_winners[:, ::2]
    left_r16_t2 = left_r32_winners[:, 1::2]
    right_r16_t1 = right_r32_winners[:, ::2]
    right_r16_t2 = right_r32_winners[:, 1::2]
    
    left_r16_winners = simulate_matches_vectorized(model, strengths_arr, left_r16_t1, left_r16_t2)
    right_r16_winners = simulate_matches_vectorized(model, strengths_arr, right_r16_t1, right_r16_t2)
    
    # 3. Quartas de final
    left_qf_t1 = left_r16_winners[:, ::2]
    left_qf_t2 = left_r16_winners[:, 1::2]
    right_qf_t1 = right_r16_winners[:, ::2]
    right_qf_t2 = right_r16_winners[:, 1::2]
    
    left_qf_winners = simulate_matches_vectorized(model, strengths_arr, left_qf_t1, left_qf_t2)
    right_qf_winners = simulate_matches_vectorized(model, strengths_arr, right_qf_t1, right_qf_t2)
    
    # 4. Semifinais
    left_sf_t1 = left_qf_winners[:, [0]]
    left_sf_t2 = left_qf_winners[:, [1]]
    right_sf_t1 = right_qf_winners[:, [0]]
    right_sf_t2 = right_qf_winners[:, [1]]
    
    left_sf_winners = simulate_matches_vectorized(model, strengths_arr, left_sf_t1, left_sf_t2)
    right_sf_winners = simulate_matches_vectorized(model, strengths_arr, right_sf_t1, right_sf_t2)
    
    # 5. Final
    final_winners = simulate_matches_vectorized(model, strengths_arr, left_sf_winners, right_sf_winners)
    
    # Contabilização de avanços por time
    oitavas_counts = np.zeros(48, dtype=np.int64)
    quartas_counts = np.zeros(48, dtype=np.int64)
    semis_counts = np.zeros(48, dtype=np.int64)
    final_counts = np.zeros(48, dtype=np.int64)
    campeao_counts = np.zeros(48, dtype=np.int64)
    
    r16_teams = np.hstack([left_r32_winners, right_r32_winners])
    qf_teams = np.hstack([left_r16_winners, right_r16_winners])
    sf_teams = np.hstack([left_qf_winners, right_qf_winners])
    final_teams = np.hstack([left_sf_winners, right_sf_winners])
    campeao_teams = final_winners
    
    for t in range(48):
        oitavas_counts[t] = np.sum(r16_teams == t)
        quartas_counts[t] = np.sum(qf_teams == t)
        semis_counts[t] = np.sum(sf_teams == t)
        final_counts[t] = np.sum(final_teams == t)
        campeao_counts[t] = np.sum(campeao_teams == t)
        
    # Construir resumo
    results = []
    all_bracket_teams = set(left_t1_init) | set(left_t2_init) | set(right_t1_init) | set(right_t2_init)
    
    for t in all_bracket_teams:
        results.append({
            "name": TEAMS[t]["name"],
            "rating": TEAMS[t]["rating"],
            "oitavas": float(oitavas_counts[t]) / iterations,
            "quartas": float(quartas_counts[t]) / iterations,
            "semis": float(semis_counts[t]) / iterations,
            "final": float(final_counts[t]) / iterations,
            "campeao": float(campeao_counts[t]) / iterations,
        })
        
    results.sort(key=lambda x: x["campeao"], reverse=True)
    return results
