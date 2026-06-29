"""Módulo responsável por resolver a classificação dos grupos com base nos resultados dos jogos."""
from models.teams import TEAMS

def classify_group(group_tables: dict, games: list[dict] = None) -> dict:
    ordered = order_teams(group_tables, games)
    return {
        "primeiro": ordered[0],
        "segundo": ordered[1],
        "terceiro": ordered[2],
        "quarto": ordered[3]
    }

def get_best_thirds(groups: list[dict]) -> list[dict]:
    """Coleta os terceiros colocados de todos os grupos e retorna os 8 melhores."""
    thirds = [group["terceiro"] for group in groups]
    thirds_dict = {team["id"]: team for team in thirds}
    return order_teams(thirds_dict)[:8]

def order_teams(teams: dict, games: list[dict] = None) -> list:
    """Ordena os times seguindo as regras de desempate do mundial (excluindo critério disciplinar)."""
    teams_list = list(teams.values())
    
    # 1. Identificar grupos de times empatados por pontos
    from collections import defaultdict
    by_points = defaultdict(list)
    for team in teams_list:
        by_points[team["pontos"]].append(team["id"])
        
    # Calcular as estatísticas de confronto direto (H2H) se houver empate
    h2h_stats = {}
    for team_id in teams:
        team_pts = teams[team_id]["pontos"]
        tied_team_ids = by_points[team_pts]
        
        h2h_pts = 0
        h2h_goals_scored = 0
        h2h_goals_conceded = 0
        
        # Só calcula H2H se houver mais de um time empatado com a mesma pontuação
        if len(tied_team_ids) > 1 and games:
            for game in games:
                h, a = game["home"], game["away"]
                hg, ag = game["home_goals"], game["away_goals"]
                
                # Se o jogo envolveu duas equipes do subgrupo de empatados
                if h in tied_team_ids and a in tied_team_ids:
                    if h == team_id:
                        h2h_goals_scored += hg
                        h2h_goals_conceded += ag
                        if hg > ag:
                            h2h_pts += 3
                        elif hg == ag:
                            h2h_pts += 1
                    elif a == team_id:
                        h2h_goals_scored += ag
                        h2h_goals_conceded += hg
                        if ag > hg:
                            h2h_pts += 3
                        elif hg == ag:
                            h2h_pts += 1
                            
        h2h_stats[team_id] = {
            "h2h_pts": h2h_pts,
            "h2h_gd": h2h_goals_scored - h2h_goals_conceded,
            "h2h_gs": h2h_goals_scored
        }

    def get_sort_key(team):
        tid = team["id"]
        stats = h2h_stats[tid]
        rating = TEAMS.get(tid, {}).get("rating", 0)
        
        # Retorna tupla de ordenação:
        # 1. Pontos totais
        # 2. Pontos no confronto direto
        # 3. Saldo de gols no confronto direto
        # 4. Gols marcados no confronto direto
        # 5. Saldo de gols geral
        # 6. Gols marcados geral
        # 7. Rating FIFA
        return (
            team["pontos"],
            stats["h2h_pts"],
            stats["h2h_gd"],
            stats["h2h_gs"],
            team["gols_marcados"] - team["gols_sofridos"],
            team["gols_marcados"],
            rating
        )
        
    return sorted(teams_list, key=get_sort_key, reverse=True)

def build_table(games: list[dict]) -> dict[int, dict]:
    """Gera a tabela de pontos e gols sem criar estruturas de dados inúteis em memória."""
    table = {}
    for game in games:
        h, a = game["home"], game["away"]
        hg, ag = game["home_goals"], game["away_goals"]

        # Inicialização rápida
        if h not in table: table[h] = {"id": h, "pontos": 0, "gols_marcados": 0, "gols_sofridos": 0}
        if a not in table: table[a] = {"id": a, "pontos": 0, "gols_marcados": 0, "gols_sofridos": 0}

        # Computa gols
        table[h]["gols_marcados"] += hg
        table[h]["gols_sofridos"] += ag
        table[a]["gols_marcados"] += ag
        table[a]["gols_sofridos"] += hg

        # Computa pontos
        if hg > ag:
            table[h]["pontos"] += 3
        elif ag > hg:
            table[a]["pontos"] += 3
        else:
            table[h]["pontos"] += 1
            table[a]["pontos"] += 1

    return table