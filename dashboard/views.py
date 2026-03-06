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
    st.markdown("**Projeção de Longo Prazo (Prophet & RandomForest)**")
    if st.button("Executar Inferência Temporal Larga (Dez/2027)", type="primary"):
        with st.spinner("Treinando algoritmos (Prophet & RandomForest)..."):
            import warnings; warnings.filterwarnings('ignore')
            
            # ── 1. Série temporal mensal completa ────────────────────────────────────────
            ts = filtered_df.resample('ME', on='dt_notific').size().reset_index()
            ts.columns = ['ds', 'y']
            ts = ts.sort_values('ds').reset_index(drop=True)

            BACKTEST_MONTHS = 12
            END_PROJ       = pd.Timestamp('2027-12-31')

            train = ts.iloc[:-BACKTEST_MONTHS].copy()
            test  = ts.iloc[-BACKTEST_MONTHS:].copy()

            # ── 2. Número de meses de projeção futura (depois do teste) ──────────────────
            last_real_date = ts['ds'].max()
            n_future = (END_PROJ.year - last_real_date.year) * 12 + (END_PROJ.month - last_real_date.month)

            # ── 3. PROPHET (ou Holt-Winters como fallback) ────────────────────────────────
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

            # ── 4. RANDOM FOREST ──────────────────────────────────────────────────────────
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

            # Previsão walkforward para o período de teste
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

            # Projeção futura walkforward RF
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

            # ── 5. Métricas ───────────────────────────────────────────────────────────────
            mae_p  = mean_absolute_error(test['y'], prophet_test_pred)
            rmse_p = math.sqrt(mean_squared_error(test['y'], prophet_test_pred))
            mae_rf = mean_absolute_error(test['y'], rf_test_pred)
            rmse_rf = math.sqrt(mean_squared_error(test['y'], rf_test_pred))

            # ── 6. GRÁFICO (Matplotlib no Streamlit) ──────────────────────────────────────
            fig, ax = plt.subplots(figsize=(12, 6))

            # Histórico (treino)
            ax.plot(train['ds'], train['y'], color='steelblue', linewidth=2, label='Histórico (treino)')

            # Real (teste)
            ax.plot(test['ds'], test['y'], color='black', linewidth=2.5, linestyle='--', marker='o', markersize=4, label='Real (backtest)')

            # Previsão backtesting - Prophet/HW
            ax.plot(test['ds'], prophet_test_pred, color='darkorange', linewidth=2, linestyle='-.', marker='s', markersize=4,
                    label=f'{model_name_prophet} backtest (MAE={mae_p:.1f})')

            # Previsão backtesting - RF
            ax.plot(test['ds'], rf_test_pred, color='green', linewidth=2, linestyle=':', marker='^', markersize=4,
                    label=f'RandomForest backtest (MAE={mae_rf:.1f})')

            # Projeção futura - Prophet/HW (com IC)
            ax.plot(prophet_future['ds'], prophet_future['yhat'], color='darkorange', linewidth=2.5, linestyle='-',
                    label=f'{model_name_prophet} → Dez/2027')
            ax.fill_between(prophet_future['ds'], prophet_future['yhat_lower'], prophet_future['yhat_upper'],
                            alpha=0.15, color='darkorange', label='IC ' + model_name_prophet)

            # Projeção futura - RF
            ax.plot(rf_future_df['ds'], rf_future_df['yhat'], color='green', linewidth=2.5, linestyle='-',
                    label='RandomForest → Dez/2027')

            ax.axvline(x=train['ds'].max(), color='gray', linestyle=':', linewidth=1.5, alpha=0.8)
            ax.axvline(x=last_real_date, color='dimgray', linestyle='--', linewidth=1.5, alpha=0.8)
            
            ax.set_title('Início Backtesting e Projeção até Dez/2027', fontsize=12, fontweight='bold')
            ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
            ax.grid(axis='y', alpha=0.3)
            plt.xticks(rotation=45)
            st.pyplot(fig)

            # Exibição de Métricas e Tabela
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

            # ── 7. EXPLICAÇÃO DO MODELO ─────────────────────────────────────────────
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
