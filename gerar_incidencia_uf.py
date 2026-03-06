import pandas as pd
import os
import requests
import plotly.express as px

def gerar_grafico_incidencia():
    # Caminhos possíveis para o arquivo de dados do SINAN
    filepaths = [
        r'c:\Users\franc\Desktop\Desafio 2\Desafio_Relampago_Analytics\data\HIV-Gestante-2018-2024.csv',
        r'data\HIV-Gestante-2018-2024.csv',
        r'..\data\HIV-Gestante-2018-2024.csv'
    ]
    
    df = None
    for path in filepaths:
        if os.path.exists(path):
            try:
                # O CSV usa separador ',' e enconding latin1
                df = pd.read_csv(path, sep=',', encoding='latin1', low_memory=False)
                break
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")
                
    if df is None:
        print("Arquivo de dados não encontrado nos caminhos mapeados.")
        return

    # Mapeamento do Código IBGE da UF (SG_UF_NOT) para a Sigla do Estado
    mapa_estados = {
        '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
        '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
        '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
        '41': 'PR', '42': 'SC', '43': 'RS',
        '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
    }
    
    df['SG_UF_NOT'] = df['SG_UF_NOT'].astype(str).str.split('.').str[0] # Garantir string limpa
    df['Estado'] = df['SG_UF_NOT'].map(mapa_estados)

    # 1. Obter o número absoluto de CASOS de HIV por UF
    casos_por_estado = df['Estado'].value_counts().reset_index()
    casos_por_estado.columns = ['Estado', 'Total_Casos']

    # 2. Dados de População Estimada IBGE (Projeção Brasil / Censo 2022 em milhares/milhões)
    # Valores em número absoluto de habitantes (aprox)
    populacao_ibge = {
        'SP': 44411238, 'MG': 20538718, 'RJ': 16054524, 'BA': 14141626, 'PR': 11444380,
        'RS': 10882965, 'PE': 9058931, 'CE': 8733687, 'PA': 8120131, 'SC': 7610361,
        'GO': 7056495, 'MA': 6775805, 'PB': 3974687, 'AM': 3941613, 'ES': 3833712,
        'MT': 3658649, 'RN': 3302729, 'PI': 3271199, 'AL': 3127683, 'DF': 2817381,
        'MS': 2757013, 'SE': 2209558, 'RO': 1581196, 'TO': 1511460, 'AC': 830018,
        'AP': 733759, 'RR': 636303
    }
    
    # Adicionar o dado da tabela do Censo (população total do estado)
    df_populacao = pd.DataFrame(list(populacao_ibge.items()), columns=['Estado', 'Populacao'])
    
    # 3. Cruzar Casos com a População (Merge)
    df_final = pd.merge(casos_por_estado, df_populacao, on='Estado')
    
    # 4. Cálculo de Incidência Relativa
    # A métrica padrão de saúde pública é "Taxa por 100.000 habitantes" ou "por 10 mil"
    # Fazer porcentagem pura (0.0001%) fica ruim de ler. O padrão é Casos / 100 mil habitantes.
    df_final['Taxa_por_100k'] = (df_final['Total_Casos'] / df_final['Populacao']) * 100000
    
    # Para atender a sua requisição estrita sobre %, podemos também exibir assim:
    df_final['Porcentagem_da_Pop (%)'] = (df_final['Total_Casos'] / df_final['Populacao']) * 100
    
    # Ordenar o Estado pela Maior Taxa de Incidência (O mais perigoso proporcionalmente no topo)
    df_final = df_final.sort_values(by='Taxa_por_100k', ascending=False)
    
    # Recuperando o código numérico IBGE (SG_UF_NOT) para o Plotly cruzar com o geojson
    mapa_estados_inv = {v: k for k, v in mapa_estados.items()}
    df_final['SG_UF_NOT'] = df_final['Estado'].map(mapa_estados_inv)
    
    # 5. Visualização (Mapa do Brasil - Coroplético)
    print("Baixando malha geográfica do Brasil na API do IBGE...")
    try:
        # Puxa o polígono dos estados do Brasil usando a API oficial do IBGE para Plotly
        url_geojson = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
        brazil_geojson = requests.get(url_geojson).json()
    except Exception as e:
        print(f"Erro ao carregar o mapa do IBGE: {e}")
        return

    print("Renderizando Mapa...")
    # Montando a visualização geográfica
    # Precisamos ligar nosso DataFrame ao ID retornado no JSON. 
    # O JSON do IBGE tem 'codarea', então ligamos pelo SG_UF_NOT
    fig_map = px.choropleth(
        df_final, 
        geojson=brazil_geojson, 
        locations="SG_UF_NOT",          # Usar o código numérico
        featureidkey="properties.codarea",
        color="Porcentagem_da_Pop (%)", 
        color_continuous_scale="Reds", 
        scope="south america",
        title="Onde o HIV em Gestantes é Mais Frequente?<br><sup>Incidência Proporcional ao Tamanho da População (Ajuste Demográfico)</sup>",
        hover_name="Estado",
        hover_data={
            'SG_UF_NOT': False, # Esconder o ID técnico no hover
            'Porcentagem_da_Pop (%)': ':.4f',
            'Taxa_por_100k': ':.1f',
            'Total_Casos': True
        },
        labels={
            'Porcentagem_da_Pop (%)': '% da População',
            'Taxa_por_100k': 'Casos/100 mil hab.'
        }
    )
    
    # Zoom e fit exclusivamente no Brasil
    fig_map.update_geos(fitbounds="locations", visible=False)
    
    # Ajustar layout
    fig_map.update_layout(
        margin={"r":0,"t":50,"l":0,"b":0}, 
        coloraxis_colorbar=dict(title="Ocorrência (%)")
    )
    
    # Exibir no Navegador Local
    fig_map.show()

if __name__ == "__main__":
    gerar_grafico_incidencia()
