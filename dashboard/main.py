# dashboard/main.py
# Entry point del dashboard modular
# Español / English: Punto de entrada principal del dashboard / Main dashboard entry point

import streamlit as st
from dashboard.data_loader import load_data
from dashboard.filters import filtrar_df
from dashboard.components.overview import render_overview
from dashboard.components.department_tab import render_department_tab
from dashboard.components.temporal_tab import render_temporal_tab
from dashboard.components.integrity_tab import render_integridad_tab
from dashboard.components.pdf_generator import create_pdf

def run_dashboard():
    """Función principal que ejecuta el dashboard.
    ---
    Main function that runs the dashboard.
    """
    st.set_page_config(
        page_title="Sentinel - Verificación Independiente CNE",
        page_icon="🇭🇳",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Carga datos
    df_raw = load_data()

    # Sidebar
    with st.sidebar:
        st.title("Sentinel 🇭🇳")
        st.markdown("**Monitoreo neutral de datos públicos del CNE**")
        st.caption("Solo hechos objetivos • Open-source")

        modo_simple = st.toggle("Modo Simple (solo resumen básico)", value=False)

        deptos_opts = ['Todos'] + sorted(df_raw['departamento'].unique())
        deptos_sel = st.multiselect("Departamentos", deptos_opts, default=['Todos'])

        partidos_opts = df_raw.columns.drop(['timestamp', 'departamento', 'total_votos', 'hash']).tolist()
        partidos_sel = st.multiselect("Partidos/Candidatos", partidos_opts, default=partidos_opts[:3])

        min_date = df_raw['timestamp'].min().date()
        max_date = df_raw['timestamp'].max().date()
        date_range = st.date_input("Rango de fechas", (min_date, max_date), min_value=min_date, max_value=max_date)

    # Filtrado
    df = filtrar_df(df_raw, deptos_sel, partidos_sel, date_range)

    if df.empty:
        st.warning("No hay datos en el rango seleccionado. Ajusta los filtros.")
        return

    # Siempre visible: Resumen básico
    render_overview(df, partidos_sel)

    if not modo_simple:
        tab1, tab2, tab3 = st.tabs(["📍 Por Departamento", "⏳ Evolución", "🔐 Integridad y Benford"])

        with tab1:
            render_department_tab(df, partidos_sel)

        with tab2:
            render_temporal_tab(df, partidos_sel)

        with tab3:
            render_integridad_tab(df)

    # Botón PDF (fix: mime explícito + seek(0) doble chequeo)
    if st.button("📄 Descargar análisis como PDF"):
        pdf_bytes = create_pdf(df, deptos_sel, date_range, partidos_sel)
        st.download_button(
            label="Descargar PDF ahora",
            data=pdf_bytes,
            file_name=f"sentinel_analisis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"  # Forzado para evitar inferencia fallida
        )

    # Footer
    st.markdown("---")
    st.markdown("**Sentinel** • Proyecto independiente • Open-source • [GitHub](https://github.com/userf8a2c4/sentinel)")
    st.caption("Datos públicos del CNE • Sin interpretación política • Monitoreo continuo")
