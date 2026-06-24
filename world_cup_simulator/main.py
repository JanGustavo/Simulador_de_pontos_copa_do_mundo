"""Application orchestrator: wires models, engine, stats, and UI."""

import sys
from engine.simulator import run_simulation
from ui.display import show

# Detecta se está sendo executado no contexto do Streamlit usando a API oficial
is_streamlit = False
try:
    from streamlit.runtime import exists
    is_streamlit = exists()
except ImportError:
    pass

if is_streamlit:
    import streamlit as st
    from models.match_model import MatchModel

    # Configuração de página
    st.set_page_config(page_title="Simulador de Copa do Mundo", page_icon="🏆", layout="centered")
    
    st.title("🏆 Simulador da Copa do Mundo (48 Seleções)")
    st.markdown("""
    Este simulador utiliza o método de **Monte Carlo** para simular milhares de torneios da Copa do Mundo.
    Ele calcula a probabilidade estatística de classificação com base nos pontos conquistados.
    """)

    # Painel de controle lateral
    st.sidebar.header("⚙️ Configurações")
    
    iterations = st.sidebar.number_input(
        "Número de Iterações",
        min_value=1_000,
        max_value=1_000_000,
        value=10_000,
        step=5_000,
        help="Quantidade de copas simuladas. Mais iterações aumentam a precisão estatística, mas também o tempo de execução."
    )
    
    weight_factor = st.sidebar.slider(
        "Fator de Força (Weight Factor)",
        min_value=0.0,
        max_value=2.0,
        value=0.0,
        step=0.1,
        help="0.0 = Totalmente sem pesos (ortogonal). Valores maiores aumentam a vantagem dos times mais fortes."
    )

    # Informações dinâmicas sobre o modelo
    if weight_factor == 0.0:
        st.sidebar.info("💡 **Modelo Sem Pesos (Ortogonal)** ativo. Todas as partidas são perfeitamente simétricas.")
    else:
        st.sidebar.success(f"🔥 **Modelo Ponderado** ativo (fator = {weight_factor:.1f}). A força dos times influenciará os gols.")

    # Botão para disparar a simulação
    if st.sidebar.button("🚀 Iniciar Simulação", use_container_width=True):
        with st.spinner("Simulando os torneios..."):
            import time
            start = time.perf_counter()
            model = MatchModel(weight_factor=weight_factor)
            summary, team_summary = run_simulation(iterations=iterations, model=model)
            elapsed = time.perf_counter() - start
            
            st.session_state["simulation_summary"] = summary
            st.session_state["simulation_team_summary"] = team_summary
            st.session_state["simulation_time"] = elapsed
            st.session_state["simulation_iterations"] = iterations
            st.toast("Simulação concluída com sucesso!", icon="✅")

    # Exibe os resultados obtidos
    if "simulation_summary" in st.session_state:
        st.success(f"⚡ Simulação de {st.session_state['simulation_iterations']:,} copas concluída em **{st.session_state['simulation_time']:.3f} segundos**!")
        show(st.session_state["simulation_summary"], st.session_state.get("simulation_team_summary"))
    else:
        st.info("👈 Ajuste os parâmetros na barra lateral e clique em **Iniciar Simulação**.")

else:
    # Fallback CLI padrão
    iteracoes = 10000
    
    def main() -> None:
        import time
        from models.match_model import MatchModel
        
        start = time.perf_counter()
        # No CLI padrão, assumimos modelo ponderado com fator 1.0 (ou 0.0 se quiser simétrico)
        model = MatchModel(weight_factor=1.0)
        summary, team_summary = run_simulation(iterations=iteracoes, model=model)
        elapsed = time.perf_counter() - start
        
        show(summary, team_summary)
        print(f"\n⚡ Simulação de {iteracoes:,} copas concluída em {elapsed:.3f} segundos!")

    if __name__ == "__main__":
        main()  