import sys

def show(summary: dict) -> None:
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


