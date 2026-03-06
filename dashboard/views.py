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
            line=dict(width=3, color=COLORS['primary']),
            fillcolor='rgba(26, 54, 93, 0.1)', name="Casos Mensais"
        ))
        
        fig_line.add_trace(go.Scatter(
            x=ts['dt_notific'], y=ts['Tendencia_MA6'], mode='lines',
            line=dict(width=2.5, color=COLORS['warning'], dash='dash'),
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
                    st.plotly_chart(format_fig(fig_esc_desig, legend_horiz=False), use_container_width=True)
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
                    st.plotly_chart(format_fig(fig_raca_desig, legend_horiz=False), use_container_width=True)
                else:
                    st.warning("Sem dados conclusivos de acesso a TARV neste recorte.")


def render_cartografia(filtered_df, brazil_geojson):
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
                color="Notificacoes", color_continuous_scale="Blues", scope="south america",
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
            color_continuous_scale="Blues"
        )
        fig_top_abs.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_top_abs, legend_horiz=False), use_container_width=True)

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
                color_continuous_scale="YlOrBr", # Usando variações de amarelo/laranja
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
            color_continuous_scale="YlOrBr", # Usando variações de amarelo/laranja
            labels={"Incidencia_100k": "Casos por 100k hab."}
        )
        fig_top_rel.update_layout(coloraxis_showscale=False)
        st.plotly_chart(format_fig(fig_top_rel, legend_horiz=False), use_container_width=True)


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

def render_cascata(filtered_df):
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
        template='plotly_white',
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

    st.plotly_chart(format_fig(fig, legend_horiz=True), use_container_width=True)
