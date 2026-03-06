import streamlit as st
import warnings

# Configuration and Data Loader
from config import COLORS, CSS_STYLE
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
    render_cascata
)

# Suppress pandas FutureWarnings for clean console
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------- 1. PAGE SETUP ---------------- #
st.set_page_config(
    page_title="Vigilância Epidemiológica: HIV em Gestantes",
    page_icon="🧬",
    layout="wide",
)

st.markdown(CSS_STYLE, unsafe_allow_html=True)

# ---------------- 2. DATA LOADING ---------------- #
brazil_geojson = get_brazil_geojson()
df_raw = load_data()

# ---------------- 3. SIDEBAR & FILTERS ---------------- #
filtered_df, ano_sel = render_sidebar(df_raw)

# ---------------- 4. HEADER ---------------- #
st.title("Vigilância Epidemiológica: HIV Gestacional")
st.markdown(
    f"""
    <div style='color: {COLORS['text_muted']}; font-size: 1.1rem; margin-bottom: 1.5rem; font-family: Inter, sans-serif;'>
        <b>Plataforma Acadêmica de Inteligência Especializada</b> | Base SINAN/MS<br>
        <i>Volume amostral atual: <b>{filtered_df.shape[0]:,}</b> notificações (N).</i>
    </div>
    """, unsafe_allow_html=True
)

# ---------------- 5. KPIs ---------------- #
render_kpis(filtered_df, ano_sel)

# ---------------- 6. TABS RENDERING ---------------- #
t1, t2, t3, t7, t4, t5, t6 = st.tabs([
    "Evolução Temporal", 
    "Perfil Social", 
    "Cartografia", 
    "Adesão a Pré-natal",
    "Estatística Bivariada", 
    "Inteligência Artificial", 
    "Matriz Bruta"
])

with t1: render_temporal(filtered_df)
with t2: render_demografico(filtered_df)
with t3: render_cartografia(filtered_df, brazil_geojson)
with t7: render_cascata(filtered_df)
with t4: render_bivariada(filtered_df)
with t5: render_ia(filtered_df)
with t6: render_matriz(filtered_df)

st.markdown("---")
st.caption("Base: SINAN/MS | Projeto Científico e Institucional Interativo")
