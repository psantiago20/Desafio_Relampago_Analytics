import streamlit as st
from config import THEMES
import plotly.express as px

def render_sidebar(df_raw):
    """Render the sidebar with theme toggle and filters."""
    with st.sidebar:
        # Logo header (HTML img URL is unreliable outside network; using styled text instead)
        st.markdown(
            '<div style="padding: 0.6rem 0; border-left: 4px solid #1152d4; padding-left: 0.75rem;">'
            '<div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b;">Sistema de Vigilância</div>'
            '<div style="font-size: 1.05rem; font-weight: 800; color: #1152d4;">HIV Gestacional</div>'
            '<div style="font-size: 0.7rem; color: #64748b;">SINAN / Ministério da Saúde</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        # Theme Toggle
        st.markdown("### Personalização")
        theme_sel = st.radio(
            "Selecione o Tema",
            options=["Claro", "Escuro"],
            index=0,
            horizontal=True,
            key="theme_toggle_main"
        )
        theme_key = "light" if theme_sel == "Claro" else "dark"
        st.markdown("---")
        
        # Filters
        st.markdown("### Filtros")
        
        # Years
        years = sorted(df_raw["ano_notific"].dropna().unique().astype(int))
        if not years:
            years = [2023]
        sel_years = st.multiselect("Janela Temporal", years, default=years)
        
        # Regions
        regions = sorted(df_raw["regiao"].unique())
        sel_regions = st.multiselect("Macro-Regiões", regions, default=regions)
        
        st.markdown("---")
        st.markdown("### Notas")
        st.info("Plataforma de vigilância otimizada para análise epidemiológica.")
        
    mask = (df_raw["ano_notific"].isin(sel_years)) & (df_raw["regiao"].isin(sel_regions))
    return df_raw[mask], sel_years, theme_key

def render_kpi_card(label, value, icon, delta=None, delta_type="up"):
    """Renders a single custom HTML KPI card matching reference."""
    delta_html = ""
    if delta:
        cls = "delta-up" if delta_type == "up" else "delta-down"
        arrow_icon = "trending_up" if delta_type == "up" else "trending_down"
        delta_html = f'<span class="kpi-delta {cls}"><span class="material-symbols-outlined" style="font-size: 0.9rem; vertical-align: middle;">{arrow_icon}</span> {delta}</span>'

    # Layout: Icon and Label in Header, Value Below
    card_html = (
        f'<div class="kpi-card">'
        f'<div class="kpi-header">'
        f'<div class="kpi-icon"><span class="material-symbols-outlined">{icon}</span></div>'
        f'<span class="kpi-label">{label.upper()}</span>'
        f'</div>'
        f'<div class="kpi-value-container">'
        f'<span class="kpi-value">{value}</span>'
        f'{delta_html}'
        f'</div>'
        f'</div>'
    )
    return card_html

def render_kpis(filtered_df, ano_sel):
    st.markdown("### Resumo Estratégico")
    
    # Calculate metrics
    n_notific = f"{len(filtered_df):,}"
    
    lag = "N/A"
    if 'atraso_dias' in filtered_df.columns:
        df_hist_filter = filtered_df[filtered_df['atraso_dias'].between(0, 365)]
        if not df_hist_filter.empty:
            lag = f"{df_hist_filter['atraso_dias'].median():.0f} d"
    
    idade = "N/A"
    if 'idade_anos' in filtered_df.columns:
        idade = f"{filtered_df['idade_anos'].mean():.1f}"
    
    variacao = "N/A"
    v_type = "up"
    if len(ano_sel) > 1:
        v_min = filtered_df[filtered_df["ano_notific"] == min(ano_sel)].shape[0]
        v_max = filtered_df[filtered_df["ano_notific"] == max(ano_sel)].shape[0]
        if v_min > 0:
            val = ((v_max - v_min) / v_min) * 100
            variacao = f"{val:+.1f}%"
            v_type = "up" if val >= 0 else "down"

    # Render with custom HTML - Labels exactly as requested
    kpi_cols = st.columns(4)
    with kpi_cols[0]: st.markdown(render_kpi_card("NOTIFICAÇÕES", n_notific, "bar_chart"), unsafe_allow_html=True)
    with kpi_cols[1]: st.markdown(render_kpi_card("MEDIANA LAG", lag, "schedule", "-2d", "up"), unsafe_allow_html=True)
    with kpi_cols[2]: st.markdown(render_kpi_card("IDADE MÉDIA", idade, "person"), unsafe_allow_html=True)
    with kpi_cols[3]: st.markdown(render_kpi_card("VARIAÇÃO", variacao, "trending_up" if v_type=="up" else "trending_down", delta=None, delta_type=v_type), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

def format_fig(fig, theme_name="light", legend_horiz=True):
    colors = THEMES[theme_name]
    
    layout_update = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=colors["text_muted"], size=12),
        margin=dict(l=20, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor=colors["card"], font_color=colors["text_main"], font_size=13, font_family="Inter")
    )
    
    if legend_horiz:
        layout_update["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="", font=dict(color=colors["text_main"]))
    else:
        layout_update["legend"] = dict(title_text="", font=dict(color=colors["text_main"]))
        
    fig.update_layout(**layout_update)
    
    # Generic axes formatting
    fig.update_xaxes(
        title_font=dict(color=colors["text_main"], size=13),
        tickfont=dict(color=colors["text_main"]),
        gridcolor=colors["border"] if theme_name == "dark" else "#f1f5f9",
        linecolor=colors["border"],
        showgrid=False
    )
    fig.update_yaxes(
        title_font=dict(color=colors["text_main"], size=13),
        tickfont=dict(color=colors["text_main"]),
        gridcolor=colors["border"] if theme_name == "dark" else "#f1f5f9",
        linecolor=colors["border"],
        showgrid=True
    )
    
    return fig
