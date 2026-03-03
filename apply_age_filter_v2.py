import json

notebook_path = "notebooks/HIV-Gestante-Completo.ipynb"

# Ler o notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

inserted = False

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source_code = cell['source']
        
        # Verificar se esta célula tem o código que queremos
        matches = [idx for idx, line in enumerate(source_code) if "data[col] = pd.to_numeric(data[col], errors='coerce')" in line]
        
        if matches:
            idx = matches[0]
            new_source = source_code[:idx+1]
            new_source.append("\n")
            new_source.append("    # --- FILTRO DE IDADE OBRIGATORIO: Apenas mulheres de 10 a 55 anos (removendo outliers) ---\n")
            new_source.append("    # A idade padrao do DataSUS vem em formato codificado onde 4000+ sao anos\n")
            new_source.append("    # Isolamos apenas os anos e depois filtramos:\n")
            new_source.append("    data['IDADE_REAL_TEMP'] = data['NU_IDADE_N'].apply(lambda x: int(str(int(x))[1:4]) if pd.notnull(x) and x > 4000 else np.nan)\n")
            new_source.append("    data = data[(data['IDADE_REAL_TEMP'] >= 10) & (data['IDADE_REAL_TEMP'] <= 55)].copy()\n")
            new_source.append("    data.drop(columns=['IDADE_REAL_TEMP'], inplace=True)\n")
            new_source.append("    print(f\"\\nTotal de registros pós-filtro de idade (10 a 55 anos): {len(data)}\")\n")
            new_source.extend(source_code[idx+1:])
            
            cell['source'] = new_source
            inserted = True
            break

if inserted:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print("Notebook atualizado com sucesso!")
else:
    print("Não encontrou o local para inserir o código.")
