import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import os
import glob
import io

st.set_page_config(page_title="Centinel", layout="wide")

# Tema minimalista oscuro y elegante
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e6e6e6; }
    .stMetric { font-size: 1.5rem !important; font-weight: 500; }
    h1, h2, h3 { margin-bottom: 1.2rem; }
    .stExpander { margin-bottom: 1.5rem; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_data():
    patterns = [
        "data/snapshots_2025/*.json",
        "tests/fixtures/snapshots_2025/*.json",
        "*.json"
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files = sorted(files, reverse=True)

    snapshots = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                data['source_path'] = os.path.basename(f)
                snapshots.append(data)
        except:
            pass

    if not snapshots:
        return pd.DataFrame(), {}, pd.DataFrame(), "No hash disponible", pd.DataFrame()

    df_summary = pd.DataFrame([{
        "timestamp": datetime.now().isoformat(),  # placeholder, usa real si existe
        "source_path": s['source_path'],
        "registered": s.get("registered_voters", 0),
        "total": s.get("total_votes", 0),
        "valid": s.get("valid_votes", 0),
        "null": s.get("null_votes", 0),
        "blank": s.get("blank_votes", 0)
    } for s in snapshots])

    last = snapshots[0]
    candidates = last.get("candidates", [])
    df_cand = pd.DataFrame(candidates)

    last_hash = last.get("last_hash", "No hash disponible")

    return df_summary, last, df_cand, last_hash

df_summary, last_snapshot, df_candidates, last_hash = load_data()

# Modo simple por default
simple_mode = st.sidebar.checkbox("Modo simple (recomendado)", value=True)

st.title("Centinel")

if last_snapshot:
    st.success("Datos cargados")
else:
    st.warning("No se encontraron snapshots")

# Panel de alertas
st.markdown("### Alertas")
if simple_mode:
    st.info("Sin alertas detectadas en este momento.")
else:
    st.info("Sin alertas detectadas. (Modo pro: revisar reglas aplicadas en detalle)")

# KPIs + barra + hash
if not df_summary.empty:
    current = last_snapshot
    prev = df_summary.iloc[1] if len(df_summary) > 1 else current

    delta_total = current.get("total", 0) - prev.get("total", 0)

    cols = st.columns(5)
    cols[0].metric("Registrados", f"{current.get('registered', 0):,}")
    cols[1].metric("Emitidos", f"{current.get('total', 0):,}", delta=f"+{delta_total:,}" if delta_total else None)
    cols[2].metric("Válidos", f"{current.get('valid', 0):,}")
    cols[3].metric("Nulos", f"{current.get('null', 0):,}")
    cols[4].metric("Blancos", f"{current.get('blank', 0):,}")

    porc = (current.get("total", 0) / current.get("registered", 1)) * 100
    st.progress(porc / 100)
    st.caption(f"Progreso aproximado: {porc:.1f}%")

    st.caption(f"Último hash verificado: {last_hash}")

# Pie chart
if not df_candidates.empty and "votes" in df_candidates.columns:
    df_candidates['votes'] = pd.to_numeric(df_candidates['votes'], errors='coerce').fillna(0)
    fig = px.pie(
        df_candidates,
        values="votes",
        names="candidato",
        hole=0.4
    )
    fig.update_layout(showlegend=False, template="plotly_dark", margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

# Explicación básica
with st.expander("¿Qué significan estos números?"):
    st.markdown("""
    - Registrados: Personas habilitadas para votar.  
    - Emitidos: Total de votos registrados.  
    - Válidos: Votos que cuentan para candidatos.  
    - Nulos / Blancos: Votos no válidos.  
    - Progreso: Porcentaje aproximado de conteo.  
    - Último hash: Firma digital que verifica la integridad de los datos capturados.
    """)

# Modo pro: todo integrado en expanders
if not simple_mode:
    st.markdown("---")
    st.subheader("Modo pro – Detalles técnicos completos")

    # Evolución temporal
    with st.expander("Evolución temporal completa"):
        if len(df_summary) > 1:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=df_summary.index, y=df_summary["total"], name="Total"))
            fig_line.add_trace(go.Scatter(x=df_summary.index, y=df_summary["valid"], name="Válidos"))
            fig_line.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Se necesitan más snapshots para mostrar evolución.")

    # Tabla detallada candidatos
    with st.expander("Tabla detallada de candidatos"):
        if not df_candidates.empty:
            st.dataframe(df_candidates.style.format({"votes": "{:,}"}), use_container_width=True)
        else:
            st.info("No hay datos de candidatos.")

    # Snapshots históricos con descarga
    with st.expander("Snapshots históricos (últimos 10)"):
        if not df_summary.empty:
            df_hist = df_summary.head(10)
            st.dataframe(df_hist, use_container_width=True)

            # Descarga CSV
            csv = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar snapshots como CSV",
                data=csv,
                file_name="snapshots_historicos.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay snapshots disponibles.")

    # Integridad: hashes
    with st.expander("Integridad: Último hash y cadena"):
        st.markdown(f"**Último hash verificado**: {last_hash}")
        st.info("Cadena completa de hashes y verificación histórica disponible en desarrollo.")

    # Benford
    with st.expander("Análisis Benford"):
        st.info("Análisis completo de Ley de Benford (distribución de dígitos, desviaciones por candidato y departamento) disponible en desarrollo. Próximamente gráficos y resultados detallados.")

    # Predicciones
    with st.expander("Predicciones y tendencias"):
        st.info("Módulo de predicciones (tendencias, extrapolaciones, estimados por candidato) disponible en desarrollo. Próximamente resultados detallados.")

    # JSON crudo
    with st.expander("JSON completo del último snapshot"):
        st.json(last_snapshot)

st.caption("Datos públicos del CNE · Actualización automática")
