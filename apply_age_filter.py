import json

notebook_path = "notebooks/HIV-Gestante-Completo.ipynb"

# Ler o notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# A célula 6 (índice 6) contém "### 2. Tratamento e Identificação de Duplicatas"
# A célula 7 (índice 7) é o código para este tratamento
code_cell = nb['cells'][7]
source_code = code_cell['source']

# Inserir o novo código logo após carregar os dados brutos e converter colunas,
# mas antes da remoção das duplicadas e cálculo da data, 
# para que sirva "para toda a base" como pedido

# Vamos encontrar uma linha que faça sentido inserir o código.
# Pelo notebook:
# # Cuidar da conversão de variáveis numéricas necessárias (para posterior categorização)
# num_cols = ['ANT_EVLABO', 'PRE_PRENAT', 'PAR_TIPO', 'CS_RACA', 'CS_ESCOL_N', 'PAR_EVOLUC', 'NU_ANO', 'SG_UF', 'NU_IDADE_N']
# for col in num_cols:
#     data[col] = pd.to_numeric(data[col], errors='coerce')

# Logo após esse for, podemos filtrar a idade.

new_source = []
inserted = False
for line in source_code:
    new_source.append(line)
    if "data[col] = pd.to_numeric(data[col], errors='coerce')" in line:
        if not inserted:
            new_source.append("\n")
            new_source.append("# --- FILTRO DE IDADE OBRIGATORIO: Apenas mulheres de 10 a 55 anos (removendo outliers) ---\n")
            new_source.append("# A idade padrao do DataSUS vem em formato codificado onde 4000+ sao anos\n")
            new_source.append("# Isolamos apenas os anos e depois filtramos:\n")
            new_source.append("data['IDADE_REAL_TEMP'] = data['NU_IDADE_N'].apply(lambda x: int(str(int(x))[1:4]) if pd.notnull(x) and x > 4000 else np.nan)\n")
            new_source.append("data = data[(data['IDADE_REAL_TEMP'] >= 10) & (data['IDADE_REAL_TEMP'] <= 55)].copy()\n")
            new_source.append("data.drop(columns=['IDADE_REAL_TEMP'], inplace=True)\n")
            new_source.append("print(f\"\\nTotal de registros pós-filtro de idade (10 a 55 anos): {len(data)}\")\n")
            inserted = True

nb['cells'][7]['source'] = new_source

# Salvar o notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write('\n')

print("Notebook atualizado com sucesso!")
