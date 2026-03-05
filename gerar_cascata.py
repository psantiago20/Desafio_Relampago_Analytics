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
    
    # Visualização: Gráfico de Barras Agrupadas
    plt.figure(figsize=(14, 8))
    sns.set_theme(style="whitegrid", rc={"axes.facecolor":"#f9f9f9"})
    
    # Em vez de volume bruto, vamos plotar a '%' para comparar regiões desiguais num funil justo
    ax = sns.barplot(
        data=df_cascata, 
        x='Etapa de Prevenção', 
        y='Retenção (%)', 
        hue='Regiao',
        hue_order=ordem_regioes,
        palette='Set2'
    )
    
    # Customizando e limpando o gráfico
    plt.title("Cascata de Prevenção do HIV por Região do Brasil\n(Percentual Retido em Cada Etapa)", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("") 
    plt.ylabel("Taxa de Retenção (%)", fontsize=12, fontweight='bold')
    plt.ylim(0, 115) # Espaço superior para legendas não encavalarem
    
    # Legenda fora do gráfico principal
    plt.legend(title='Região', bbox_to_anchor=(1.02, 1), loc='upper left')
    
    # Adicionando os valores numéricos em cima de cada barra (somente a %)
    for p in ax.patches:
        height = p.get_height()
        if height > 0: # Não plota números nulos
            ax.annotate(
                f"{height:.0f}%", 
                (p.get_x() + p.get_width() / 2., height), 
                ha='center', va='bottom', fontsize=10,
                xytext=(0, 3), textcoords='offset points'
            )
            
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    gerar_cascata_prevencao()
