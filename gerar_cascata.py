import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os


def gerar_cascata_prevencao():
    # Caminhos possíveis para o arquivo de dados
    filepaths = [
        r'c:\Users\franc\Desktop\Desafio 2\Desafio_Relampago_Analytics\data\HIV-Gestante-2018-2024.csv',
        r'data\HIV-Gestante-2018-2024.csv',
        r'..\data\HIV-Gestante-2018-2024.csv'
    ]
    
    df = None
    for path in filepaths:
        if os.path.exists(path):
            try:
                # O CSV parece estar separado por vírgula (,) e não ponto-e-vírgula (;)
                df = pd.read_csv(path, sep=',', encoding='latin1', low_memory=False)
                print(f"Dados carregados com sucesso: {path}")
                break
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")
                
    if df is None:
        print("Arquivo de dados não encontrado nos caminhos mapeados.")
        return

    # Limpando os dados para garantir formato numérico (tratando NAs e espaços vazios como algo diferente de 1)
    df['PRE_PRENAT'] = pd.to_numeric(df['PRE_PRENAT'], errors='coerce').fillna(0)
    df['PRE_ANTRET'] = pd.to_numeric(df['PRE_ANTRET'], errors='coerce').fillna(0)
    df['PAR_ANTIDU'] = pd.to_numeric(df['PAR_ANTIDU'], errors='coerce').fillna(0)
    
    # 1. Função para extrair a região a partir do código IBGE do estado (SG_UF_NOT)
    def map_regiao(uf_cod):
        try:
            primeiro_digito = str(int(uf_cod))[0]
            regioes = {
                '1': 'Norte',
                '2': 'Nordeste',
                '3': 'Sudeste',
                '4': 'Sul',
                '5': 'Centro-Oeste'
            }
            return regioes.get(primeiro_digito, 'Outros/Ignorado')
        except:
            return 'Outros/Ignorado'

    # Criar a coluna de Região baseada no estado de notificação
    df['Regiao'] = df['SG_UF_NOT'].apply(map_regiao)
    
    # Remover casos sem região definida (ou de outros países)
    df = df[df['Regiao'] != 'Outros/Ignorado']

    # Fases do funil de prevenção
    fases_nomes = [
        '1. Diagnóstico', 
        '2. Pré-Natal', 
        '3. TARV na\nGestação', 
        '4. ARV no\nParto (Ideal)'
    ]
    
    # Lista para acumular os resultados por região
    resultados = []
    
    # Calcular as etapas para CADA Região
    for regiao in df['Regiao'].unique():
        df_reg = df[df['Regiao'] == regiao]
        
        # Etapas
        total_gest = len(df_reg)
        fez_prenatal = len(df_reg[df_reg['PRE_PRENAT'] == 1])
        prenatal_e_tarv = len(df_reg[(df_reg['PRE_PRENAT'] == 1) & (df_reg['PRE_ANTRET'] == 1)])
        fluxo_completo = len(df_reg[(df_reg['PRE_PRENAT'] == 1) & (df_reg['PRE_ANTRET'] == 1) & (df_reg['PAR_ANTIDU'] == 1)])
        
        quantidades = [total_gest, fez_prenatal, prenatal_e_tarv, fluxo_completo]
        
        # Percentuais relativos ao total inicial (Diagnóstico) da DAQUELA região
        # Para evitar divisão por zero, checamos o total_gest
        percentuais = [(q / total_gest * 100) if total_gest > 0 else 0 for q in quantidades]
        
        for i, fase in enumerate(fases_nomes):
            resultados.append({
                'Regiao': regiao,
                'Etapa de Prevenção': fase,
                'Número de Gestantes': quantidades[i],
                'Retenção (%)': percentuais[i]
            })

    # Criar o DataFrame consolidado final
    df_cascata = pd.DataFrame(resultados)
    
    # Ordenar as regiões e as etapas (para o gráfico não misturar a ordem cronológica)
    df_cascata['Etapa de Prevenção'] = pd.Categorical(df_cascata['Etapa de Prevenção'], categories=fases_nomes, ordered=True)
    ordem_regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
    
    import plotly.express as px
    
    # O Plotly Exige que a ordenação das categorias seja respeitada na renderização
    # Ele também constrói o funil naturalmente de cima para baixo
    fig = px.funnel(
        df_cascata, 
        y='Etapa de Prevenção', 
        x='Número de Gestantes', 
        color='Regiao',
        template='plotly_white',
        title="Cascata de Prevenção do HIV por Região do Brasil (Funil de Retenção)",
        labels={'Número de Gestantes': 'Absoluto de Gestantes', 'Etapa de Prevenção': 'Etapas'}
    )
    
    # Customizando layout para ficar visualmente incrível
    fig.update_layout(
        title_font=dict(size=20),
        legend_title_text='Região do Brasil',
        # Configurar para que hover mostre todas as informações alinhadas
        hovermode="y unified"
    )
    
    # Formatando o texto de cada barra para mostrar apenas as porcentagens (visão limpa)
    # E movendo a explicação completa absoluta para a caixa flutuante (hover)
    fig.update_traces(
        texttemplate='<b>%{percentInitial:.1%}</b><br>(%{percentPrevious:.1%})', 
        textposition='inside',
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Gestantes nesta etapa: %{value}<br>"
            "Retenção Total (desde o início): %{percentInitial:.1%}<br>"
            "Retenção vs. Etapa Anterior: %{percentPrevious:.1%}"
            "<extra></extra>"
        )
    )

    # Abre o gráfico no navegador de forma interativa
    fig.show()

if __name__ == "__main__":
    gerar_cascata_prevencao()
