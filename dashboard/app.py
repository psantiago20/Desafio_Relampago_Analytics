import streamlit as st
import warnings

# Configuration and Data Loader
from config import get_css, THEMES
from data_loader import load_data, get_brazil_geojson

# Components and Views
from components import render_sidebar, render_kpis
from views import (
    render_temporal, 
    render_demografico, 
    render_cartografia, 
    render_bivariada, 
    render_ia, 
    render_matriz,
    render_cascata,
    render_fontes
)

# Suppress pandas FutureWarnings for clean console
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------- 1. PAGE SETUP ---------------- #
st.set_page_config(
    page_title="Vigilância Epidemiológica: HIV em Gestantes",
    page_icon="https://www.gov.br/favicon.ico", # Usando um ícone oficial ou similar, ou apenas removendo o emoji
    layout="wide",
)

# ---------------- 2. DATA LOADING ---------------- #
brazil_geojson = get_brazil_geojson()
df_raw = load_data()

# ---------------- 3. SIDEBAR, FILTERS & THEME ---------------- #
filtered_df, ano_sel, theme_key = render_sidebar(df_raw)

# Inject dynamic CSS based on theme
st.markdown(get_css(theme_key), unsafe_allow_html=True)

# ---------------- 4. HEADER ---------------- #
st.title("Vigilância Epidemiológica: HIV Gestacional")
st.markdown(
    f"""
    <div style='color: var(--text-muted); font-size: 1.1rem; margin-bottom: 1.5rem; font-family: Inter, sans-serif;'>
        <b>Plataforma de Inteligência Especializada</b> | Base SINAN/MS<br>
        <i>Volume amostral atual: <b>{filtered_df.shape[0]:,}</b> notificações (N).</i>
    </div>
    """, unsafe_allow_html=True
)

# ---------------- 5. KPIs ---------------- #
render_kpis(filtered_df, ano_sel)

# ---------------- 6. TABS RENDERING ---------------- #
t1, t2, t3, t4, t7, t5, t6, t8 = st.tabs([
    "Evolução Temporal", 
    "Perfil Social", 
    "Cartografia", 
    "Correlações Clínicas",
    "Adesão ao Tratamento",
    "Inteligência Artificial", 
    "Matriz Bruta",
    "Fontes"
])

with t1: render_temporal(filtered_df, theme_key)
with t2: render_demografico(filtered_df, theme_key)
with t3: render_cartografia(filtered_df, brazil_geojson, theme_key)
with t4: render_bivariada(filtered_df, theme_key)
with t7: render_cascata(filtered_df, theme_key)
with t5: render_ia(filtered_df, theme_key)
with t6: render_matriz(filtered_df, theme_key)
with t8: render_fontes(theme_key)

st.markdown("---")
st.caption("Base: SINAN/MS | Projeto Científico e Institucional Interativo")
