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
    df = df[df["ano_notific"] <= 2023]
    
    raca_map = {1: 'Branca', 2: 'Preta', 3: 'Amarela', 4: 'Parda', 5: 'Indígena', 9: 'Ignorado'}
    if 'cs_raca' in df.columns:
        df['raca'] = df['cs_raca'].map(raca_map).fillna('Ignorado')
    
    escol_map = {0: 'Sem Escolaridade', 1: 'Fund. I', 2: 'Fund. II', 3: 'Fund. II', 4: 'Fund. Comp.', 5: 'Med. Incomp.', 6: 'Med. Comp.', 7: 'Sup. Incomp.', 8: 'Sup. Comp.', 9: 'Ignorado'}
    if 'cs_escol_n' in df.columns:
        df['escolaridade'] = df['cs_escol_n'].map(escol_map).fillna('Ignorado')
    
    diag_map = {1: 'Pré-natal', 2: 'Parto', 3: 'Pós-parto', 4: 'Sem pré-natal', 9: 'Ignorado'}
    if 'pre_prenat' in df.columns:
        df['momento_diagnostico'] = df['pre_prenat'].map(diag_map).fillna('Ignorado')

    parto_map = {1: 'Vaginal', 2: 'Cesáreo', 3: 'Ignorado', 4: 'Ignorado', 9: 'Ignorado'}
    if 'par_tipo' in df.columns:
        df['tipo_parto'] = df['par_tipo'].map(parto_map).fillna('Ignorado')

    if 'dt_diag' in df.columns:
        df['atraso_dias'] = (df['dt_notific'] - pd.to_datetime(df['dt_diag'], errors='coerce')).dt.days

    if 'nu_idade_n' in df.columns:
        df['idade_anos'] = df['nu_idade_n'].apply(lambda x: x-4000 if x >= 4000 else x)
        df.loc[(df['idade_anos'] < 10) | (df['idade_anos'] > 55), 'idade_anos'] = np.nan
        
        bins = [10, 19, 29, 39, 55]
        labels = ['Adolescente (10-19)', 'Jovem (20-29)', 'Adulta (30-39)', 'Sênior (40+)']
        df['idade_categoria'] = pd.cut(df['idade_anos'], bins=bins, labels=labels)

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

    return df
