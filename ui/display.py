import sys

def show(summary: dict, team_summary: list[dict] = None) -> None:
    # Verifica se o código está executando no contexto do Streamlit usando a API oficial
    is_streamlit = False
    try:
        from streamlit.runtime import exists
        is_streamlit = exists()
    except ImportError:
        pass

    if is_streamlit:
        import streamlit as st
        import pandas as pd
        
        # Cria abas para organizar o conteúdo de forma profissional
        if team_summary is not None:
            tab1, tab2 = st.tabs(["📊 Probabilidade por Pontos", "🌍 Probabilidade por Seleção"])
        else:
            tab1 = st.container()
            tab2 = None
            
        with tab1:
            st.subheader("📊 Estatísticas da Fase de Grupos")
            st.markdown("Probabilidade de classificação para o mata-mata com base nos pontos conquistados:")

            # Organiza dados em formato estruturado para o Streamlit (multiplicando a probabilidade por 100)
            data = []
            for pontos, dados in summary.items():
                data.append({
                    "Pontos": pontos,
                    "Aparições": dados["appearances"],
                    "Classificações": dados["classifications"],
                    "Probabilidade (%)": dados["probability"] * 100
                })
            
            df = pd.DataFrame(data)
            
            # Exibição da Tabela interativa formatada
            st.dataframe(
                df,
                column_config={
                    "Pontos": st.column_config.NumberColumn("Pontos", format="%d"),
                    "Aparições": st.column_config.NumberColumn("Aparições", format="%d"),
                    "Classificações": st.column_config.NumberColumn("Classificações", format="%d"),
                    "Probabilidade (%)": st.column_config.ProgressColumn(
                        "Probabilidade de Classificação",
                        help="Chance de passar de fase em porcentagem",
                        format="%.2f%%",
                        min_value=0.0,
                        max_value=100.0,
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

            # Exibição de Gráfico de Barras
            st.markdown("### 📈 Curva de Probabilidade por Pontos")
            st.bar_chart(
                df,
                x="Pontos",
                y="Probabilidade (%)",
                color="#2e7d32",
                use_container_width=True
            )
            
        if tab2 is not None:
            with tab2:
                st.subheader("🌍 Probabilidades Individuais das Seleções")
                st.markdown("Chances reais de cada país classificar para o mata-mata baseado em seu **Rating FIFA**:")
                
                df_teams = pd.DataFrame(team_summary)
                df_teams["Probabilidade (%)"] = df_teams["probability"] * 100
                
                # Exibição da Tabela interativa de seleções
                st.dataframe(
                    df_teams[["name", "rating", "Probabilidade (%)"]],
                    column_config={
                        "name": "Seleção",
                        "rating": st.column_config.NumberColumn("Rating FIFA", format="%d"),
                        "Probabilidade (%)": st.column_config.ProgressColumn(
                            "Probabilidade de Classificação",
                            help="Porcentagem de vezes que a seleção avançou de fase",
                            format="%.2f%%",
                            min_value=0.0,
                            max_value=100.0,
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                )
                
                st.markdown("### 🔝 Top 10 Seleções Favoritas")
                st.bar_chart(
                    df_teams.head(10),
                    x="name",
                    y="Probabilidade (%)",
                    color="#0f4c81",
                    use_container_width=True
                )
    else:
        # Cabeçalho com alinhamento e larguras fixas para o CLI
        header = f"{'Pontos':^6} | {'Aparições':^12} | {'Classificações':^16} | {'Probabilidade':^13}"
        divider = "-" * len(header)
        print(header)
        print(divider)
        for pontos, dados in summary.items():
            appearances = dados['appearances']
            classifications = dados['classifications']
            probability = dados['probability']
            print(f"{pontos:^6} | {appearances:>12,} | {classifications:>16,} | {probability:>13.2%}")
            
        if team_summary is not None:
            print("\n🌍 Top 10 Seleções mais propensas a classificar:")
            print(f"{'Seleção':<18} | {'Rating':^6} | {'Chance':^8}")
            print("-" * 38)
            for item in team_summary[:10]:
                print(f"{item['name']:<18} | {item['rating']:^6} | {item['probability']:>7.2%}")

def show_knockout(results: list[dict]) -> None:
    """Exibe os resultados da simulação do mata-mata no Streamlit ou CLI."""
    is_streamlit = False
    try:
        from streamlit.runtime import exists
        is_streamlit = exists()
    except ImportError:
        pass

    if is_streamlit:
        import streamlit as st
        import pandas as pd
        
        st.subheader("🏆 Probabilidade de Avanço no Mata-Mata")
        st.markdown("Chances estatísticas de cada seleção alcançar cada fase e vencer o torneio:")
        
        df = pd.DataFrame(results)
        # Multiplicar por 100 para exibição em porcentagem
        df["Oitavas (%)"] = df["oitavas"] * 100
        df["Quartas (%)"] = df["quartas"] * 100
        df["Semis (%)"] = df["semis"] * 100
        df["Final (%)"] = df["final"] * 100
        df["Campeão (%)"] = df["campeao"] * 100
        
        st.dataframe(
            df[["name", "rating", "Oitavas (%)", "Quartas (%)", "Semis (%)", "Final (%)", "Campeão (%)"]],
            column_config={
                "name": "Seleção",
                "rating": st.column_config.NumberColumn("Rating FIFA", format="%d"),
                "Oitavas (%)": st.column_config.NumberColumn("Oitavas", format="%.2f%%"),
                "Quartas (%)": st.column_config.NumberColumn("Quartas", format="%.2f%%"),
                "Semis (%)": st.column_config.NumberColumn("Semis", format="%.2f%%"),
                "Final (%)": st.column_config.NumberColumn("Final", format="%.2f%%"),
                "Campeão (%)": st.column_config.ProgressColumn(
                    "Campeão",
                    help="Chance de ganhar a Copa do Mundo",
                    format="%.2f%%",
                    min_value=0.0,
                    max_value=100.0,
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        
        st.markdown("### 🥇 Top 10 Seleções com Maior Chance de Título")
        st.bar_chart(
            df.head(10),
            x="name",
            y="Campeão (%)",
            color="#d4af37", # Dourado para o campeão
            use_container_width=True
        )
        
    else:
        # Saída padrão CLI
        header = f"{'Seleção':<18} | {'Rating':^6} | {'Oitavas':^8} | {'Quartas':^8} | {'Semis':^8} | {'Final':^8} | {'Campeão':^8}"
        divider = "-" * len(header)
        print(header)
        print(divider)
        for r in results[:15]:
            print(f"{r['name']:<18} | {r['rating']:^6} | {r['oitavas']:>7.2%} | {r['quartas']:>7.2%} | {r['semis']:>7.2%} | {r['final']:>7.2%} | {r['campeao']:>7.2%}")
        if len(results) > 15:
            print(f"... e mais {len(results) - 15} seleções.")
