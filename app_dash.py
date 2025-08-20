import pandas as pd
from dash import Dash, dcc, html, Input, Output

import plotly.express as px
import plotly.graph_objects as go

# =========================
# 1) CARREGAR E PREPARAR
# =========================
df = pd.read_excel("data/dataset_biagio.xlsx")

# Tipos
df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype("Int64")
df["Mês"] = pd.to_numeric(df["Mês"], errors="coerce").astype("Int64")
for c in ["Vendas", "Margem_%", "Margem_Valor"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Coluna temporal mensal
df["Ano-Mês"] = pd.to_datetime(
    df["Ano"].astype(str) + "-" + df["Mês"].astype(str).str.zfill(2) + "-01",
    errors="coerce"
)
df = df.sort_values(["Ano", "Mês"])

# Opções filtros
opts_canal = sorted([c for c in df["Canal"].dropna().unique()])
opts_prod  = sorted([p for p in df["Produto"].dropna().unique()])
anos_disponiveis = sorted([int(a) for a in df["Ano"].dropna().unique()])

# Nome dos meses (para o gráfico por ano)
MAPA_MESES = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
              7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

def no_data_fig(titulo: str):
    fig = go.Figure()
    fig.update_layout(
        title=titulo,
        annotations=[dict(text="Sem dados para os filtros selecionados",
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font=dict(size=14, color="gray"))]
    )
    return fig

def _kpi(titulo: str, valor: str):
    return html.Div(
        style={"background":"#f6f6f6","padding":"14px","borderRadius":"12px",
               "textAlign":"center","boxShadow":"0 1px 2px rgba(0,0,0,0.05)"},
        children=[
            html.Div(titulo, style={"fontSize":"12px","color":"#666","marginBottom":"4px"}),
            html.Div(valor,  style={"fontSize":"26px","fontWeight":"700"})
        ]
    )

# =========================
# 2) APP E LAYOUT
# =========================
app = Dash(__name__)
app.title = "Dashboard Dataset Biagio"

app.layout = html.Div(
    style={"fontFamily":"system-ui, Segoe UI, Roboto, Arial", "padding":"12px 18px"},
    children=[
        html.H1("Dashboard • Dataset Biagio", style={"marginBottom":0}),
        html.P("Filtros interativos + KPIs + 6 gráficos", style={"marginTop":4, "color":"#666"}),

        # Filtros
        html.Div(
            style={"display":"grid","gridTemplateColumns":"1fr 2fr 0.6fr","gap":"12px","margin":"8px 0 14px"},
            children=[
                html.Div([
                    html.Label("Canal"),
                    dcc.Dropdown(
                        id="filtro-canal",
                        options=[{"label":c,"value":c} for c in opts_canal],
                        value=opts_canal, multi=True, clearable=False),
                ]),
                html.Div([
                    html.Label("Produto"),
                    dcc.Dropdown(
                        id="filtro-produto",
                        options=[{"label":p,"value":p} for p in opts_prod],
                        value=opts_prod, multi=True, clearable=False),
                ]),
                html.Div([
                    html.Label("Ano"),
                    dcc.Dropdown(
                        id="filtro-ano",
                        options=[{"label":str(a),"value":int(a)} for a in anos_disponiveis],
                        value=max(anos_disponiveis) if anos_disponiveis else None,
                        clearable=False),
                ]),
            ],
        ),

        # KPIs
        html.Div(id="kpi-cards",
                 style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"16px","margin":"6px 0 18px"}),

        # Gráficos
        dcc.Graph(id="graf-clientes"),
        dcc.Graph(id="graf-tempo"),
        dcc.Graph(id="graf-margem"),
        dcc.Graph(id="graf-ano"),
        dcc.Graph(id="graf-mes"),
        dcc.Graph(id="graf-mes-ano"),  # NOVO: por mês no ano selecionado
    ],
)

# =========================
# 3) CALLBACK
# =========================
@app.callback(
    Output("kpi-cards","children"),
    Output("graf-clientes","figure"),
    Output("graf-tempo","figure"),
    Output("graf-margem","figure"),
    Output("graf-ano","figure"),
    Output("graf-mes","figure"),
    Output("graf-mes-ano","figure"),      # novo
    Input("filtro-canal","value"),
    Input("filtro-produto","value"),
    Input("filtro-ano","value"),          # novo
)
def atualizar(sel_canais, sel_produtos, ano_sel):
    if not sel_canais or not sel_produtos:
        fig = no_data_fig
        empty = []
        return (empty, fig("Top 10 Clientes"), fig("Vendas no tempo"),
                fig("Distribuição da Margem"), fig("Vendas por Ano"),
                fig("Vendas por Mês"), fig(f"Vendas por Mês (Ano {ano_sel})"))

    dff = df[df["Canal"].isin(sel_canais) & df["Produto"].isin(sel_produtos)].copy()
    if dff.empty:
        fig = no_data_fig
        empty = []
        return (empty, fig("Top 10 Clientes"), fig("Vendas no tempo"),
                fig("Distribuição da Margem"), fig("Vendas por Ano"),
                fig("Vendas por Mês"), fig(f"Vendas por Mês (Ano {ano_sel})"))

    # KPIs
    total_vendas = dff["Vendas"].sum(skipna=True)
    margem_media = dff["Margem_%"].mean(skipna=True)
    n_clientes   = dff["Cliente"].nunique()
    kpis = [
        _kpi("💰 Total Vendas", f"{total_vendas:,.0f} €"),
        _kpi("📈 Margem Média", f"{margem_media:.2%}" if pd.notna(margem_media) else "—"),
        _kpi("👥 Nº Clientes", f"{n_clientes}"),
    ]

    # Gráfico 1 — Top clientes
    top_clientes = dff.groupby("Cliente", as_index=False)["Vendas"].sum().nlargest(10, "Vendas")
    fig1 = px.bar(top_clientes, x="Cliente", y="Vendas", title="Top 10 Clientes por Vendas")
    fig1.update_layout(xaxis_tickangle=-30)

    # Gráfico 2 — Série mensal (Ano‑Mês)
    vendas_tempo = dff.groupby("Ano-Mês", as_index=False)["Vendas"].sum().sort_values("Ano-Mês")
    fig2 = px.line(vendas_tempo, x="Ano-Mês", y="Vendas", markers=True, title="Vendas ao longo do tempo (mensal)")

    # Gráfico 3 — Histograma margem
    fig3 = px.histogram(dff.dropna(subset=["Margem_%"]), x="Margem_%", nbins=25, title="Distribuição da Margem (%)")

    # Gráfico 4 — Vendas por Ano
    vendas_ano = dff.groupby("Ano", as_index=False)["Vendas"].sum().sort_values("Ano")
    fig4 = px.bar(vendas_ano, x="Ano", y="Vendas", title="Vendas por Ano")

    # Gráfico 5 — Vendas por Mês (todos os anos)
    vendas_mes = dff.groupby("Mês", as_index=False)["Vendas"].sum().sort_values("Mês")
    fig5 = px.bar(vendas_mes, x="Mês", y="Vendas", title="Vendas por Mês")

    # Gráfico 6 — Vendas por Mês no Ano selecionado
    dff_ano = dff[dff["Ano"] == ano_sel].copy()
    if dff_ano.empty:
        fig6 = no_data_fig(f"Vendas por Mês (Ano {ano_sel})")
    else:
        vendas_mes_ano = (
            dff_ano.groupby("Mês", as_index=False)["Vendas"]
                   .sum(min_count=1).sort_values("Mês")
        )
        vendas_mes_ano["Mês"] = vendas_mes_ano["Mês"].map(MAPA_MESES)
        fig6 = px.bar(vendas_mes_ano, x="Mês", y="Vendas",
                      title=f"Vendas por Mês (Ano {ano_sel})")

    return kpis, fig1, fig2, fig3, fig4, fig5, fig6

# =========================
# 4) RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)  # muda a porta com port=8051 se precisares