import json
import uuid

notebook_path = "notebooks/HIV-Gestante-Completo.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Cell 1: Filter 2024 data (it's cell with index 4, let's search it by content)
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and "pd.read_csv" in "".join(cell['source']):
        source_code = cell['source']
        matches = [idx for idx, line in enumerate(source_code) if "data_raw = pd.read_csv(" in line]
        
        if matches:
            idx = matches[0]
            new_source = source_code[:idx+1]
            new_source.append("\n")
            new_source.append("    # --- FILTRO 2024 OBRIGATÓRIO: Trabalhar com dados somente até Dezembro de 2023 ---\n")
            new_source.append("    data_raw = data_raw[data_raw['NU_ANO'] < 2024].copy()\n")
            new_source.extend(source_code[idx+1:])
            cell['source'] = new_source
        break


# Cell 2: Update Projections config
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and "BACKTEST_MONTHS" in "".join(cell['source']):
        source_code = "".join(cell['source'])
        
        # Replace hardcoded lengths
        source_code = source_code.replace("BACKTEST_MONTHS = 6", "BACKTEST_MONTHS = 12")
        source_code = source_code.replace("END_PROJ       = pd.Timestamp('2026-12-31')", "END_PROJ       = pd.Timestamp('2027-12-31')")
        
        # Replace occurrences in graph titles and prints
        source_code = source_code.replace("Dez/2026", "Dez/2027")
        source_code = source_code.replace("backtest 6 meses", "backtest 12 meses")
        
        # Update specific RF split condition (if any needed). We check line by line and reinsert.
        # But `.replace` over the string should cover it.
        # We split it back to list to write it correctly.
        cell['source'] = [line + '\n' for line in source_code.split('\n')]
        # Clean trailing empty newline added by split
        cell['source'][-1] = cell['source'][-1].rstrip('\n')
        break


with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write('\n')

print("Notebook atualizado com sucesso!")
