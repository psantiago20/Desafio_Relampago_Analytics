import json

notebook_path = "notebooks/HIV-Gestante-Completo.ipynb"

# Ler o notebook
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Modificar a célula 1 (índice 1, pois 0 é o título)
if nb['cells'][1]['cell_type'] == 'markdown':
    nb['cells'][1]['source'] = [
        "## 1. Importação de Bibliotecas e Configurações\n",
        "Nesta etapa, importamos todas as bibliotecas necessárias para manipulação de dados (`pandas`, `numpy`), análise estatística (`scipy`), visualização de dados (`matplotlib`, `seaborn`), aprendizado de máquina e modelagem preditiva (`sklearn`, `statsmodels`, `prophet`), bem como ferramentas para análise de dados espaciais (`geobr`). Adicionalmente, ajustamos as configurações visuais globais para os gráficos."
    ]

# Salvar o notebook
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write('\n')  # Adicionar nova linha no final do arquivo

print("Notebook atualizado com sucesso!")
