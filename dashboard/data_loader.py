import streamlit as st
import pandas as pd
import numpy as np
import urllib.request
import json
import os

@st.cache_data
def get_brazil_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    try:
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except:
        return None

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "HIV-Gestante-2018-2024.csv")
    
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    df = pd.read_csv(file_path, low_memory=False)
    df.columns = df.columns.str.lower()
    
    date_cols = ['dt_notific', 'dt_diag', 'dt_nasc']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
            
    df = df.dropna(subset=["dt_notific"])
    df["ano_notific"] = df["dt_notific"].dt.year
    df["mes_notificacao"] = df["dt_notific"].dt.month
    df = df[df["ano_notific"] <= 2023]
    
    raca_map = {1: 'Branca', 2: 'Preta', 3: 'Amarela', 4: 'Parda', 5: 'Indígena', 9: 'Ignorado'}
    if 'cs_raca' in df.columns:
        df['raca'] = df['cs_raca'].map(raca_map).fillna('Ignorado')
    
    escol_map = {
        0: 'Sem instrução/escolaridade', 
        1: 'Fundamental incompleto', 
        2: 'Fundamental incompleto', 
        3: 'Fundamental incompleto', 
        4: 'Fundamental completo', 
        5: 'Médio incompleto', 
        6: 'Médio completo', 
        7: 'Superior incompleto', 
        8: 'Superior completo', 
        9: 'Ignorado'
    }
    if 'cs_escol_n' in df.columns:
        df['escolaridade'] = df['cs_escol_n'].map(escol_map).fillna('Ignorado')
    
    diag_map = {1: 'Antes Pré-Natal', 2: 'Durante Pré-Natal', 3: 'Durante o parto', 4: 'Após parto', 9: 'Ignorado'}
    if 'pre_prenat' in df.columns:
        df['momento_diagnostico'] = df['pre_prenat'].map(diag_map).fillna('Ignorado')

    parto_map = {1: 'Vaginal', 2: 'Cesáreo', 3: 'Ignorado', 4: 'Ignorado', 9: 'Ignorado'}
    if 'par_tipo' in df.columns:
        df['tipo_parto'] = df['par_tipo'].map(parto_map).fillna('Ignorado')

    if 'dt_diag' in df.columns:
        df['atraso_dias'] = (df['dt_notific'] - pd.to_datetime(df['dt_diag'], errors='coerce')).dt.days

    if 'nu_idade_n' in df.columns:
        df['idade_real'] = df['nu_idade_n'].apply(lambda x: x-4000 if (x is not None and x >= 4000) else x)
        df.loc[(df['idade_real'] < 10) | (df['idade_real'] > 55), 'idade_real'] = np.nan
        df['idade_anos'] = df['idade_real'] # Keep compatibility for other charts
        
        bins = [10, 19, 29, 39, 100] # 100 to ensure we catch all up to 55+
        labels = ['Adolescente (10 - 19 anos)', 'Jovem Adulta (20 - 29 anos)', 'Adulta (30 - 39 anos)', 'Adulta (acima de 40)']
        df['idade_categoria'] = pd.cut(df['idade_real'], bins=bins, labels=labels)

    uf_map = {
        11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
        21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
        31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
        41: 'PR', 42: 'SC', 43: 'RS',
        50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
    }
    if 'sg_uf_not' in df.columns:
        df['uf'] = pd.to_numeric(df['sg_uf_not'], errors='coerce').map(uf_map).fillna('Ignorado')

    regioes = {
        'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
        'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
        'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
        'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
        'Sul': ['PR', 'RS', 'SC']
    }
    uf_to_reg = {uf: reg for reg, ufs in regioes.items() for uf in ufs}
    if 'uf' in df.columns:
        df['regiao'] = df['uf'].map(uf_to_reg).fillna('Ignorado')
        
        # IDH por Região (Valores aproximados baseados em dados recentes do PNUD)
        idh_map = {
            'Norte': 0.730,
            'Nordeste': 0.710,
            'Centro-Oeste': 0.789,
            'Sudeste': 0.796,
            'Sul': 0.792,
            'Ignorado': 0.750 # Valor médio do país como fallback
        }
        df['idh_regiao'] = df['regiao'].map(idh_map)

    # Cálculo da Taxa de Incidência por UF (per 100k habitantes)
    populacao_ibge = {
        'SP': 44411238, 'MG': 20538718, 'RJ': 16054524, 'BA': 14141626, 'PR': 11444380,
        'RS': 10882965, 'PE': 9058931, 'CE': 8733687, 'PA': 8120131, 'SC': 7610361,
        'GO': 7056495, 'MA': 6775805, 'PB': 3974687, 'AM': 3941613, 'ES': 3833712,
        'MT': 3658649, 'RN': 3302729, 'PI': 3271199, 'AL': 3127683, 'DF': 2817381,
        'MS': 2757013, 'SE': 2209558, 'RO': 1581196, 'TO': 1511460, 'AC': 830018,
        'AP': 733759, 'RR': 636303
    }
    casos_uf = df['uf'].value_counts().to_dict()
    df['taxa_incidencia'] = df['uf'].apply(lambda x: (casos_uf.get(x, 0) / populacao_ibge.get(x, 1)) * 100000 if x in populacao_ibge else 0)

    return df
