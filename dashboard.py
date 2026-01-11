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
    page_icon="📡",
    layout="wide"
)

# Tema oscuro
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .metric-delta { font-size: 1.2rem !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CARGAR SNAPSHOTS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_snapshots():
    # Diagnóstico visible
    patterns = [
        "data/snapshots_2025/*.json",
        "tests/fixtures/snapshots_2025/*.json",
        "*.json"
    ]
    
    snapshot_files = []
    for pattern in patterns:
        snapshot_files.extend(glob.glob(pattern))
    
    snapshot_files = sorted(snapshot_files, reverse=True)
    
    # Mostrar diagnóstico
    st.write("**Diagnóstico de carga:**")
    st.write(f"Rutas buscadas: {patterns}")
    st.write(f"Archivos JSON encontrados: {len(snapshot_files)}")
    if snapshot_files:
        st.write("Nombres:", [os.path.basename(f) for f in snapshot_files[:5]])
    else:
        st.error("¡Ningún archivo .json encontrado! Verifica el repositorio en GitHub y las carpetas.")
    
    snapshots = []
    for file_path in snapshot_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['source_path'] = os.path.basename(file_path)
                snapshots.append(data)
        except Exception as e:
            st.warning(f"Error cargando {os.path.basename(file_path)}: {e}")
    
    st.write(f"Snapshots cargados correctamente: {len(snapshots)}")
    
    if not snapshots:
        return pd.DataFrame(), {}, pd.DataFrame()
    
    # Crear resumen seguro
    summary_data = []
    for s in snapshots:
        if "estadisticas" not in s:
            continue
        distrib = s["estadisticas"].get("distribucion_votos", {})
        totaliz = s["estadisticas"].get("totalizacion_actas", {})
        
        try:
            validos = int(distrib.get("validos", "0").replace(",", ""))
            nulos = int(distrib.get("nulos", "0").replace(",", ""))
            blancos = int(distrib.get("blancos", "0").replace(",", ""))
        except:
            validos = nulos = blancos = 0
        
        summary_data.append({
            "source_path": s.get("source_path", "unknown"),
            "actas_divulgadas": totaliz.get("actas_divulgadas", "N/A"),
            "validos": validos,
            "nulos": nulos,
            "blancos": blancos
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Extracción de timestamp robusta
    def extract_ts(filename):
        pattern = r'(\d{4}-\d{2}-\d{2})[\s_-]*(\d{2})[_\-\:]*(\d{2})[_\-\:]*(\d{2})'
        match = re.search(pattern, filename)
        if match:
            ymd, h, m, s = match.groups()
            try:
                return pd.to_datetime(f"{ymd} {h}:{m}:{s}")
            except:
                return pd.NaT
        return pd.NaT
    
    if not df_summary.empty:
        df_summary['timestamp'] = df_summary['source_path'].apply(extract_ts)
        
        # Fallback si no se pudo extraer ninguno
        if df_summary['timestamp'].isna().all():
            df_summary['timestamp'] = pd.date_range(
                end=datetime.now(), periods=len(df_summary), freq='-15min'
            )[::-1]
        
        df_summary = df_summary.sort_values('timestamp', ascending=False, na_position='last')
    else:
        df_summary['timestamp'] = pd.NaT
    
    # Último snapshot y candidatos
    last_snapshot = snapshots[0] if snapshots else {}
    resultados = last_snapshot.get("resultados", [])
    df_candidates = pd.DataFrame(resultados)
    if not df_candidates.empty:
        try:
            df_candidates['votos_num'] = df_candidates['votos'].str.replace(",", "").astype(int)
            df_candidates = df_candidates.sort_values('votos_num', ascending=False)
        except:
            pass  # Si falla la conversión, mantener como string
    
    return df_summary, last_snapshot, df_candidates

# Cargar datos
df_snapshots, last_snapshot, df_candidates = load_snapshots()

# ──────────────────────────────────────────────────────────────────────────────
# INTERFAZ
# ──────────────────────────────────────────────────────────────────────────────
st.title("📡 Centinel - Auditoría Electoral 2025")
st.markdown("Monitoreo neutral • Datos públicos CNE • Elecciones Honduras 30N 2025")

if last_snapshot:
    st.success(f"✓ Datos cargados • Actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("No hay snapshots válidos. Revisa el diagnóstico arriba.")

# Panorama General
st.subheader("Panorama General")
if not df_snapshots.empty:
    current = last_snapshot.get("estadisticas", {})
    distrib = current.get("distribucion_votos", {})
    totaliz = current.get("totalizacion_actas", {})
    
    cols = st.columns(4)
    cols[0].metric("Actas Divulgadas", totaliz.get("actas_divulgadas", "N/A"))
    cols[1].metric("Votos Válidos", f"{distrib.get('validos', '0'):,}")
    cols[2].metric("Votos Nulos", f"{distrib.get('nulos', '0'):,}")
    cols[3].metric("Votos Blancos", f"{distrib.get('blancos', '0'):,}")
    
    actas_t = int(totaliz.get("actas_totales", 1))
    actas_d = int(totaliz.get("actas_divulgadas", 0))
    porc = (actas_d / actas_t) * 100 if actas_t > 0 else 0
    st.progress(porc / 100)
    st.caption(f"Progreso: **{porc:.1f}%** ({actas_d:,} de {actas_t:,} actas)")

# Distribución
st.subheader("Distribución de Votos Válidos")
if not df_candidates.empty:
    fig = px.pie(
        df_candidates,
        values="votos_num" if "votos_num" in df_candidates else "votos",
        names="candidato",
        hover_data=["partido", "porcentaje"],
        hole=0.35
    )
    fig.update_layout(template="plotly_dark", height=550)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de candidatos en el último snapshot.")

# Tabla candidatos
if not df_candidates.empty:
    st.subheader("Resultados por Candidato")
    cols_show = [c for c in ["candidato", "partido", "votos", "porcentaje"] if c in df_candidates.columns]
    st.dataframe(df_candidates[cols_show], use_container_width=True)

# JSON
with st.expander("JSON completo del último snapshot"):
    st.json(last_snapshot)

st.markdown("---")
st.caption("Sentinel Project • Open Source • 🇭🇳")
