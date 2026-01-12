# dashboard.py
# Sentinel - Dashboard Interactivo Completo de Verificación de Datos Electorales CNE
# Versión mejorada: carga realista, Benford real, PDF completo
# Ejecutar: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import hashlib
import base64
import kaleido  # Necesario para fig.write_image()

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sentinel - Verificación Independiente CNE Honduras",
    page_icon="🇭🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS (simulación realista - reemplaza con tu scraper o load JSON/CSV)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)  # Cache 1 hora
def load_data():
    # Estructura típica de datos CNE: snapshots con votos por candidato, depto, timestamp
    timestamps = pd.date_range(start='2025-11-30 18:00', end='2025-12-01 06:00', freq='15min')
    departamentos = ['Cortés', 'Francisco Morazán', 'Atlántida', 'Comayagua', 'Choluteca']
    candidatos = ['Partido Libre', 'Partido Nacional', 'PSH', 'Otros']
    
    data = []
    for ts in timestamps:
        for depto in departamentos:
            total = np.random.randint(5000, 50000)
            votos = np.random.multinomial(total, [0.38, 0.35, 0.18, 0.09])
            hash_sim = hashlib.sha256(f"{ts}_{depto}_{votos}".encode()).hexdigest()
            data.append({
                'timestamp': ts,
                'departamento': depto,
                'total_votos': total,
                **{c: v for c, v in zip(candidatos, votos)},
                'hash_snapshot': hash_sim
            })
    
    df = pd.DataFrame(data)
    return df

df_raw = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR - Controles
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Sentinel 🇭🇳")
    st.markdown("**Monitoreo neutral y continuo de datos públicos del CNE**")
    st.markdown("Open-source | Solo hechos objetivos")
    
    st.markdown("---")
    
    modo_simple = st.toggle("Modo Simple (solo resumen)", value=False)
    
    st.subheader("Filtros Globales")
    
    deptos_disponibles = ['Todos'] + sorted(df_raw['departamento'].unique().tolist())
    deptos_seleccionados = st.multiselect("Departamento(s)", deptos_disponibles, default=['Todos'])
    
    candidatos_disponibles = df_raw.columns.drop(['timestamp', 'departamento', 'total_votos', 'hash_snapshot']).tolist()
    candidatos_seleccionados = st.multiselect("Candidatos / Partidos", candidatos_disponibles, default=candidatos_disponibles[:2])
    
    min_ts, max_ts = df_raw['timestamp'].min(), df_raw['timestamp'].max()
    rango_ts = st.slider(
        "Rango de Snapshots",
        min_value=min_ts.to_pydatetime(),
        max_value=max_ts.to_pydatetime(),
        value=(min_ts.to_pydatetime(), max_ts.to_pydatetime())
    )
    
    umbral_alerta_benford = st.slider("Umbral alerta Benford (desviación %)", 0.0, 15.0, 5.0, 0.5)

# ──────────────────────────────────────────────────────────────────────────────
# FILTRADO
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def filtrar_df(df, deptos, candidatos, rango):
    df_f = df.copy()
    if 'Todos' not in deptos:
        df_f = df_f[df_f['departamento'].isin(deptos)]
    df_f = df_f[(df_f['timestamp'] >= pd.to_datetime(rango[0])) & (df_f['timestamp'] <= pd.to_datetime(rango[1]))]
    return df_f

df = filtrar_df(df_raw, deptos_seleccionados, candidatos_seleccionados, rango_ts)

# ──────────────────────────────────────────────────────────────────────────────
# FUNCIÓN BENFORD REAL
# ──────────────────────────────────────────────────────────────────────────────
def calcular_benford(series):
    """Calcula distribución primer dígito y desviación de Benford"""
    if len(series) < 10:
        return None, None, None
    
    # Primer dígito (ignorar 0)
    primeros = series.astype(str).str[0].astype(int)
    primeros = primeros[primeros.between(1,9)]
    
    if len(primeros) < 10:
        return None, None, None
    
    observada = primeros.value_counts(normalize=True).sort_index().reindex(range(1,10), fill_value=0)
    
    # Distribución teórica Benford
    benford_teorica = pd.Series([np.log10(1 + 1/d) for d in range(1,10)], index=range(1,10))
    
    # Desviación MAD (Mean Absolute Deviation)
    mad = np.mean(np.abs(observada - benford_teorica))
    porcentaje_desviacion = mad * 100
    
    return observada, benford_teorica, porcentaje_desviacion

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
if df.empty:
    st.warning("No hay datos en el rango seleccionado. Ajusta los filtros.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "🗺️ Por Departamento", "⏱️ Temporal", "🔒 Integridad & Benford"])

    with tab1:
        st.subheader("Resumen Filtrado (Último Snapshot)")
        ultimo = df.iloc[-1]
        
        cols = st.columns(len(candidatos_seleccionados) + 1)
        with cols[0]:
            st.metric("Total Votos", f"{ultimo['total_votos']:,}")
        
        for i, cand in enumerate(candidatos_seleccionados, 1):
            with cols[i]:
                v = ultimo[cand]
                p = v / ultimo['total_votos'] * 100 if ultimo['total_votos'] > 0 else 0
                st.metric(cand, f"{v:,}", f"{p:.1f}%")

    with tab2:
        st.subheader("Votos por Departamento (Último Snapshot)")
        df_depto = df.groupby('departamento')[['total_votos'] + candidatos_seleccionados].last().reset_index()
        st.dataframe(df_depto.style.format({c: "{:,}" for c in df_depto.columns if c != 'departamento'}))
        
        fig_bar = px.bar(
            df_depto.melt(id_vars='departamento', value_vars=candidatos_seleccionados),
            x='departamento', y='value', color='variable',
            barmode='group', title="Distribución por Candidato y Departamento"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Evolución Temporal")
        df_melt = df.melt(id_vars='timestamp', value_vars=candidatos_seleccionados, var_name='Candidato', value_name='Votos')
        fig_line = px.line(df_melt, x='timestamp', y='Votos', color='Candidato', title="Evolución de Votos")
        st.plotly_chart(fig_line, use_container_width=True)

    with tab4:
        st.subheader("Integridad y Ley de Benford")
        
        st.markdown("**Cadena de Hashes (últimos 5)**")
        for h in df['hash_snapshot'].tail(5):
            st.code(h)
        
        st.subheader("Análisis Benford (Primer Dígito)")
        # Aplicamos Benford a columna de total_votos como ejemplo (puedes cambiar a votos por candidato)
        obs, teor, desviacion = calcular_benford(df['total_votos'])
        
        if obs is not None:
            df_benford = pd.DataFrame({
                'Dígito': range(1,10),
                'Observado': obs.values,
                'Esperado (Benford)': teor.values
            })
            
            fig_benford = go.Figure()
            fig_benford.add_trace(go.Bar(x=df_benford['Dígito'], y=df_benford['Observado'], name='Observado'))
            fig_benford.add_trace(go.Scatter(x=df_benford['Dígito'], y=df_benford['Esperado (Benford)'], mode='lines+markers', name='Benford Teórica'))
            fig_benford.update_layout(title=f"Distribución Primer Dígito - Desviación: {desviacion:.2f}%")
            st.plotly_chart(fig_benford, use_container_width=True)
            
            if desviacion > umbral_alerta_benford:
                st.error(f"⚠️ Alerta: Desviación {desviacion:.2f}% supera umbral de {umbral_alerta_benford}%")
            else:
                st.success(f"✅ Desviación dentro de lo esperado ({desviacion:.2f}%)")
        else:
            st.info("Datos insuficientes para análisis Benford")

# ──────────────────────────────────────────────────────────────────────────────
# GENERAR PDF COMPLETO
# ──────────────────────────────────────────────────────────────────────────────
def generar_pdf_completo(df_filtrado, candidatos_sel, rango, desviacion_benford=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Análisis Personalizado - Sentinel", ln=1, align='C')
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Filtros Aplicados:", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Departamentos: {', '.join(deptos_seleccionados)}", ln=1)
    pdf.cell(0, 8, f"Rango: {rango[0].strftime('%Y-%m-%d %H:%M')} → {rango[1].strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(0, 8, f"Candidatos: {', '.join(candidatos_sel)}", ln=1)
    pdf.ln(10)
    
    # Tabla totals último snapshot
    ultimo = df_filtrado.iloc[-1]
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Resumen Último Snapshot", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(60, 8, "Total Votos:", border=1)
    pdf.cell(0, 8, f"{ultimo['total_votos']:,}", border=1, ln=1)
    for cand in candidatos_sel:
        pdf.cell(60, 8, f"{cand}:", border=1)
        pdf.cell(0, 8, f"{ultimo[cand]:,} ({ultimo[cand]/ultimo['total_votos']*100:.1f}%)", border=1, ln=1)
    
    pdf.ln(10)
    
    # Benford
    if desviacion_benford is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, f"Análisis Benford - Desviación: {desviacion_benford:.2f}%", ln=1)
        pdf.set_font("Helvetica", "", 11)
        if desviacion_benford > umbral_alerta_benford:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 8, "⚠️ Posible anomalía detectada", ln=1)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 8, "✅ Dentro de parámetros esperados", ln=1)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 8, "Sentinel es una herramienta independiente, open-source y neutral.\n"
                         "Datos públicos del CNE. Sin interpretación política.\n"
                         "Código: https://github.com/userf8a2c4/sentinel")
    
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# DESCARGA PDF
# ──────────────────────────────────────────────────────────────────────────────
if st.button("📄 Generar y Descargar Análisis Completo como PDF"):
    if not df.empty:
        obs, _, dev = calcular_benford(df['total_votos'])
        pdf_data = generar_pdf_completo(df, candidatos_seleccionados, rango_ts, dev)
        
        st.download_button(
            label="Descargar PDF ahora",
            data=pdf_data,
            file_name=f"sentinel_analisis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("No hay datos para generar PDF")

# Footer
st.markdown("---")
st.markdown(
    "**Sentinel** es open-source y 100% neutral. "
    "Revisa el código y contribuye: "
    "[github.com/userf8a2c4/sentinel](https://github.com/userf8a2c4/sentinel)"
)
st.caption("Datos públicos del CNE Honduras • Solo hechos objetivos • Proyecto independiente")
