import json

with open("notebooks/HIV-Gestante-Completo.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell.get("source", []))
        if "PCA" in source:
            print("FOUND PCA CELL!")
            print(source)
            print("-" * 40)
