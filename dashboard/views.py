import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from prophet import Prophet
from config import COLORS
from components import format_fig

try:
    from streamlit_extras.dataframe_explorer import dataframe_explorer
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False

def render_temporal(filtered_df):
    st.markdown("### Dinâmica Temporal e Eficiência Regulatória")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Série Histórica Mensal (Acumulado)**")
        ts = filtered_df.resample("ME", on="dt_notific").size().reset_index(name="casos")
        ts['Tendencia_MA6'] = ts['casos'].rolling(window=6).mean()
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=ts['dt_notific'], y=ts['casos'], mode='lines', fill='tozeroy',
            line=dict(width=3, color=COLORS['primary'], shape='spline', smoothing=1.3),
            fillcolor='rgba(26, 54, 93, 0.1)', name="Casos Mensais"
        ))
        
        fig_line.add_trace(go.Scatter(
            x=ts['dt_notific'], y=ts['Tendencia_MA6'], mode='lines',
            line=dict(width=2.5, color=COLORS['warning'], dash='dash', shape='spline', smoothing=1.3),
            name="Tendência (Média 6M)"
        ))

        fig_line.update_layout(hovermode="x", xaxis_title="", yaxis_title="Volume", legend_title_text="")
        st.plotly_chart(format_fig(fig_line, legend_horiz=True), use_container_width=True)
        
    with col2:
        st.markdown("**Frequência de Delay (Notificação)**")
        if 'atraso_dias' in filtered_df.columns:
            df_hist_filter = filtered_df[filtered_df['atraso_dias'].between(0, 365)]
            if not df_hist_filter.empty:
                mediana_lag = df_hist_filter['atraso_dias'].median()
                fig_hist = px.histogram(df_hist_filter, x='atraso_dias', nbins=30, color_discrete_sequence=[COLORS["accent"]], opacity=0.85)
                fig_hist.add_vline(x=mediana_lag, line_width=2.5, line_dash="dot", line_color=COLORS['warning'], 
                                   annotation_text=f"Mediana: {mediana_lag:.0f} dias", annotation_position="top right", 
                                   annotation_font_color=COLORS['text_main'], annotation_font_weight="bold")
                fig_hist.update_layout(xaxis_title="Atraso em Dias", yaxis_title="Frequência", bargap=0.08)
                st.plotly_chart(format_fig(fig_hist, legend_horiz=False), use_container_width=True)

def render_demografico(filtered_df):
    st.markdown("### Variáveis Biossociais e de Saúde")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Declaração Étnico-Racial**")
        df_raca = filtered_df['raca'].value_counts().reset_index()
        fig_raca = px.bar(df_raca, x='raca', y='count', color='raca', color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(format_fig(fig_raca, legend_horiz=False), use_container_width=True)
        
        st.markdown("**Concentração Etária (KDE)**")
        if 'idade_anos' in filtered_df.columns:
            import plotly.figure_factory as ff
            hist_data = [filtered_df['idade_anos'].dropna()]
            group_labels = ['Idade']
            fig_kde = ff.create_distplot(hist_data, group_labels, show_hist=False, show_rug=False, colors=[COLORS["primary"]])
            st.plotly_chart(format_fig(fig_kde, legend_horiz=False), use_container_width=True)
            
    with c2:
        st.markdown("**Grau de Escolaridade Reportado**")
        df_esc = filtered_df['escolaridade'].value_counts().reset_index()
        fig_esc = px.bar(df_esc, x='count', y='escolaridade', orientation='h', color='count', color_continuous_scale='Blues')
        fig_esc.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_esc, legend_horiz=False), use_container_width=True)

        st.markdown("**Dispersão Etária por Região**")
        if 'idade_anos' in filtered_df.columns:
            fig_box = px.box(filtered_df, x='regiao', y='idade_anos', color='regiao', color_discrete_sequence=px.colors.qualitative.Plotly)
            st.plotly_chart(format_fig(fig_box), use_container_width=True)

def render_cartografia(filtered_df, brazil_geojson):
    st.markdown("### Cartografia Estratégica Regional")
    geo = filtered_df["uf"].value_counts().reset_index()
    geo.columns = ["UF", "Notificacoes"]
    col_map, col_bar = st.columns([1.5, 1])
    
    with col_map:
        if brazil_geojson:
            st.markdown("**Densidade Geográfica de Casos (Brasil)**")
            fig_map = px.choropleth(
                geo, geojson=brazil_geojson, locations="UF", featureidkey="properties.sigla",
                color="Notificacoes", color_continuous_scale="Blues", scope="south america"
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(margin={"r":0,"t":10,"l":0,"b":0}, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Falha na renderização espacial: GeoJSON indisponível. Exibindo alternativa tabular.")

    with col_bar:
        st.markdown("**Top 10 Unidades Federativas (Ranking)**")
        top_geo = geo.head(10).sort_values(by="Notificacoes", ascending=True)
        fig_top = px.bar(top_geo, x="Notificacoes", y="UF", orientation='h', text_auto='.3s', color="Notificacoes", color_continuous_scale="Blues")
        fig_top.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_top, legend_horiz=False), use_container_width=True)

def render_bivariada(filtered_df):
    st.markdown("### Correlações e Testes de Hipótese Clínicas")
    st.info("Testes de independência Qui-Quadrado (Chi-Squared) com significância de 5% (p < 0.05).")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Relação Idade x Pré-Natal**")
        df_clean = filtered_df.dropna(subset=['idade_categoria', 'momento_diagnostico'])
        df_clean = df_clean[(df_clean['idade_categoria'] != 'Ignorado') & (df_clean['momento_diagnostico'] != 'Ignorado')]
        if not df_clean.empty:
            tab = pd.crosstab(df_clean['idade_categoria'], df_clean['momento_diagnostico'])
            chi2, p, dof, ex = chi2_contingency(tab)
            df_plot = tab.reset_index().melt(id_vars='idade_categoria', var_name='Resposta', value_name='Freq')
            fig1 = px.bar(df_plot, x='idade_categoria', y='Freq', color='Resposta', barmode='group', color_discrete_sequence=px.colors.qualitative.T10)
            fig1.add_annotation(x=0.5, y=0.95, xref="paper", yref="paper", text=f"p-value = {p:.4e}", showarrow=False, font=dict(color=COLORS['warning'], size=14, weight="bold"))
            st.plotly_chart(format_fig(fig1), use_container_width=True)
            
    with c2:
        st.markdown("**Relação Tipo de Parto x Pré-Natal (Proporcional)**")
        df_clean2 = filtered_df.dropna(subset=['tipo_parto', 'momento_diagnostico'])
        df_clean2 = df_clean2[(df_clean2['tipo_parto'] != 'Ignorado') & (df_clean2['momento_diagnostico'] != 'Ignorado')]
        if not df_clean2.empty:
            tab2 = pd.crosstab(df_clean2['momento_diagnostico'], df_clean2['tipo_parto'])
            chi2_2, p_2, dof_2, ex_2 = chi2_contingency(tab2)
            pct_df = (tab2.div(tab2.sum(axis=1), axis=0) * 100).reset_index().melt(id_vars='momento_diagnostico', value_name='Percentual')
            fig2 = px.bar(pct_df, x='momento_diagnostico', y='Percentual', color='tipo_parto', text_auto='.1f', color_discrete_sequence=[COLORS['primary'], COLORS['secondary']])
            fig2.add_annotation(x=0.5, y=1.05, xref="paper", yref="paper", text=f"p-value = {p_2:.4e}", showarrow=False, font=dict(color=COLORS['warning'], size=14, weight="bold"))
            st.plotly_chart(format_fig(fig2), use_container_width=True)

def render_ia(filtered_df):
    st.markdown("### Segmentação e Inferência Preditiva Longitudinal")
    c_m1, c_m2 = st.columns([1, 1])
    
    with c_m1:
        st.markdown("**Segmentação PCA: Idade vs UF**")
        df_pca = filtered_df[['idade_anos', 'uf']].dropna().copy()
        if not df_pca.empty:
            df_pca['uf_code'] = df_pca['uf'].astype('category').cat.codes
            X = StandardScaler().fit_transform(df_pca[['idade_anos', 'uf_code']])
            coords = PCA(n_components=2).fit_transform(X)
            df_pca['PCA1'] = coords[:, 0]
            df_pca['PCA2'] = coords[:, 1]
            fig_pca = px.scatter(df_pca.sample(min(2000, len(df_pca))), x='PCA1', y='PCA2', color='uf', opacity=0.7)
            st.plotly_chart(format_fig(fig_pca, legend_horiz=False), use_container_width=True)

    with c_m2:
        st.markdown("**Drivers do Atraso de Notificação (Random Forest)**")
        df_rf = filtered_df[['idade_anos', 'regiao', 'momento_diagnostico', 'atraso_dias']].dropna()
        if not df_rf.empty:
            df_rf = df_rf[df_rf['atraso_dias'] >= 0] 
            X_rf = pd.get_dummies(df_rf[['idade_anos', 'regiao', 'momento_diagnostico']], drop_first=True)
            y_rf = df_rf['atraso_dias']
            rf_model = RandomForestRegressor(n_estimators=50, random_state=42).fit(X_rf, y_rf)
            imp = pd.DataFrame({'feature': X_rf.columns, 'importance': rf_model.feature_importances_}).sort_values('importance', ascending=True)
            fig_rf = px.bar(imp.tail(10), x='importance', y='feature', orientation='h', color='importance', color_continuous_scale='Greens')
            fig_rf.update_layout(coloraxis_showscale=False)
            st.plotly_chart(format_fig(fig_rf, legend_horiz=False), use_container_width=True)
            
    st.divider()
    st.markdown("**Projeção de Longo Prazo (Prophet)**")
    if st.button("Executar Inferência Temporal Larga (24 meses)", type="primary"):
        with st.spinner("Treinando algoritmos Prophet..."):
            ts_prophet = filtered_df.resample("ME", on="dt_notific").size().reset_index(name="casos")
            ts_prophet = ts_prophet.rename(columns={"dt_notific": "ds", "casos": "y"})
            model = Prophet(yearly_seasonality=True)
            model.fit(ts_prophet)
            future = model.make_future_dataframe(periods=24, freq="ME")
            forecast = model.predict(future)
            
            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(x=ts_prophet["ds"], y=ts_prophet["y"], mode='markers+lines', name="Dados Históricos", line=dict(color=COLORS["secondary"], width=2)))
            fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], name="Modelo Preditivo", line=dict(color=COLORS["accent"], dash="dash", width=3)))
            fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_upper"], line=dict(width=0), showlegend=False))
            fig_fc.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_lower"], fill='tonexty', fillcolor='rgba(49, 130, 206, 0.2)', line=dict(width=0), name="Interv. Confiança"))
            st.plotly_chart(format_fig(fig_fc), use_container_width=True)

def render_matriz(filtered_df):
    st.markdown("### Matriz Exploratória (Data Mining)")
    cols_to_show = [c for c in ['dt_notific', 'ano_notific', 'uf', 'regiao', 'idade_anos', 'raca', 'escolaridade', 'momento_diagnostico', 'tipo_parto', 'atraso_dias'] if c in filtered_df.columns]
    
    if EXTRAS_AVAILABLE:
        try:
            filtered_df_exp = dataframe_explorer(filtered_df[cols_to_show])
            st.dataframe(filtered_df_exp, use_container_width=True)
        except Exception:
            st.dataframe(filtered_df[cols_to_show].head(1000), use_container_width=True)
    else:
        st.dataframe(filtered_df[cols_to_show].head(1000), use_container_width=True)
