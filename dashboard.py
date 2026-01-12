# dashboard.py
# Sentinel - Dashboard Interactivo de Verificación Independiente CNE
# Iteración pulida - Enero 2026
# Ejecutar: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import hashlib

# Configuración de página
st.set_page_config(
    page_title="Sentinel - Verificación Independiente CNE",
    page_icon="🇭🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS (simulación realista - REEMPLAZA con tu loader real)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)  # Cache 30 min
def load_data():
    # Simulación de snapshots CNE (reemplaza con pd.read_json o tu scraper)
    timestamps = pd.date_range('2025-11-30 18:00', '2025-12-01 06:00', freq='15min')
    deptos = ['Cortés', 'Francisco Morazán', 'Atlántida', 'Comayagua', 'Choluteca']
    partidos = ['Libre', 'Nacional', 'PSH', 'Otros']
    
    data = []
    for ts in timestamps:
        for depto in deptos:
            total = np.random.randint(8000, 60000)
            votos = np.random.multinomial(total, [0.42, 0.36, 0.15, 0.07])
            hash_val = hashlib.sha256(f"{ts}_{depto}_{votos}".encode()).hexdigest()
            data.append({
                'timestamp': ts,
                'departamento': depto,
                'total_votos': total,
                **{p: v for p, v in zip(partidos, votos)},
                'hash': hash_val
            })
    return pd.DataFrame(data)

df_raw = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR - Controles principales
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Sentinel 🇭🇳")
    st.markdown("**Monitoreo neutral de datos públicos del CNE**")
    st.caption("Solo hechos objetivos • Open-source")

    modo_simple = st.toggle("Modo Simple (resumen básico)", value=False)

    st.subheader("Filtros")
    deptos_opts = ['Todos'] + sorted(df_raw['departamento'].unique())
    deptos_sel = st.multiselect("Departamentos", deptos_opts, default=['Todos'])

    partidos_opts = df_raw.columns.drop(['timestamp', 'departamento', 'total_votos', 'hash']).tolist()
    partidos_sel = st.multiselect("Partidos/Candidatos", partidos_opts, default=partidos_opts[:3])

    min_date = df_raw['timestamp'].min().date()
    max_date = df_raw['timestamp'].max().date()
    date_range = st.date_input("Rango de fechas", (min_date, max_date), min_value=min_date, max_value=max_date)

# ──────────────────────────────────────────────────────────────────────────────
# FILTRADO
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def filtrar(df, deptos, partidos, dates):
    df_f = df.copy()
    if 'Todos' not in deptos:
        df_f = df_f[df_f['departamento'].isin(deptos)]
    df_f = df_f[(df_f['timestamp'].dt.date >= dates[0]) & (df_f['timestamp'].dt.date <= dates[1])]
    return df_f

df = filtrar(df_raw, deptos_sel, partidos_sel, date_range)

# ──────────────────────────────────────────────────────────────────────────────
# BENFORD REAL (primer dígito)
# ──────────────────────────────────────────────────────────────────────────────
def benford_analysis(series):
    if len(series) < 20:
        return None, None, None
    primeros = series.astype(str).str[0].astype(int)
    primeros = primeros[(primeros >= 1) & (primeros <= 9)]
    if len(primeros) < 10:
        return None, None, None
    obs = primeros.value_counts(normalize=True).sort_index().reindex(range(1,10), fill_value=0)
    teor = pd.Series([np.log10(1 + 1/d) for d in range(1,10)], index=range(1,10))
    desviacion = np.mean(np.abs(obs - teor)) * 100
    return obs, teor, desviacion

# ──────────────────────────────────────────────────────────────────────────────
# CONTENIDO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
if df.empty:
    st.warning("No hay datos en el rango seleccionado. Ajusta filtros.")
else:
    # Resumen básico siempre visible
    st.header("Resumen Nacional (Último Snapshot)")
    ultimo = df.iloc[-1]
    cols = st.columns(len(partidos_sel) + 1)
    cols[0].metric("Total Votos", f"{ultimo['total_votos']:,}")
    for i, p in enumerate(partidos_sel, 1):
        v = ultimo[p]
        porc = v / ultimo['total_votos'] * 100 if ultimo['total_votos'] > 0 else 0
        cols[i].metric(p, f"{v:,}", f"{porc:.1f}%")

    if not modo_simple:
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["📍 Por Departamento", "⏳ Evolución", "🔐 Integridad"])

        with tab1:
            df_depto = df.groupby('departamento')[['total_votos'] + partidos_sel].last().reset_index()
            st.dataframe(df_depto.style.format({c: "{:,}" for c in df_depto.columns if c != 'departamento'}))
            fig = px.bar(df_depto.melt(id_vars='departamento', value_vars=partidos_sel),
                         x='departamento', y='value', color='variable', barmode='group')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            df_melt = df.melt(id_vars='timestamp', value_vars=partidos_sel, var_name='Partido', value_name='Votos')
            fig_line = px.line(df_melt, x='timestamp', y='Votos', color='Partido')
            st.plotly_chart(fig_line, use_container_width=True)

        with tab3:
            st.subheader("Cadena de Hashes (últimos 5)")
            for h in df['hash'].tail(5):
                st.code(h)

            st.subheader("Ley de Benford")
            obs, teor, desv = benford_analysis(df['total_votos'])
            if obs is not None:
                fig_b = go.Figure()
                fig_b.add_trace(go.Bar(x=list(range(1,10)), y=obs, name='Observado'))
                fig_b.add_trace(go.Scatter(x=list(range(1,10)), y=teor, mode='lines+markers', name='Benford'))
                fig_b.update_layout(title=f"Desviación: {desv:.2f}%")
                st.plotly_chart(fig_b, use_container_width=True)
                if desv > 5:
                    st.error(f"⚠️ Posible anomalía (desviación {desv:.2f}%)")
                else:
                    st.success(f"✅ Dentro de lo esperado ({desv:.2f}%)")
            else:
                st.info("Datos insuficientes para Benford")

# ──────────────────────────────────────────────────────────────────────────────
# PDF EXPORT
# ──────────────────────────────────────────────────────────────────────────────
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Análisis Personalizado - Sentinel", ln=1, align='C')
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.ln(5)
    
    pdf.cell(0, 8, f"Rango: {date_range[0]} a {date_range[1]}", ln=1)
    pdf.cell(0, 8, f"Departamentos: {', '.join(deptos_sel)}", ln=1)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Resumen Último Snapshot", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Total Votos: {ultimo['total_votos']:,}", ln=1)
    for p in partidos_sel:
        pdf.cell(0, 8, f"{p}: {ultimo[p]:,} ({ultimo[p]/ultimo['total_votos']*100:.1f}%)", ln=1)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 8, "Sentinel: herramienta independiente y neutral.\n"
                         "Solo datos públicos del CNE.\n"
                         "Código: https://github.com/userf8a2c4/sentinel")
    
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()

if st.button("📄 Descargar análisis como PDF"):
    if not df.empty:
        pdf_bytes = create_pdf()
        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("No hay datos para exportar")

# Footer
st.markdown("---")
st.markdown("**Sentinel** • Proyecto independiente • Open-source • [GitHub](https://github.com/userf8a2c4/sentinel)")
st.caption("Datos públicos del CNE • Sin interpretación política • Monitoreo continuo")
