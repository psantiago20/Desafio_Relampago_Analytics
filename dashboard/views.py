import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt
import math
from config import THEMES
from components import format_fig

try:
    from streamlit_extras.dataframe_explorer import dataframe_explorer
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False

def render_temporal(filtered_df, theme_key="light"):
    colors = THEMES[theme_key]
    st.markdown("### Dinâmica Temporal e Eficiência Regulatória")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Série Histórica Mensal (Acumulado)**")
        ts = filtered_df.resample("ME", on="dt_notific").size().reset_index(name="casos")
        ts['Tendencia_MA6'] = ts['casos'].rolling(window=6).mean()
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=ts['dt_notific'], y=ts['casos'], mode='lines', fill='tozeroy',
            line=dict(width=3, color=colors['primary']),
            fillcolor=colors['fill_color'], name="Casos Mensais"
        ))
        
        fig_line.add_trace(go.Scatter(
            x=ts['dt_notific'], y=ts['Tendencia_MA6'], mode='lines',
            line=dict(width=2.5, color=colors['accent_red'], dash='dash'),
            name="Tendência (Média 6M)"
        ))

        fig_line.update_layout(hovermode="x", xaxis_title="", yaxis_title="Volume", legend_title_text="")
        st.plotly_chart(format_fig(fig_line, theme_name=theme_key, legend_horiz=True), use_container_width=True)
        
    with col2:
        st.markdown("**Frequência de Delay (Notificação)**")
        if 'atraso_dias' in filtered_df.columns:
            df_hist_filter = filtered_df[filtered_df['atraso_dias'].between(0, 365)]
            if not df_hist_filter.empty:
                mediana_lag = df_hist_filter['atraso_dias'].median()
                fig_hist = px.histogram(df_hist_filter, x='atraso_dias', nbins=30, color_discrete_sequence=[colors["primary"]], opacity=0.85)
                fig_hist.add_vline(x=mediana_lag, line_width=2.5, line_dash="dot", line_color=colors['accent_red'], 
                                   annotation_text=f"Mediana: {mediana_lag:.0f} dias", annotation_position="top right", 
                                   annotation_font_color=colors['text_main'], annotation_font_weight="bold")
                st.plotly_chart(format_fig(fig_hist, theme_name=theme_key, legend_horiz=False), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights da Dinâmica Temporal)**")

def render_demografico(filtered_df, theme_key="light"):
    colors = THEMES[theme_key]
    st.markdown("### Variáveis Biossociais e de Saúde")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Declaração Étnico-Racial**")
        df_raca = filtered_df['raca'].value_counts().reset_index()
        fig_raca = px.bar(df_raca, x='raca', y='count', color='raca', color_discrete_sequence=px.colors.sequential.Blues_r if theme_key == "light" else px.colors.sequential.Purples_r)
        st.plotly_chart(format_fig(fig_raca, theme_name=theme_key, legend_horiz=False), use_container_width=True)
        
        st.markdown("**Concentração Etária (KDE)**")
        if 'idade_anos' in filtered_df.columns:
            import plotly.figure_factory as ff
            hist_data = [filtered_df['idade_anos'].dropna()]
            group_labels = ['Idade']
            fig_kde = ff.create_distplot(hist_data, group_labels, show_hist=True, bin_size=1, show_rug=False, colors=["#805AD5"])
            fig_kde.update_layout(bargap=0.1)
            st.plotly_chart(format_fig(fig_kde, theme_name=theme_key, legend_horiz=False), use_container_width=True)
            
    with c2:
        st.markdown("**Grau de Escolaridade Reportado**")
        df_esc = filtered_df['escolaridade'].value_counts().reset_index()
        fig_esc = px.bar(df_esc, x='count', y='escolaridade', orientation='h', color='count', color_continuous_scale='Blues' if theme_key == "light" else 'Purples')
        fig_esc.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_esc, theme_name=theme_key, legend_horiz=False), use_container_width=True)

        st.markdown("**Dispersão Etária por Região**")
        if 'idade_anos' in filtered_df.columns:
            fig_box = px.box(filtered_df, x='regiao', y='idade_anos', color='regiao', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(format_fig(fig_box, theme_name=theme_key), use_container_width=True)

    st.markdown("---")
    st.markdown("### Perfil Social vs Acesso à Terapia Antirretroviral (TARV)")
    st.info("Taxa de gestantes diagnosticadas que conseguiram efetivar a receita e utilizar profilaxia antirretroviral (TARV), filtradas por grupo.")
    
    # Pre-processing para Acesso a TARV
    df_desig = filtered_df.copy()
    if 'pre_antret' in df_desig.columns:
        df_desig['pre_antret_num'] = pd.to_numeric(df_desig['pre_antret'], errors='coerce')
        
        c3, c4 = st.columns(2)
        
        with c3:
            st.markdown("**Acesso por Grau de Escolaridade**")
            # Filtrar escolaridades ignoradas
            df_esc_desig = df_desig[df_desig['escolaridade'] != 'Ignorado'].dropna(subset=['escolaridade', 'pre_antret_num'])
            if not df_esc_desig.empty:
                tab_esc = pd.crosstab(df_esc_desig['escolaridade'], df_esc_desig['pre_antret_num'])
                if 1 in tab_esc.columns:
                    tab_esc['Taxa_Acesso_TARV (%)'] = (tab_esc[1] / tab_esc.sum(axis=1)) * 100
                    tab_esc = tab_esc.reset_index()
                    
                    # Ordem lógica de escolaridade (de menor para maior, ou vice-versa, pro Plotly desenhar corretamente)
                    ordem_esc = ['Sem Escolaridade', 'Fund. I', 'Fund. II', 'Fund. Comp.', 'Med. Incomp.', 'Med. Comp.', 'Sup. Incomp.', 'Sup. Comp.']
                    tab_esc['escolaridade'] = pd.Categorical(tab_esc['escolaridade'], categories=ordem_esc, ordered=True)
                    tab_esc = tab_esc.sort_values(by='escolaridade', ascending=False) # Plotly empilha de baixo pra cima
                    
                    fig_esc_desig = px.bar(
                        tab_esc, x='Taxa_Acesso_TARV (%)', y='escolaridade', orientation='h',
                        text_auto='.1f', color='Taxa_Acesso_TARV (%)', color_continuous_scale='viridis_r',
                        labels={'escolaridade': 'Escolaridade'}
                    )
                    fig_esc_desig.update_layout(coloraxis_showscale=False, xaxis_title="Gestantes Protegidas por TARV (%)", yaxis_title="")
                    st.plotly_chart(format_fig(fig_esc_desig, theme_name=theme_key, legend_horiz=False), use_container_width=True)
                else:
                    st.warning("Sem dados conclusivos de acesso a TARV neste recorte.")
                    
        with c4:
            st.markdown("**Acesso por Cor/Raça**")
            df_raca_desig = df_desig[df_desig['raca'] != 'Ignorado'].dropna(subset=['raca', 'pre_antret_num'])
            if not df_raca_desig.empty:
                tab_raca = pd.crosstab(df_raca_desig['raca'], df_raca_desig['pre_antret_num'])
                if 1 in tab_raca.columns:
                    tab_raca['Taxa_Acesso_TARV (%)'] = (tab_raca[1] / tab_raca.sum(axis=1)) * 100
                    
                    # Aqui, como é raça, podemos ordenar quem tem mais acesso primeiro, não cronológico
                    tab_raca = tab_raca.reset_index().sort_values(by='Taxa_Acesso_TARV (%)', ascending=True)
                    
                    fig_raca_desig = px.bar(
                        tab_raca, x='Taxa_Acesso_TARV (%)', y='raca', orientation='h',
                        text_auto='.1f', color='Taxa_Acesso_TARV (%)', color_continuous_scale='magma',
                        labels={'raca': 'Raça/Cor'}
                    )
                    fig_raca_desig.update_layout(coloraxis_showscale=False, xaxis_title="Gestantes Protegidas por TARV (%)", yaxis_title="")
                    st.plotly_chart(format_fig(fig_raca_desig, theme_name=theme_key, legend_horiz=False), use_container_width=True)
                else:
                    st.warning("Sem dados conclusivos de acesso a TARV neste recorte.")

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights do Perfil Social e Demográfico)**")


def render_cartografia(filtered_df, brazil_geojson, theme_key="light"):
    colors = THEMES[theme_key]
    st.markdown("### Cartografia Estratégica Regional")
    
    # 1. Agrupar os casos absolutos por UF
    geo = filtered_df["uf"].value_counts().reset_index()
    geo.columns = ["UF", "Notificacoes"]
    
    # 2. Dados de População Estimada IBGE para transformar número absoluto em relativo
    populacao_ibge = {
        'SP': 44411238, 'MG': 20538718, 'RJ': 16054524, 'BA': 14141626, 'PR': 11444380,
        'RS': 10882965, 'PE': 9058931, 'CE': 8733687, 'PA': 8120131, 'SC': 7610361,
        'GO': 7056495, 'MA': 6775805, 'PB': 3974687, 'AM': 3941613, 'ES': 3833712,
        'MT': 3658649, 'RN': 3302729, 'PI': 3271199, 'AL': 3127683, 'DF': 2817381,
        'MS': 2757013, 'SE': 2209558, 'RO': 1581196, 'TO': 1511460, 'AC': 830018,
        'AP': 733759, 'RR': 636303
    }
    
    # 3. Calcular a incidência (Casos a cada 100.000 habitantes)
    geo['Populacao'] = geo['UF'].map(populacao_ibge)
    geo['Incidencia_100k'] = (geo['Notificacoes'] / geo['Populacao']) * 100000
    
    # Opcional: Remover eventuais UFs que não conseguiram cruzar corretamente
    geo = geo.dropna(subset=['Incidencia_100k'])

    # =========================================================
    # SEÇÃO 1: VALORES ABSOLUTOS
    # =========================================================
    st.markdown("#### 1. Casos Absolutos (Volume Total de Notificações)")
    col_map_abs, col_bar_abs = st.columns([1.5, 1])
    
    with col_map_abs:
        if brazil_geojson:
            st.markdown("**Densidade Geográfica de Casos (Brasil)**")
            fig_map_abs = px.choropleth(
                geo, geojson=brazil_geojson, locations="UF", featureidkey="properties.sigla",
                color="Notificacoes", color_continuous_scale="Blues" if theme_key == "light" else "Purples", scope="south america",
                hover_data={"UF": True, "Notificacoes": True, "Incidencia_100k": False, "Populacao": False}
            )
            fig_map_abs.update_geos(fitbounds="locations", visible=False)
            fig_map_abs.update_layout(margin={"r":0,"t":10,"l":0,"b":0}, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_map_abs, use_container_width=True)
        else:
            st.warning("Falha na renderização espacial: GeoJSON indisponível. Exibindo alternativa tabular.")

    with col_bar_abs:
        st.markdown("**Unidades Federativas com maior número de casos**")
        top_geo_abs = geo.sort_values(by="Notificacoes", ascending=False).head(10)
        # Invertendo para o Plotly construir a barra do maior em cima
        top_geo_abs = top_geo_abs.sort_values(by="Notificacoes", ascending=True)
        
        fig_top_abs = px.bar(
            top_geo_abs, 
            x="Notificacoes", 
            y="UF", 
            orientation='h', 
            text_auto='.3s', 
            color="Notificacoes", 
            color_continuous_scale="Blues" if theme_key == "light" else "Purples"
        )
        fig_top_abs.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_top_abs, theme_name=theme_key, legend_horiz=False), use_container_width=True)

    st.markdown("---") # Linha divisória visual

    # =========================================================
    # SEÇÃO 2: VALORES PROPORCIONAIS (PORCENTAGEM)
    # =========================================================
    st.markdown("#### 2. Casos Relativos (Incidência Proporcional à População)")
    col_map_rel, col_bar_rel = st.columns([1.5, 1])
    
    with col_map_rel:
        if brazil_geojson:
            st.markdown("**Densidade Geográfica de Casos (Ajuste Demográfico)**")
            fig_map_rel = px.choropleth(
                geo, 
                geojson=brazil_geojson, 
                locations="UF", 
                featureidkey="properties.sigla",
                color="Incidencia_100k", # A Cor do calor responde à incidência
                color_continuous_scale="YlOrBr" if theme_key == "light" else "Oranges", # Usando variações de amarelo/laranja
                scope="south america",
                hover_data={"UF": True, "Notificacoes": True, "Incidencia_100k": ":.1f", "Populacao": False},
                labels={"Incidencia_100k": "Casos/100k hab."}
            )
            fig_map_rel.update_geos(fitbounds="locations", visible=False)
            fig_map_rel.update_layout(margin={"r":0,"t":10,"l":0,"b":0}, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_map_rel, use_container_width=True)
        else:
            st.warning("Falha na renderização espacial: GeoJSON indisponível. Exibindo alternativa tabular.")

    with col_bar_rel:
        st.markdown("**Unidades Federativas com maior proporção de casos por 100k habitantes**")
        # Top 10 piores casos em proporção
        top_geo_rel = geo.sort_values(by="Incidencia_100k", ascending=False).head(10)
        top_geo_rel = top_geo_rel.sort_values(by="Incidencia_100k", ascending=True)
        
        fig_top_rel = px.bar(
            top_geo_rel, 
            x="Incidencia_100k", 
            y="UF", 
            orientation='h', 
            text_auto='.1f', # Reduzindo as casas decimais para mostrar, ex: "45.2" 
            color="Incidencia_100k", 
            color_continuous_scale="YlOrBr" if theme_key == "light" else "Oranges", # Usando variações de amarelo/laranja
            labels={"Incidencia_100k": "Casos por 100k hab."}
        )
        fig_top_rel.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_top_rel, theme_name=theme_key, legend_horiz=False), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights de Cartografia e Distribuição Espacial)**")

def render_bivariada(filtered_df, theme_key="light"):
    colors = THEMES[theme_key]
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
            palette1 = px.colors.qualitative.T10 if theme_key == "light" else px.colors.qualitative.Pastel
            fig1 = px.bar(df_plot, x='idade_categoria', y='Freq', color='Resposta', barmode='group', color_discrete_sequence=palette1)
            fig1.add_annotation(x=0, y=1.05, xref="paper", yref="paper", text=f"p-value = {p:.4e}", showarrow=False, font=dict(color=colors['accent_red'], size=14, weight="bold"), xanchor='left')
            fig1.update_layout(margin=dict(t=50)) 
            st.plotly_chart(format_fig(fig1, theme_name=theme_key), use_container_width=True)
            
    with c2:
        st.markdown("**Relação Tipo de Parto x Pré-Natal (Proporcional)**")
        df_clean2 = filtered_df.dropna(subset=['tipo_parto', 'momento_diagnostico']).copy()
        
        # Agrupar momentos de diagnóstico em categorias binárias de Pré-Natal
        # 'Pré-natal' (1) -> Realizou
        # 'Sem pré-natal' (4), 'Parto' (2), 'Pós-parto' (3) -> Não realizou
        pn_map = {
            'Pré-natal': 'Realizou Pré-Natal',
            'Sem pré-natal': 'Não realizou Pré-Natal',
            'Parto': 'Não realizou Pré-Natal',
            'Pós-parto': 'Não realizou Pré-Natal'
        }
        df_clean2['status_pre_natal'] = df_clean2['momento_diagnostico'].map(pn_map)
        
        # Remover 'Ignorado' e garantir que temos dados válidos
        df_clean2 = df_clean2[df_clean2['status_pre_natal'].notna() & (df_clean2['tipo_parto'] != 'Ignorado')]
        
        if not df_clean2.empty:
            tab2 = pd.crosstab(df_clean2['status_pre_natal'], df_clean2['tipo_parto'])
            chi2_2, p_2, dof_2, ex_2 = chi2_contingency(tab2)
            
            # Cálculo percentual por grupo de Pré-Natal
            pct_df = (tab2.div(tab2.sum(axis=1), axis=0) * 100).reset_index().melt(id_vars='status_pre_natal', value_name='Percentual')
            
            palette2 = [colors['primary'], colors['text_muted']] if theme_key == "light" else [colors['primary'], "#94a3b8"]
            
            fig2 = px.bar(
                pct_df, 
                x='status_pre_natal', 
                y='Percentual', 
                color='tipo_parto', 
                text_auto='.1f', 
                color_discrete_sequence=palette2,
                labels={
                    'status_pre_natal': 'Acompanhamento Pré-Natal',
                    'tipo_parto': 'Tipo de Parto',
                    'Percentual': 'Distribuição (%)'
                }
            )
            fig2.update_traces(texttemplate='%{y:.1f}%', textposition='inside')
            
            fig2.add_annotation(
                x=0, y=1.05, xref="paper", yref="paper", 
                text=f"p-value = {p_2:.4e}", 
                showarrow=False, 
                font=dict(color=colors['accent_red'], size=14, weight="bold"), 
                xanchor='left'
            )
            fig2.update_layout(margin=dict(t=50)) 
            st.plotly_chart(format_fig(fig2, theme_name=theme_key), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights dos Testes de Hipótese e Correlações)**")

def render_ia(filtered_df, theme_key="light"):
    colors = THEMES[theme_key]
    st.markdown("### Segmentação e Inferência Preditiva Longitudinal")
    c_m1, c_m2 = st.columns([1, 1])
    
    with c_m1:
        st.markdown("**Segmentação PCA: Idade vs UF (agrupado por Região)**")
        df_pca = filtered_df[['idade_anos', 'uf', 'regiao']].dropna().copy()
        if not df_pca.empty:
            # Replicar numeração IBGE exata para alinhar a matemática do PCA com o Notebook
            ibge_codes = {
                'RO': 11, 'AC': 12, 'AM': 13, 'RR': 14, 'PA': 15, 'AP': 16, 'TO': 17,
                'MA': 21, 'PI': 22, 'CE': 23, 'RN': 24, 'PB': 25, 'PE': 26, 'AL': 27, 'SE': 28, 'BA': 29,
                'MG': 31, 'ES': 32, 'RJ': 33, 'SP': 35,
                'PR': 41, 'SC': 42, 'RS': 43,
                'MS': 50, 'MT': 51, 'GO': 52, 'DF': 53
            }
            df_pca['uf_num'] = df_pca['uf'].map(ibge_codes).fillna(0)
            
            X = StandardScaler().fit_transform(df_pca[['idade_anos', 'uf_num']])
            coords = PCA(n_components=2).fit_transform(X)
            df_pca['PCA1'] = coords[:, 0]
            df_pca['PCA2'] = coords[:, 1]
            fig_pca = px.scatter(
                df_pca.sample(min(2000, len(df_pca))), 
                x='PCA1', y='PCA2', color='regiao', 
                opacity=0.85, 
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={'regiao': 'Regiões'}
            )
            fig_pca.update_traces(marker=dict(size=8, line=dict(width=0.4, color=colors['background'])))
            st.plotly_chart(format_fig(fig_pca, theme_name=theme_key, legend_horiz=True), use_container_width=True)

    with c_m2:
        st.markdown("**Drivers do Atraso de Notificação (Random Forest)**")
        df_rf = filtered_df[['idade_anos', 'regiao', 'momento_diagnostico', 'atraso_dias']].dropna()
        if not df_rf.empty:
            df_rf = df_rf[df_rf['atraso_dias'] >= 0] 
            X_rf = pd.get_dummies(df_rf[['idade_anos', 'regiao', 'momento_diagnostico']], drop_first=True)
            y_rf = df_rf['atraso_dias']
            rf_model = RandomForestRegressor(n_estimators=50, random_state=42).fit(X_rf, y_rf)
            imp = pd.DataFrame({'feature': X_rf.columns, 'importance': rf_model.feature_importances_}).sort_values('importance', ascending=True)
            fig_rf = px.bar(
                imp.tail(10), x='importance', y='feature', orientation='h', 
                color_discrete_sequence=[colors['primary']]
            )
            st.plotly_chart(format_fig(fig_rf, theme_name=theme_key, legend_horiz=False), use_container_width=True)
            
    st.divider()
    st.markdown("**Projeção de Longo Prazo (Prophet & RandomForest)**")

    # --- Button triggers computation and stores results in session_state ---
    if st.button("Executar Inferência Temporal Larga (Dez/2027)", type="primary"):
        with st.spinner("Treinando algoritmos (Prophet & RandomForest)..."):
            import warnings; warnings.filterwarnings('ignore')
            
            ts = filtered_df.resample('ME', on='dt_notific').size().reset_index()
            ts.columns = ['ds', 'y']
            ts = ts.sort_values('ds').reset_index(drop=True)

            BACKTEST_MONTHS = 12
            END_PROJ       = pd.Timestamp('2027-12-31')

            train = ts.iloc[:-BACKTEST_MONTHS].copy()
            test  = ts.iloc[-BACKTEST_MONTHS:].copy()

            last_real_date = ts['ds'].max()
            n_future = (END_PROJ.year - last_real_date.year) * 12 + (END_PROJ.month - last_real_date.month)

            PROPHET_AVAILABLE = True
            try:
                from prophet import Prophet
                m_p = Prophet(yearly_seasonality=True, changepoint_prior_scale=0.1)
                m_p.fit(train[['ds', 'y']])
                future_full = m_p.make_future_dataframe(periods=BACKTEST_MONTHS + n_future, freq='ME')
                fc_p = m_p.predict(future_full)
                prophet_test_pred  = fc_p[fc_p['ds'].isin(test['ds'])]['yhat'].values
                prophet_future     = fc_p[fc_p['ds'] > last_real_date][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                model_name_prophet = 'Prophet'
            except Exception as e:
                PROPHET_AVAILABLE = False
                st.warning(f'Prophet falhou: {e}. Usando Holt-Winters como fallback.')

            if not PROPHET_AVAILABLE:
                hw = ExponentialSmoothing(train['y'], seasonal_periods=12, trend='add', seasonal='add').fit()
                hw_all  = hw.forecast(BACKTEST_MONTHS + n_future)
                prophet_test_pred  = hw_all.values[:BACKTEST_MONTHS]
                future_dates_hw    = pd.date_range(last_real_date + pd.DateOffset(months=1), periods=n_future, freq='ME')
                std_hw             = train['y'].std()
                prophet_future = pd.DataFrame({
                    'ds': future_dates_hw,
                    'yhat': hw_all.values[BACKTEST_MONTHS:],
                    'yhat_lower': hw_all.values[BACKTEST_MONTHS:] - 1.5*std_hw,
                    'yhat_upper': hw_all.values[BACKTEST_MONTHS:] + 1.5*std_hw,
                })
                model_name_prophet = 'Holt-Winters'

            def make_rf_features(s):
                s = s.copy()
                s['month'] = s['ds'].dt.month
                s['year']  = s['ds'].dt.year
                s['t']     = range(len(s))
                for lag in [1, 2, 3, 6, 12]:
                    if len(s) > lag:
                        s[f'lag_{lag}'] = s['y'].shift(lag)
                return s.dropna()

            train_feat = make_rf_features(train)
            X_cols = ['month', 'year', 't', 'lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12']
            rf = RandomForestRegressor(n_estimators=200, random_state=42)
            rf.fit(train_feat[X_cols], train_feat['y'])

            ts_extended = ts.copy()
            rf_test_pred = []
            for i in range(BACKTEST_MONTHS):
                row = ts_extended.iloc[-(BACKTEST_MONTHS - i)]
                feats = {
                    'month': row['ds'].month, 'year': row['ds'].year,
                    't': len(train) + i,
                    'lag_1':  ts_extended['y'].iloc[-(BACKTEST_MONTHS - i) - 1],
                    'lag_2':  ts_extended['y'].iloc[-(BACKTEST_MONTHS - i) - 2],
                    'lag_3':  ts_extended['y'].iloc[-(BACKTEST_MONTHS - i) - 3],
                    'lag_6':  ts_extended['y'].iloc[-(BACKTEST_MONTHS - i) - 6],
                    'lag_12': ts_extended['y'].iloc[-(BACKTEST_MONTHS - i) - 12],
                }
                pred = rf.predict(pd.DataFrame([feats]))[0]
                rf_test_pred.append(pred)

            future_dates = pd.date_range(last_real_date + pd.DateOffset(months=1), periods=n_future, freq='ME')
            ts_proj = ts.copy()
            rf_future_pred = []
            for j, fd in enumerate(future_dates):
                feats = {
                    'month': fd.month, 'year': fd.year,
                    't': len(ts) + j,
                    'lag_1':  ts_proj['y'].iloc[-1],
                    'lag_2':  ts_proj['y'].iloc[-2],
                    'lag_3':  ts_proj['y'].iloc[-3],
                    'lag_6':  ts_proj['y'].iloc[-6],
                    'lag_12': ts_proj['y'].iloc[-12] if len(ts_proj) >= 12 else ts_proj['y'].mean(),
                }
                pred = rf.predict(pd.DataFrame([feats]))[0]
                rf_future_pred.append(pred)
                ts_proj = pd.concat([ts_proj, pd.DataFrame({'ds': [fd], 'y': [pred]})], ignore_index=True)

            rf_future_df = pd.DataFrame({'ds': future_dates, 'yhat': rf_future_pred})

            mae_p  = mean_absolute_error(test['y'], prophet_test_pred)
            rmse_p = math.sqrt(mean_squared_error(test['y'], prophet_test_pred))
            mae_rf = mean_absolute_error(test['y'], rf_test_pred)
            rmse_rf = math.sqrt(mean_squared_error(test['y'], rf_test_pred))

            # ── Save all results to session_state so they persist across reruns ────────
            st.session_state['ia_results'] = {
                'train': train,
                'test': test,
                'prophet_test_pred': prophet_test_pred,
                'rf_test_pred': rf_test_pred,
                'prophet_future': prophet_future,
                'rf_future_df': rf_future_df,
                'model_name_prophet': model_name_prophet,
                'mae_p': mae_p, 'rmse_p': rmse_p,
                'mae_rf': mae_rf, 'rmse_rf': rmse_rf,
                'last_real_date': last_real_date,
            }

    # ── Chart section renders from session_state (persists across multiselect changes) ─
    if 'ia_results' in st.session_state:
        r = st.session_state['ia_results']
        train              = r['train']
        test               = r['test']
        prophet_test_pred  = r['prophet_test_pred']
        rf_test_pred       = r['rf_test_pred']
        prophet_future     = r['prophet_future']
        rf_future_df       = r['rf_future_df']
        model_name_prophet = r['model_name_prophet']
        mae_p              = r['mae_p']
        rmse_p             = r['rmse_p']
        mae_rf             = r['mae_rf']
        rmse_rf            = r['rmse_rf']
        last_real_date     = r['last_real_date']

        # ── Series Selector (outside button block → survives reruns) ──────────────
        st.markdown("#### Séries Visíveis")
        series_options = [
            "Histórico (Treino)",
            "Real (Backtest)",
            f"{model_name_prophet} - Backtest",
            "RandomForest - Backtest",
            f"{model_name_prophet} → Dez/2027",
            f"IC {model_name_prophet}",
            "RandomForest → Dez/2027",
        ]
        series_sel = st.multiselect(
            "Escolha quais séries exibir no gráfico:",
            options=series_options,
            default=series_options,
            key="ia_series_selector"
        )

        # ── Chart ─────────────────────────────────────────────────────────────────
        bg_color    = colors['background']
        text_color  = colors['text_main']
        spine_color = "#e2e8f0" if theme_key == "light" else "#334155"
        grid_color  = "#cbd5e1" if theme_key == "light" else "#1e293b"

        fig, ax = plt.subplots(figsize=(13, 6))
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color, which='both', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(spine_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)

        if "Histórico (Treino)" in series_sel:
            ax.plot(train['ds'], train['y'], color=colors['primary'], linewidth=2, label='Histórico (treino)')
        if "Real (Backtest)" in series_sel:
            ax.plot(test['ds'], test['y'], color=text_color, linewidth=2, linestyle='--', marker='o', markersize=3, label='Real (backtest)')
        if f"{model_name_prophet} - Backtest" in series_sel:
            ax.plot(test['ds'], prophet_test_pred, color=colors['accent_red'], linewidth=1.8, linestyle='-.', marker='s', markersize=3, label=f'{model_name_prophet} backtest (MAE={mae_p:.1f})')
        if "RandomForest - Backtest" in series_sel:
            ax.plot(test['ds'], rf_test_pred, color=colors['accent_green'], linewidth=1.8, linestyle=':', marker='^', markersize=3, label=f'RandomForest backtest (MAE={mae_rf:.1f})')
        if f"{model_name_prophet} → Dez/2027" in series_sel:
            ax.plot(prophet_future['ds'], prophet_future['yhat'], color=colors['accent_red'], linewidth=2.5, label=f'{model_name_prophet} → Dez/2027')
        if f"IC {model_name_prophet}" in series_sel:
            ax.fill_between(prophet_future['ds'], prophet_future['yhat_lower'], prophet_future['yhat_upper'], alpha=0.45, color=colors['accent_red'], label=f'IC {model_name_prophet}')
        if "RandomForest → Dez/2027" in series_sel:
            ax.plot(rf_future_df['ds'], rf_future_df['yhat'], color=colors['accent_green'], linewidth=2.5, label='RandomForest → Dez/2027')

        ax.axvline(x=train['ds'].max(), color=spine_color, linestyle=':', linewidth=1.5, alpha=0.9)
        ax.axvline(x=last_real_date, color=spine_color, linestyle='--', linewidth=1.5, alpha=0.9)

        ax.set_title('Backtesting e Projeção até Dez/2027', fontsize=13, fontweight='bold', color=colors['primary'], pad=14)
        ax.grid(axis='y', alpha=0.18, color=grid_color, linestyle='--')
        plt.xticks(rotation=30, ha='right', fontsize=8, color=text_color)
        plt.yticks(fontsize=8, color=text_color)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            legend = ax.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=4, fontsize=8, framealpha=0.0, facecolor=bg_color)
            plt.setp(legend.get_texts(), color=text_color)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # ── Métricas ──────────────────────────────────────────────────────────────
        m1, m2 = st.columns(2)
        with m1:
            st.metric(f"MAE {model_name_prophet}", f"{mae_p:.1f}")
            st.metric(f"RMSE {model_name_prophet}", f"{rmse_p:.1f}")
        with m2:
            st.metric("MAE RandomForest", f"{mae_rf:.1f}")
            st.metric("RMSE RandomForest", f"{rmse_rf:.1f}")

        st.markdown("### Projeção até Dez/2027")
        proj_df = prophet_future[['ds','yhat']].rename(columns={'yhat': model_name_prophet})
        proj_df['RandomForest'] = rf_future_df['yhat'].values
        proj_df['ds'] = proj_df['ds'].dt.strftime('%b/%Y')
        st.dataframe(proj_df, use_container_width=True)

        st.info("""
        **Guia Rápido dos Resultados:**
        *   **Histórico (Treino):** Dados reais usados para ensinar os modelos.
        *   **Real (Backtest):** Dados reais ocultados do treino para testar a precisão.
        *   **Modelos (Prophet/RandomForest):** Algoritmos que preveem tendências futuras.
        *   **IC (Intervalo de Confiança):** Margem de erro esperada (área sombreada).
        *   **Métricas de Performance:**
            *   **MAE (Erro Médio Absoluto):** Em média, quantas notificações erramos (quanto menor, melhor).
            *   **RMSE (Raiz do Erro Quadrático Médio):** Similar ao MAE, mas penaliza mais erros grandes, detectando picos atípicos.
        """)

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("""
* **Segmentação PCA:** Ao agrupar os dados por idade e macrorregião (em vez de 27 UFs isoladas), o gráfico se torna mais coeso, permitindo enxergar agrupamentos demográficos consolidados e reduzindo o ruído visual percebido (Overplotting).
* **Modelo Random Forest (Drivers):** Essa análise identifica as "Features Importances". Ela revela quais atributos estatísticos da gestante (como a região ou o acesso ao pré-natal) são os maiores "culpados" pelas ocorrências ou atrasos de notificação verificados no modelo preditivo.
* **Projeção Híbrida (Prophet vs RF):** Ao executar a inferência de longo prazo no botão, o sistema roda dois algoritmos simultaneamente para criar um *ensemble* estatístico. Isso gera duas visões do futuro (geralmente Prophet captura melhor sazonalidades puras e RF captura melhor auto-regressão complexa), oferecendo ao gestor público um intervalo de variação para planejamento de políticas de saúde.
    """)

def render_matriz(filtered_df, theme_key="light"):

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

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights sobre a Tabela de Microdados)**")

def render_cascata(filtered_df, theme_key="light"):
    colors = THEMES[theme_key]
    st.markdown("### Adesão ao Pré-Natal e Cascata de Prevenção")
    st.info("Acompanhamento longitudinal das etapas desde o diagnóstico no SINAN até o momento ideal do parto.")
    
    df = filtered_df.copy()
    
    # Checar se as colunas necessárias existem com base no loader original minúsculo do db
    for col in ['pre_prenat', 'pre_antret', 'par_antidu']:
        if col not in df.columns:
            st.warning(f"Coluna necessária '{col}' não encontrada para gerar o funil de retenção.")
            return

    # Limpando os dados para garantir formato numérico temporário 
    df['pre_prenat_num'] = pd.to_numeric(df['pre_prenat'], errors='coerce').fillna(0)
    df['pre_antret_num'] = pd.to_numeric(df['pre_antret'], errors='coerce').fillna(0)
    df['par_antidu_num'] = pd.to_numeric(df['par_antidu'], errors='coerce').fillna(0)
    
    # O dataframe principal em views já vem com a coluna 'regiao' do data_loader
    if 'regiao' not in df.columns:
        df['regiao'] = 'Geral'
    else:
        df = df[df['regiao'] != 'Ignorado']

    # Fases do funil de prevenção
    fases_nomes = [
        '1. Diagnóstico', 
        '2. Pré-Natal', 
        '3. TARV na<br>Gestação', 
        '4. ARV no<br>Parto (Ideal)'
    ]
    
    resultados = []
    
    # Calcular as etapas para CADA Região
    for regiao in df['regiao'].unique():
        df_reg = df[df['regiao'] == regiao]
        
        # Etapas Absolutas
        total_gest = len(df_reg)
        fez_prenatal = len(df_reg[df_reg['pre_prenat_num'] == 1])
        prenatal_e_tarv = len(df_reg[(df_reg['pre_prenat_num'] == 1) & (df_reg['pre_antret_num'] == 1)])
        fluxo_completo = len(df_reg[(df_reg['pre_prenat_num'] == 1) & (df_reg['pre_antret_num'] == 1) & (df_reg['par_antidu_num'] == 1)])
        
        quantidades = [total_gest, fez_prenatal, prenatal_e_tarv, fluxo_completo]
        
        for i, fase in enumerate(fases_nomes):
            resultados.append({
                'Regiao': regiao,
                'Etapa de Prevenção': fase,
                'Número de Gestantes': quantidades[i]
            })

    if not resultados:
        st.warning("Sem dados válidos de retenção na seleção atual.")
        return

    # Criar o DataFrame consolidado final
    df_cascata = pd.DataFrame(resultados)
    
    # Ordenar as regiões e as etapas cronológicas
    df_cascata['Etapa de Prevenção'] = pd.Categorical(df_cascata['Etapa de Prevenção'], categories=fases_nomes, ordered=True)
    ordem_regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
    
    # O Plotly constrói o funil
    fig = px.funnel(
        df_cascata, 
        y='Etapa de Prevenção', 
        x='Número de Gestantes', 
        color='Regiao',
        template='plotly_dark' if theme_key == 'dark' else 'plotly_white',
        category_orders={"Regiao": ordem_regioes},
        color_discrete_sequence=px.colors.qualitative.Plotly,
        labels={'Número de Gestantes': 'Absoluto de Gestantes', 'Etapa de Prevenção': 'Etapas'}
    )
    
    # Customizando layout
    fig.update_layout(
        legend_title_text='Região do Brasil',
        hovermode="y unified",
        margin={"r":0,"t":20,"l":0,"b":0}
    )
    
    # Formatando o texto de cada barra para mostrar apenas as porcentagens (visão limpa)
    # E movendo a explicação completa absoluta para a caixa flutuante (hover)
    fig.update_traces(
        texttemplate='<b>%{percentInitial:.1%}</b><br>(%{percentPrevious:.1%})', 
        textposition='inside',
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Gestantes nesta etapa: %{value}<br>"
            "Retenção Total (desde o Início): %{percentInitial:.1%}<br>"
            "Retenção vs. Etapa Anterior: %{percentPrevious:.1%}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(format_fig(fig, theme_name=theme_key, legend_horiz=True), use_container_width=True)

    st.markdown("---")
    st.markdown('<h3 style="display: flex; align-items: center;"><span class="material-symbols-outlined" style="margin-right: 0.5rem; color: var(--primary);">tips_and_updates</span> Insights</h3>', unsafe_allow_html=True)
    st.markdown("**(Espaço reservado para documentação de insights sobre a Cascata de Prevenção)**")
