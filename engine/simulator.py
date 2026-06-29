import numpy as np
from models.match_model import MatchModel

def run_simulation_batch(N: int, model: MatchModel = None) -> tuple[np.ndarray, np.ndarray]:
    base_lam = 1.35
    
    # 1. Configurar as forças das equipes de forma vetorizada (Shape: 48)
    if model is None:
        weight_factor = 0.0
        strengths_arr = np.full(48, 0.5)
    else:
        weight_factor = model.weight_factor
        strengths_arr = np.array([model.strengths.get(i, 0.5) for i in range(48)])

    # Índices locais das 6 partidas possíveis dentro de um grupo de 4 times
    home_idx_local = np.array([0, 0, 0, 1, 1, 2])
    away_idx_local = np.array([1, 2, 3, 2, 3, 3])
    
    # Expandir para os IDs globais dos 72 jogos da fase de grupos (12 grupos x 6 jogos)
    group_offsets = np.arange(12)[:, np.newaxis] * 4
    all_home_ids = (group_offsets + home_idx_local).reshape(12, 6)
    all_away_ids = (group_offsets + away_idx_local).reshape(12, 6)
    
    # Calcular os lambdas de Poisson para os 72 confrontos de uma vez (exponencial ortogonal)
    if weight_factor > 0.0:
        diff = strengths_arr[all_home_ids] - strengths_arr[all_away_ids]
        lam_home = base_lam * np.exp(weight_factor * diff)
        lam_away = base_lam * np.exp(-weight_factor * diff)
    else:
        lam_home = np.full((12, 6), base_lam)
        lam_away = np.full((12, 6), base_lam)
        
    # Broadcast dos lambdas para cobrir todas as N iterações de forma tridimensional (Shape: N, 12, 6)
    lam_home_3d = np.tile(lam_home, (N, 1, 1))
    lam_away_3d = np.tile(lam_away, (N, 1, 1))
    
    # 2. GERAR TODOS OS GOLS DA COPA DE UMA SÓ VEZ EM MEMÓRIA C
    home_goals = np.random.poisson(lam=lam_home_3d).astype(np.uint8)
    away_goals = np.random.poisson(lam=lam_away_3d).astype(np.uint8)
    
    # 3. Mapeamento de pontos por partida (Shape: N, 12, 6)
    pts_home_games = np.where(home_goals > away_goals, 3, np.where(home_goals == away_goals, 1, 0)).astype(np.uint8)
    pts_away_games = np.where(away_goals > home_goals, 3, np.where(home_goals == away_goals, 1, 0)).astype(np.uint8)
    
    # 4. Construção das Tabelas dos Grupos (Shape: N, 12, 4)
    pontos = np.zeros((N, 12, 4), dtype=np.uint8)
    gols_marcados = np.zeros((N, 12, 4), dtype=np.uint8)
    gols_sofridos = np.zeros((N, 12, 4), dtype=np.uint8)
    
    # Loop fixo de 6 iterações (tamanho constante das partidas do grupo, não escala com N)
    for i in range(6):
        h = home_idx_local[i]
        a = away_idx_local[i]
        
        pontos[:, :, h] += pts_home_games[:, :, i]
        pontos[:, :, a] += pts_away_games[:, :, i]
        
        gols_marcados[:, :, h] += home_goals[:, :, i]
        gols_marcados[:, :, a] += away_goals[:, :, i]
        
        gols_sofridos[:, :, h] += away_goals[:, :, i]
        gols_sofridos[:, :, a] += home_goals[:, :, i]
        
    saldo = gols_marcados.astype(np.int16) - gols_sofridos.astype(np.int16)
    
    # 5. O TRUQUE ARQUITETURAL: Sorting de múltiplos critérios sem loops (Score Combinado)
    # Confronto Direto (H2H) vetorizado
    h2h_pts_mat = np.zeros((N, 12, 4, 4), dtype=np.uint8)
    h2h_gd_mat = np.zeros((N, 12, 4, 4), dtype=np.int16)
    h2h_gs_mat = np.zeros((N, 12, 4, 4), dtype=np.uint8)
    
    for i in range(6):
        h = home_idx_local[i]
        a = away_idx_local[i]
        
        # Time de casa vs Time de fora
        h2h_pts_mat[:, :, h, a] = pts_home_games[:, :, i]
        h2h_gd_mat[:, :, h, a] = home_goals[:, :, i].astype(np.int16) - away_goals[:, :, i].astype(np.int16)
        h2h_gs_mat[:, :, h, a] = home_goals[:, :, i]
        
        # Time de fora vs Time de casa
        h2h_pts_mat[:, :, a, h] = pts_away_games[:, :, i]
        h2h_gd_mat[:, :, a, h] = away_goals[:, :, i].astype(np.int16) - home_goals[:, :, i].astype(np.int16)
        h2h_gs_mat[:, :, a, h] = away_goals[:, :, i]
        
    # Máscara para identificar times com a mesma pontuação geral no grupo
    pontos_col = pontos[:, :, :, np.newaxis]
    pontos_row = pontos[:, :, np.newaxis, :]
    tied_mask = (pontos_col == pontos_row)
    
    # Soma das estatísticas apenas nos confrontos entre os times empatados
    h2h_pts_tied = np.sum(h2h_pts_mat * tied_mask, axis=3)
    h2h_gd_tied = np.sum(h2h_gd_mat * tied_mask, axis=3)
    h2h_gs_tied = np.sum(h2h_gs_mat * tied_mask, axis=3)
    
    # Obter os ratings FIFA para o desempate final
    from models.teams import TEAMS
    ratings_arr = np.array([TEAMS[t]["rating"] for t in range(48)], dtype=np.int32)
    # Criar mapeamento de IDs globais (0 a 47) tridimensional
    global_ids_3d = np.tile(np.arange(48, dtype=np.uint8).reshape(12, 4), (N, 1, 1))
    team_ratings = ratings_arr[global_ids_3d]
    
    # Codificação dos múltiplos critérios em um único inteiro de 64 bits para ordenação estável
    # Critérios em ordem de prioridade (decrescente):
    # 1. Pontos no grupo
    # 2. Pontos no confronto direto
    # 3. Saldo de gols no confronto direto
    # 4. Gols marcados no confronto direto
    # 5. Saldo de gols geral
    # 6. Gols marcados geral
    # 7. Rating FIFA
    score = (
        pontos.astype(np.int64) * 10_000_000_000_000 +
        h2h_pts_tied.astype(np.int64) * 100_000_000_000 +
        (h2h_gd_tied.astype(np.int64) + 15) * 1_000_000_000 +
        h2h_gs_tied.astype(np.int64) * 10_000_000 +
        (saldo.astype(np.int64) + 50) * 100_000 +
        gols_marcados.astype(np.int64) * 2000 +
        team_ratings.astype(np.int64)
    )
    rankings = np.argsort(-score, axis=2) # Retorna os índices locais ordenados do 1º ao 4º lugar
    
    # Indexação avançada para reordenar todas as matrizes conforme o ranking real
    grid_n, grid_g = np.meshgrid(np.arange(N, dtype=np.int32), np.arange(12, dtype=np.int32), indexing='ij')
    grid_n = grid_n[:, :, np.newaxis]
    grid_g = grid_g[:, :, np.newaxis]
    
    sorted_global_ids = global_ids_3d[grid_n, grid_g, rankings]
    sorted_pontos = pontos[grid_n, grid_g, rankings]
    sorted_saldo = saldo[grid_n, grid_g, rankings]
    sorted_gols_marcados = gols_marcados[grid_n, grid_g, rankings]
    
    # 6. Definir Classificados Diretos (G2)
    passed = np.zeros((N, 48), dtype=np.uint8)
    grid_n_2d = np.arange(N, dtype=np.int32)[:, np.newaxis]
    
    passed[grid_n_2d, sorted_global_ids[:, :, 0]] = 1 # 1º Colocado
    passed[grid_n_2d, sorted_global_ids[:, :, 1]] = 1 # 2º Colocado
    
    # 7. Resolução Vetorizada da Repescagem dos 12 Terceiros Colocados
    thirds_ids = sorted_global_ids[:, :, 2]
    thirds_points = sorted_pontos[:, :, 2]
    thirds_saldo = sorted_saldo[:, :, 2]
    thirds_goals = sorted_gols_marcados[:, :, 2]
    
    # Obter ratings dos terceiros colocados para o desempate final por Ranking FIFA
    thirds_ratings = ratings_arr[thirds_ids]
    
    # Aplica o Score Combinado para classificar a tabela dos terceiros
    # Prioridades: Pontos ➔ Saldo Geral ➔ Gols Pró ➔ Rating FIFA
    thirds_score = (
        thirds_points.astype(np.int64) * 10_000_000 +
        (thirds_saldo.astype(np.int64) + 50) * 100_000 +
        thirds_goals.astype(np.int64) * 2000 +
        thirds_ratings.astype(np.int64)
    )
    thirds_rankings = np.argsort(-thirds_score, axis=1)
    
    # Extrai os 8 melhores terceiros de cada uma das N iterações de uma vez
    best_thirds_ids = thirds_ids[grid_n_2d, thirds_rankings[:, :8]]
    passed[grid_n_2d, best_thirds_ids] = 1
    
    flat_points = pontos.reshape(N, 48)
    return flat_points, passed


def run_simulation(iterations: int, model: MatchModel = None, batch_size: int = 100_000) -> tuple[dict, list[dict]]:
    # Inicializa os acumuladores
    appearances_acc = np.zeros(10, dtype=np.int64)
    classifications_acc = np.zeros(10, dtype=np.int64)
    passed_counts_acc = np.zeros(48, dtype=np.int64)
    
    # Executa a simulação em lotes (batches)
    remaining = iterations
    while remaining > 0:
        current_batch = min(batch_size, remaining)
        flat_points, passed = run_simulation_batch(current_batch, model)
        
        # Acumula classificações por time
        passed_counts_acc += passed.sum(axis=0, dtype=np.int64)
        
        # Acumula estatísticas por faixa de pontos obtida
        for p in range(10):
            mask_p = (flat_points == p)
            appearances_acc[p] += mask_p.sum(dtype=np.int64)
            classifications_acc[p] += passed[mask_p].sum(dtype=np.int64)
            
        remaining -= current_batch

    # Monta o dicionário de resumo (probabilidade por pontos obtidos)
    summary = {}
    for p in range(10):
        app = int(appearances_acc[p])
        cls = int(classifications_acc[p])
        prob = cls / app if app > 0 else 0.0
        summary[p] = {
            "appearances": app,
            "classifications": cls,
            "probability": prob
        }
        
    # Monta a lista com probabilidade para cada uma das seleções
    from models.teams import TEAMS
    team_summary = []
    for t in range(48):
        prob = float(passed_counts_acc[t]) / iterations
        team_summary.append({
            "name": TEAMS[t]["name"],
            "rating": TEAMS[t]["rating"],
            "probability": prob
        })
    team_summary.sort(key=lambda x: (x["probability"], x["rating"]), reverse=True)
    
    return summary, team_summary