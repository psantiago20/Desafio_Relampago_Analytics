import streamlit as st
from config import COLORS
import plotly.express as px

try:
    from streamlit_extras.metric_cards import style_metric_cards
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False

def render_sidebar(df_raw):
    with st.sidebar:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Red_and_Black_Ribbon.png/640px-Red_and_Black_Ribbon.png", width=110)
        st.markdown("---")
        st.markdown("### Parâmetros Experimentais")
        
        anos = sorted(df_raw["ano_notific"].dropna().unique().astype(int))
        ano_sel = st.multiselect("Janela Temporal", anos, default=anos)
        
        regioes = sorted(df_raw["regiao"].unique())
        reg_sel = st.multiselect("Macro-Regiões", regioes, default=regioes)
        
        st.markdown("---")
        st.markdown("### Notas Técnicas")
        st.info("A filtragem restringe os dados até o fim de 2023 para evitar vieses de subnotificação do ano corrente.")
        
    return df_raw[(df_raw["ano_notific"].isin(ano_sel)) & (df_raw["regiao"].isin(reg_sel))], ano_sel

def render_kpis(filtered_df, ano_sel):
    st.markdown("### Resumo Estatístico")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(label="Notificações (N)", value=f"{len(filtered_df):,}")

    with c2:
        if 'atraso_dias' in filtered_df.columns:
            mediana_atraso = filtered_df['atraso_dias'].median()
            st.metric(label="Mdn. Lag de Registro", value=f"{mediana_atraso:.0f} dias")
        else:
            st.metric(label="Mdn. Lag de Registro", value="N/A")

    with c3:
        if 'idade_anos' in filtered_df.columns:
            idade_media = filtered_df['idade_anos'].mean()
            st.metric(label="Idade Média", value=f"{idade_media:.1f} anos")
        else:
            st.metric(label="Idade Média", value="N/A")

    with c4:
        if len(ano_sel) > 1:
            ano_min = min(ano_sel)
            ano_max = max(ano_sel)
            vol_min = filtered_df[filtered_df["ano_notific"] == ano_min].shape[0]
            vol_max = filtered_df[filtered_df["ano_notific"] == ano_max].shape[0]
            if vol_min > 0:
                var_acumulada = ((vol_max - vol_min) / vol_min) * 100
                st.metric(label=f"Variação ({ano_min}-{ano_max})", value=f"{var_acumulada:+.1f}%")
            else:
                st.metric(label="Variação Acumulada", value="N/A")
        else:
            st.metric(label="Variação Acumulada", value="N/A")

    if EXTRAS_AVAILABLE:
        style_metric_cards(background_color=COLORS["card"], border_left_color=COLORS["accent"], border_color=COLORS["border"], box_shadow=True)
    st.divider()

def format_fig(fig, legend_horiz=True):
    layout_update = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["text_muted"], size=12),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    if legend_horiz:
        layout_update["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="")
    else:
        layout_update["legend"] = dict(title_text="")
        
    fig.update_layout(**layout_update)
    
    # Force blank titles and suppress 'undefined' ghost rendering
    fig.update_xaxes(title_text='', showgrid=False, linecolor=COLORS["border"])
    fig.update_yaxes(title_text='', showgrid=True, gridcolor="#EDF2F7", linecolor=COLORS["border"])
    
    return fig
