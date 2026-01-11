import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import os
import glob
import re

# Configuración de página
st.set_page_config(
    page_title="Centinel - Auditoría Electoral Honduras 2025",
    page_icon="",
    layout="wide"
)

# Tema oscuro básico
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-delta { font-size: 1.2rem !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CARGAR TODOS LOS SNAPSHOTS REALES
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_snapshots():
    patterns = [
        "data/snapshots_2025/*.json",
        "tests/fixtures/snapshots_2025/*.json",
        "*.json"  # fallback
    ]
    
    snapshot_files = []
    for pattern in patterns:
        snapshot_files.extend(glob.glob(pattern))
    
    snapshot_files = sorted(snapshot_files, reverse=True)  # más reciente primero
    
    if not snapshot_files:
        st.error("No se encontraron archivos JSON en las carpetas esperadas.")
        return pd.DataFrame(), {}, pd.DataFrame()
    
    snapshots = []
    for file_path in snapshot_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source_path'] = os.path.basename(file_path)
                snapshots.append(data)
        except Exception as e:
            st.warning(f"Error cargando {file_path}: {e}")
    
    if not snapshots:
        return pd.DataFrame(), {}, pd.DataFrame()
    
    # Crear DataFrame resumen
    df_summary = pd.DataFrame([{
        "source_path": s.get("source_path", ""),
        "actas_divulgadas": s.get("estadisticas", {})
                               .get("totalizacion_actas", {})
                               .get("actas_divulgadas", "N/A"),
        "validos": int(s.get("estadisticas", {})
                          .get("distribucion_votos", {})
                          .get("validos", "0").replace(",", "")),
        "nulos": int(s.get("estadisticas", {})
                        .get("distribucion_votos", {})
                        .get("nulos", "0").replace(",", "")),
        "blancos": int(s.get("estadisticas", {})
                          .get("distribucion_votos", {})
                          .get("blancos", "0").replace(",", ""))
    } for s in snapshots if "estadisticas" in s])
    
    # ── OPCIÓN A: Extracción robusta de timestamp desde el nombre del archivo ──
    def extract_timestamp_from_filename(filename):
        # Busca patrones como: 2025-12-03 21_00_11, 2025-12-03_21-00-11, etc.
        pattern = r'(\d{4}-\d{2}-\d{2})[\s_-]*(\d{2})[_:-]?(\d{2})[_:-]?(\d{2})'
        match = re.search(pattern, filename)
        if match:
            year_month_day, hour, minute, second = match.groups()
            time_str = f"{hour}:{minute}:{second}"
            full_datetime_str = f"{year_month_day} {time_str}"
            try:
                return pd.to_datetime(full_datetime_str)
            except:
                return pd.NaT
        return pd.NaT
    
    df_summary['timestamp'] = df_summary['source_path'].apply(extract_timestamp_from_filename)
    
    # Si no se pudo extraer ninguno, usar placeholder
    if df_summary['timestamp'].isna().all():
        df_summary['timestamp'] = pd.date_range(
            end=datetime.now(), periods=len(df_summary), freq='-15min'
        )[::-1]  # orden descendente
    
    # Ordenar por timestamp (maneja NaT al final)
    df_summary = df_summary.sort_values('timestamp', ascending=False, na_position='last')
    
    # Último snapshot (el más reciente)
    last_snapshot = snapshots[0]
    
    # Candidatos dinámicos
    resultados = last_snapshot.get("resultados", [])
    df_candidates = pd.DataFrame(resultados)
    if not df_candidates.empty:
        df_candidates['votos_num'] = df_candidates['votos'].str.replace(",", "").astype(int)
        df_candidates = df_candidates.sort_values('votos_num', ascending=False)
    
    return df_summary, last_snapshot, df_candidates

# Carga de datos
df_snapshots, last_snapshot, df_candidates = load_snapshots()

# ──────────────────────────────────────────────────────────────────────────────
# INTERFAZ DEL DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
st.title("📡 Centinel - Auditoría Electoral 2025")
st.markdown("Monitoreo neutral y automático • Datos públicos del CNE • Elecciones 30N 2025")

if last_snapshot:
    st.success(f"✓ Snapshot cargado • Actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption(f"Archivo: {last_snapshot.get('source_path', '—')}")
else:
    st.error("No hay datos válidos disponibles.")

# KPIs
st.subheader("Panorama General")
if not df_snapshots.empty:
    current_stats = last_snapshot.get("estadisticas", {})
    distrib = current_stats.get("distribucion_votos", {})
    totalizacion = current_stats.get("totalizacion_actas", {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Actas Divulgadas", totalizacion.get("actas_divulgadas", "N/A"))
    col2.metric("Votos Válidos", f"{distrib.get('validos', '0'):,}")
    col3.metric("Votos Nulos", f"{distrib.get('nulos', '0'):,}")
    col4.metric("Votos Blancos", f"{distrib.get('blancos', '0'):,}")
    
    actas_total = int(totalizacion.get("actas_totales", 1))
    actas_div = int(totalizacion.get("actas_divulgadas", 0))
    porc = (actas_div / actas_total) * 100 if actas_total > 0 else 0
    st.progress(porc / 100)
    st.caption(f"Progreso de totalización: **{porc:.1f}%**")

# Pie Chart
st.subheader("Distribución de Votos Válidos")
if not df_candidates.empty:
    fig = px.pie(
        df_candidates,
        values="votos_num",
        names="candidato",
        hover_data=["partido", "porcentaje"],
        hole=0.35
    )
    fig.update_layout(template="plotly_dark", height=550)
    st.plotly_chart(fig, use_container_width=True)

# Tabla de candidatos
if not df_candidates.empty:
    st.subheader("Resultados por Candidato")
    st.dataframe(
        df_candidates[["candidato", "partido", "votos", "porcentaje"]],
        use_container_width=True
    )

# JSON raw
with st.expander("Ver JSON completo del último snapshot"):
    st.json(last_snapshot)

st.markdown("---")
st.caption("Sentinel Project • 🇭🇳 • Open Source • Actualización automática")
