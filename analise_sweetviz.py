import pandas as pd
import sweetviz as sv
from pathlib import Path
import webbrowser

# Carrega o dataset
df = pd.read_excel("data/dataset_biagio.xlsx")

# Trata a coluna "Mês" como string/categoria, se existir
if "Mês" in df.columns:
    df["Mês"] = df["Mês"].astype(str)

# Gera o relatório Sweetviz
report = sv.analyze(df)

# Cria diretório de saída, se necessário
out_dir = Path("reports")
out_dir.mkdir(parents=True, exist_ok=True)
output_path = out_dir / "sweetviz_report.html"

# Salva o relatório em HTML
report.show_html(str(output_path), open_browser=False)

print(f"✅ Relatório criado em: {output_path}")
webbrowser.open(output_path.resolve().as_uri())