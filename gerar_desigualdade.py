import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

def gerar_grafico_desigualdade():
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
                # O CSV usa separador ',' e enconding latin1
                df = pd.read_csv(path, sep=',', encoding='latin1', low_memory=False)
                print(f"Dados carregados com sucesso: {path}")
                break
            except Exception as e:
                print(f"Erro ao ler {path}: {e}")
                
    if df is None:
        print("Arquivo de dados não encontrado nos caminhos mapeados.")
        return

    # Limpar as colunas de análise
    df['CS_ESCOL_N'] = pd.to_numeric(df['CS_ESCOL_N'], errors='coerce')
    df['PRE_ANTRET'] = pd.to_numeric(df['PRE_ANTRET'], errors='coerce')

    # Dicionário de conversão de escolaridade do SINAN
    # Agrupamos as categorias para o gráfico ficar mais fácil de ler e ter impacto estatístico
    mapa_escolaridade = {
        0: '1. Analfabeto',
        1: '2. Fundamental Incomp.',
        2: '3. Fundamental Comp.',
        3: '2. Fundamental Incomp.', # 5ª à 8ª série tbm entra aqui
        4: '3. Fundamental Comp.',
        5: '4. Ensino Médio',     # Incompleto entra aqui por simplificação
        6: '4. Ensino Médio',     # Completo
        7: '5. Ensino Superior',  # Incompleto
        8: '5. Ensino Superior',  # Completo
        9: 'Ignorado',
        10: 'Ignorado' # Não se aplica (ignorar para o funil)
    }
    
    df['Escolaridade'] = df['CS_ESCOL_N'].map(mapa_escolaridade)
    
    # Remover casos ignorados ou vazios para não poluir a análise central
    df_validos = df.dropna(subset=['Escolaridade', 'PRE_ANTRET'])
    df_validos = df_validos[df_validos['Escolaridade'] != 'Ignorado']

    # Focar apenas em quem TEM HIV (total) e ver a proporção de quem tomou o Remédio PRE_ANTRET == 1 (Sim)
    # Criamos uma tabela cruzada: Escolaridade (linhas) x Uso_De_Remedio (Colunas)
    tabela = pd.crosstab(df_validos['Escolaridade'], df_validos['PRE_ANTRET'])
    
    if 1 not in tabela.columns:
        print("Atenção: Nenhuma paciente registrada com Uso de TARV (PRE_ANTRET=1). Verifique os dados.")
        return

    # Calcular o percentual de sucesso (Quantas tomaram / Total daquele grupo de escolaridade)
    # O index 1 da crosstab representa "Sim, usou medicação"
    tabela['Total_Gestantes'] = tabela.sum(axis=1)
    tabela['Taxa_Acesso_Medicacao (%)'] = (tabela[1] / tabela['Total_Gestantes']) * 100
    
    # Ordenar a tabela pelo índice natural de escolaridade que deixamos numerado ('1.', '2.', etc)
    tabela = tabela.sort_index().reset_index()

    # Visualização: Gráfico de Barras Horizontais mostrando o sucesso no Acesso
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid", rc={"axes.facecolor":"#fcfcfc"})
    
    # Usamos uma paleta sequencial. Cores mais escuras = Menor escolaridade
    ax = sns.barplot(
        data=tabela, 
        y='Escolaridade', 
        x='Taxa_Acesso_Medicacao (%)', 
        hue='Escolaridade',
        legend=False,
        palette="viridis_r" # invertemos para o escuro ficar na base 'analfabeto'
    )
    
    # Detalhes visuais e limpeza
    plt.title("Acesso a Antirretrovirais (TARV) na Gestação por Escolaridade\n(O Peso da Desigualdade Social na Proteção Infantil)", 
              fontsize=15, fontweight='bold', pad=20)
    plt.ylabel("") 
    plt.xlabel("Taxa de Gestantes que Receberam a Medicação (%)", fontsize=12)
    plt.xlim(0, 105) # Esticando o Eixo X até 100% para mostrar onde está a "Falta"
    
    # Adicionando a porcentagem exata na ponta de cada barra
    for p in ax.patches:
        width = p.get_width()
        if width > 0:
            ax.annotate(
                f"{width:.1f}%", 
                (width, p.get_y() + p.get_height() / 2.), 
                ha='left', va='center', fontsize=12, fontweight='bold',
                xytext=(5, 0), textcoords='offset points'
            )
            
    plt.tight_layout()
    plt.show()

    # --- Análise 2: Acesso a Antirretrovirais (TARV) por Raça/Cor ---
    
    df['CS_RACA'] = pd.to_numeric(df['CS_RACA'], errors='coerce')
    
    mapa_raca = {
        1: 'Branca',
        2: 'Preta',
        3: 'Amarela',
        4: 'Parda',
        5: 'Indígena',
        9: 'Ignorado'
    }
    
    df['Raca_Cor'] = df['CS_RACA'].map(mapa_raca)
    
    # Remover casos ignorados
    df_raca_validos = df.dropna(subset=['Raca_Cor', 'PRE_ANTRET'])
    df_raca_validos = df_raca_validos[df_raca_validos['Raca_Cor'] != 'Ignorado']
    
    tabela_raca = pd.crosstab(df_raca_validos['Raca_Cor'], df_raca_validos['PRE_ANTRET'])
    
    if 1 in tabela_raca.columns:
        # Calcular o percentual de sucesso
        tabela_raca['Total_Gestantes'] = tabela_raca.sum(axis=1)
        tabela_raca['Taxa_Acesso_Medicacao (%)'] = (tabela_raca[1] / tabela_raca['Total_Gestantes']) * 100
        
        # Ordenar a tabela pelo maior eixo de acesso
        tabela_raca = tabela_raca.reset_index().sort_values(by='Taxa_Acesso_Medicacao (%)', ascending=False)
        
        # Visualização: Gráfico de Barras
        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid", rc={"axes.facecolor":"#fcfcfc"})
        
        ax_raca = sns.barplot(
            data=tabela_raca, 
            y='Raca_Cor', 
            x='Taxa_Acesso_Medicacao (%)', 
            hue='Raca_Cor',
            legend=False,
            palette="magma" 
        )
        
        plt.title("Acesso a Antirretrovirais (TARV) na Gestação por Raça/Cor\n(Desigualdade Étnico-Racial no Acesso à Saúde)", 
                  fontsize=15, fontweight='bold', pad=20)
        plt.ylabel("") 
        plt.xlabel("Taxa de Gestantes que Receberam a Medicação (%)", fontsize=12)
        plt.xlim(0, 105)
        
        for p in ax_raca.patches:
            width = p.get_width()
            if width > 0:
                ax_raca.annotate(
                    f"{width:.1f}%", 
                    (width, p.get_y() + p.get_height() / 2.), 
                    ha='left', va='center', fontsize=12, fontweight='bold',
                    xytext=(5, 0), textcoords='offset points'
                )
                
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    gerar_grafico_desigualdade()
