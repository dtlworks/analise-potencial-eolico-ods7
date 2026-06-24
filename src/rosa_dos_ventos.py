import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict

SETOR_NAMES = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
]


def calcular_rosa(df: pd.DataFrame, n_setores: int = 16) -> Dict:
    angulo_setor = 360 / n_setores
    idx_validos = df["direcao_vento"].notna() & df["velocidade_vento"].notna()
    direcoes = df.loc[idx_validos, "direcao_vento"].values
    velocidades = df.loc[idx_validos, "velocidade_vento"].values

    contagem = np.zeros(n_setores)
    soma_velocidades = np.zeros(n_setores)

    for d, v in zip(direcoes, velocidades):
        idx = int(d // angulo_setor) % n_setores
        contagem[idx] += 1
        soma_velocidades[idx] += v

    total = contagem.sum()
    frequencia = contagem / total * 100
    vel_media = np.where(contagem > 0, soma_velocidades / contagem, 0)

    return {
        "n_setores": n_setores,
        "angulo_setor": angulo_setor,
        "nomes": SETOR_NAMES[:n_setores],
        "contagem": contagem,
        "frequencia_pct": frequencia,
        "velocidade_media": vel_media,
        "total_registros": int(total),
    }


def plotar_rosa(df: pd.DataFrame, salvar: str = None) -> plt.Figure:
    rosa = calcular_rosa(df)
    n = rosa["n_setores"]
    angulos = np.linspace(0, 2 * np.pi, n, endpoint=False)
    largura = 2 * np.pi / n * 0.85

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    bars = ax.bar(angulos, rosa["frequencia_pct"], width=largura, alpha=0.7, edgecolor="black")

    for bar, vel in zip(bars, rosa["velocidade_media"]):
        bar.set_facecolor(plt.cm.YlOrRd(vel / max(rosa["velocidade_media"].max(), 1)))

    ax.set_xticks(angulos)
    ax.set_xticklabels(rosa["nomes"], fontsize=9)
    ax.set_title("Rosa dos Ventos - Maceió (A303)\nFrequência (%) por Direção", fontsize=12, pad=20)

    sm = plt.cm.ScalarMappable(
        cmap="YlOrRd",
        norm=plt.Normalize(vmin=0, vmax=rosa["velocidade_media"].max()),
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.1, shrink=0.6)
    cbar.set_label("Velocidade média (m/s)", fontsize=9)

    if salvar:
        fig.savefig(salvar, dpi=150, bbox_inches="tight")
    return fig


if __name__ == "__main__":
    from utils import csv_path

    df = pd.read_csv(csv_path(), parse_dates=["data_hora"])

    rosa = calcular_rosa(df)

    print(f"=== Rosa dos Ventos ===")
    print(f"  Total de registros: {rosa['total_registros']}")
    print()
    print(f"  {'Direcao':<6} {'Freq %':<10} {'Vel Media (m/s)':<16} {'Contagem':<10}")
    for i in range(rosa["n_setores"]):
        print(f"  {rosa['nomes'][i]:<6} {rosa['frequencia_pct'][i]:<10.2f} {rosa['velocidade_media'][i]:<16.2f} {int(rosa['contagem'][i]):<10}")

    plotar_rosa(df)
    plt.show()
