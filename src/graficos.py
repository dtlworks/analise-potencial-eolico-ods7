import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict

from calculo_densidade import ajustar_weibull, weibull_pdf
from taylor_expansao import expansao_taylor
from rosa_dos_ventos import plotar_rosa


def grafico_histograma_weibull(velocidades: np.ndarray, k: float, c: float, salvar: str = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(velocidades, bins=50, density=True, alpha=0.6, color="steelblue", edgecolor="white", label="Dados")

    v_fit = np.linspace(0, velocidades.max() * 1.2, 200)
    pdf_fit = weibull_pdf(v_fit, k, c)
    ax.plot(v_fit, pdf_fit, "r-", lw=2, label=f"Weibull (k={k:.2f}, c={c:.2f})")

    ax.set_xlabel("Velocidade do vento (m/s)", fontsize=11)
    ax.set_ylabel("Densidade de probabilidade", fontsize=11)
    ax.set_title("Distribuicao de Velocidades do Vento - Maceio (A303)", fontsize=12)
    ax.legend()
    ax.grid(alpha=0.3)
    if salvar:
        fig.savefig(salvar, dpi=150, bbox_inches="tight")
    return fig


def grafico_serie_temporal(df: pd.DataFrame, salvar: str = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df["data_hora"], df["velocidade_vento"], lw=0.5, alpha=0.7, color="steelblue")

    ax.set_xlabel("Data", fontsize=11)
    ax.set_ylabel("Velocidade do vento (m/s)", fontsize=11)
    ax.set_title("Serie Temporal - Velocidade do Vento", fontsize=12)
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    if salvar:
        fig.savefig(salvar, dpi=150, bbox_inches="tight")
    return fig


def grafico_comparacao_integracao(resultado_densidade: Dict, salvar: str = None) -> plt.Figure:
    metodos = list(resultado_densidade["densidade_potencia"].keys())
    valores = [resultado_densidade["densidade_potencia"][m] for m in metodos]
    cores = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6"]

    fig, ax = plt.subplots(figsize=(8, 5))
    barras = ax.bar(metodos, valores, color=cores[:len(metodos)], edgecolor="black")

    for bar, val in zip(barras, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{val:.4f}", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Densidade de Potencia (W/m²)", fontsize=11)
    ax.set_title("Comparacao dos Metodos de Integracao Numerica", fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    if salvar:
        fig.savefig(salvar, dpi=150, bbox_inches="tight")
    return fig


def grafico_convergencia_taylor(resultado_taylor: Dict, salvar: str = None) -> plt.Figure:
    conv = resultado_taylor["convergencia"]
    n_termos = [c["n_termos"] for c in conv]
    erros = [c["erro_relativo_pct"] for c in conv]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n_termos, erros, "o-", color="steelblue", lw=2, markersize=6)
    ax.axhline(y=0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Numero de termos da serie de Taylor", fontsize=11)
    ax.set_ylabel("Erro relativo (%)", fontsize=11)
    ax.set_title("Convergencia da Expansao de Taylor para <v³>", fontsize=12)
    ax.set_xticks(n_termos)
    ax.grid(alpha=0.3)
    if salvar:
        fig.savefig(salvar, dpi=150, bbox_inches="tight")
    return fig


def gerar_todos_graficos(df: pd.DataFrame, resultado_densidade: Dict, resultado_taylor: Dict, salvar: bool = False):
    prefixo = "dados/processed/" if salvar else None

    velocidades = df["velocidade_vento"].dropna().values
    velocidades = velocidades[velocidades > 0]

    grafico_histograma_weibull(
        velocidades,
        resultado_densidade["k_weibull"],
        resultado_densidade["c_weibull"],
        salvar=f"{prefixo}histograma_weibull.png" if salvar else None,
    )
    grafico_serie_temporal(df, salvar=f"{prefixo}serie_temporal.png" if salvar else None)
    grafico_comparacao_integracao(resultado_densidade, salvar=f"{prefixo}comparacao_integracao.png" if salvar else None)
    grafico_convergencia_taylor(resultado_taylor, salvar=f"{prefixo}convergencia_taylor.png" if salvar else None)
    plotar_rosa(df, salvar=f"{prefixo}rosa_ventos.png" if salvar else None)

    plt.show()
