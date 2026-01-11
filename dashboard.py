import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import glob

# Configuración de página
st.set_page_config(
    page_title="Centinel Dashboard",
    page_icon="📡",
    layout="wide"
)

# Tema oscuro básico
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-delta { font-size: 1.1rem !important; }
    </style>
""", unsafe_allow_html=True)

# Cargar snapshots desde GitHub/local (tu lógica original adaptada)
@st.cache_data(ttl=300)
def load_data():
    # Buscar en las carpetas típicas
    snapshot_files = glob.glob("tests/fixtures/snapshots_2025/*.json") or \
                     glob.glob("data/snapshots_2025/*.json") or \
                     glob.glob("*.json")
    
    if not snapshot_files:
        st.error("No se encontraron snapshots JSON.")
        return pd.DataFrame(), {}, pd.DataFrame()
    
    snapshot_files = sorted(snapshot_files)  # cronológico ascendente
    
    snapshots = []
    for file_path in snapshot_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source_path'] = os.path.basename(file_path)
                # Intentar extraer timestamp del nombre si no existe
                if 'timestamp' not in data:
                    name = os.path.basename(file_path)
                    ts_str = name.split('snapshot_')[-1].split('.')[0].replace('_', ':')
                    try:
                        data['timestamp'] = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S').isoformat()
                    except:
                        data['timestamp'] = datetime.now().isoformat()
                snapshots.append(data)
        except Exception as e:
            st.warning(f"Error cargando {file_path}: {e}")
    
    if not snapshots:
        return pd.DataFrame(), {}, pd.DataFrame()
    
    # DataFrame de resúmenes
    df_snapshots = pd.DataFrame([{
        "timestamp": pd.to_datetime(s["timestamp"]),
        "registered_voters": s.get("registered_voters", 0),
        "total_votes": s.get("total_votes", 0),
        "valid_votes": s.get("valid_votes", 0),
        "null_votes": s.get("null_votes", 0),
        "blank_votes": s.get("blank_votes", 0),
        "source_path": s["source_path"]
    } for s in snapshots])
    
    df_snapshots = df_snapshots.sort_values("timestamp")
    
    last_snapshot = snapshots[-1]  # el más reciente
    
    # Candidatos dinámicos (de tu estructura real)
    candidates = last_snapshot.get("candidates", [])
    if not candidates:
        # Fallback si está dentro de otra clave (como en tus fixtures)
        candidates = last_snapshot.get("votos_blancos", {}).get("candidatos", [])
    
    df_candidates = pd.DataFrame(candidates)
    
    return df_snapshots, last_snapshot, df_candidates

df_snapshots, last_snapshot, df_candidates = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.title("📡 Centinel Dashboard")
st.markdown("Visualización automática de snapshots • Datos desde GitHub")

if last_snapshot:
    st.success(f"✓ Snapshot cargado: {last_snapshot.get('source_path', 'desconocido')}")
    st.caption(f"Última comprobación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.error("No hay datos disponibles.")

# ──────────────────────────────────────────────────────────────────────────────
# KPIs con DELTA y PORCENTAJE
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Panorama General")

if not df_snapshots.empty:
    current = last_snapshot
    prev = df_snapshots.iloc[-2] if len(df_snapshots) > 1 else current
    
    delta_emitidos = current.get("total_votes", 0) - prev.get("total_votes", 0)
    
    cols = st.columns(5)
    cols[0].metric("Registrados", f"{current.get('registered_voters', 0):,}")
    cols[1].metric("Votos Emitidos", f"{current.get('total_votes', 0):,}", 
                   delta=f"+{delta_emitidos:,}" if delta_emitidos else None)
    cols[2].metric("Votos Válidos", f"{current.get('valid_votes', 0):,}")
    cols[3].metric("Votos Nulos", f"{current.get('null_votes', 0):,}")
    cols[4].metric("Votos Blancos", f"{current.get('blank_votes', 0):,}")
    
    # Porcentaje de avance
    porc_avance = (current.get("total_votes", 0) / current.get("registered_voters", 1)) * 100
    st.progress(porc_avance / 100)
    st.caption(f"**Escrutinio aproximado: {porc_avance:.1f}%**")

# ──────────────────────────────────────────────────────────────────────────────
# PIE CHART DINÁMICO
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Distribución de Votos Válidos (Último Snapshot)")

if not df_candidates.empty:
    fig = px.pie(
        df_candidates,
        values="votes",
        names="candidato",
        hover_data=["partido"],
        title="Votos por Candidato",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend_title_text="Candidatos", template="plotly_dark")
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de candidatos en el último snapshot.")

# ──────────────────────────────────────────────────────────────────────────────
# Evolución temporal (tu gráfico original)
# ──────────────────────────────────────────────────────────────────────────────
st.subheader("Evolución Temporal")

if len(df_snapshots) > 1:
    fig_line = go.Figure()
    
    fig_line.add_trace(go.Scatter(
        x=df_snapshots["timestamp"],
        y=df_snapshots["total_votes"],
        mode='lines+markers',
        name='Total Votos'
    ))
    
    fig_line.add_trace(go.Scatter(
        x=df_snapshots["timestamp"],
        y=df_snapshots["valid_votes"],
        mode='lines+markers',
        name='Votos Válidos'
    ))
    
    fig_line.update_layout(
        xaxis_title="Fecha y Hora",
        yaxis_title="Votos",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_line, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABLAS (tu estructura original)
# ──────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Totales por Snapshot")
    if not df_snapshots.empty:
        st.dataframe(df_snapshots.style.format({
            "total_votes": "{:,}",
            "valid_votes": "{:,}"
        }), use_container_width=True)

with col_right:
    st.subheader("Último Snapshot - Candidatos")
    if not df_candidates.empty:
        st.dataframe(df_candidates, use_container_width=True)

# Explicaciones simples
with st.expander("¿Qué significan estos números?"):
    st.markdown("""
    - **Registrados**: Personas habilitadas para votar en el departamento.
    - **Votos Emitidos**: Total de personas que votaron.
    - **Votos Válidos**: Votos que cuentan para los candidatos.
    - **Votos Nulos / Blancos**: No cuentan para ningún candidato.
    - **Δ (delta)**: Cambio respecto al snapshot anterior (ej. +120 votos).
    - **Escrutinio %**: Porcentaje aproximado de votos contados.
    """)

# JSON raw (tu expander original)
with st.expander("Ver JSON del último snapshot"):
    st.json(last_snapshot)

st.caption("Powered by Streamlit • Datos desde GitHub • Actualización automática")
