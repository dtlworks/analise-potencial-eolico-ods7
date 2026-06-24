import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import gamma as gamma_func
from typing import Dict

from utils import RHO


def ajustar_weibull(velocidades: np.ndarray) -> tuple:
    k, _, c = stats.weibull_min.fit(velocidades, floc=0)
    return k, c


def weibull_pdf(v: np.ndarray, k: float, c: float) -> np.ndarray:
    return (k / c) * (v / c) ** (k - 1) * np.exp(-((v / c) ** k))


def media_cubica_analitica(k: float, c: float) -> float:
    return c ** 3 * gamma_func(1 + 3 / k)


def media_cubica_riemann(v: np.ndarray, k: float, c: float) -> float:
    v_sorted = np.sort(v)
    dv = np.diff(v_sorted)
    v_mid = (v_sorted[:-1] + v_sorted[1:]) / 2
    pdf_vals = weibull_pdf(v_mid, k, c)
    return np.sum(v_mid ** 3 * pdf_vals * dv)


def media_cubica_trapezio(v: np.ndarray, k: float, c: float) -> float:
    v_sorted = np.sort(v)
    dv = np.diff(v_sorted)
    pdf_left = weibull_pdf(v_sorted[:-1], k, c)
    pdf_right = weibull_pdf(v_sorted[1:], k, c)
    return np.sum((v_sorted[:-1] ** 3 * pdf_left + v_sorted[1:] ** 3 * pdf_right) * dv / 2)


def media_cubica_simpson(v: np.ndarray, k: float, c: float) -> float:
    v_sorted = np.sort(v)
    n = len(v_sorted)
    if n < 3 or n % 2 == 0:
        return media_cubica_trapezio(v_sorted, k, c)

    dv = v_sorted[1] - v_sorted[0]
    integrando = v_sorted ** 3 * weibull_pdf(v_sorted, k, c)
    resultado = integrando[0] + integrando[-1]
    resultado += 4 * np.sum(integrando[1:-1:2])
    resultado += 2 * np.sum(integrando[2:-2:2])
    return resultado * dv / 3


def calcular_densidade_potencia(df: pd.DataFrame, rho: float = RHO) -> Dict:
    velocidades = df["velocidade_vento"].dropna().values
    velocidades = velocidades[velocidades > 0]

    k, c = ajustar_weibull(velocidades)

    v_range = np.linspace(0, velocidades.max() * 1.5, 1000)

    cubica_riemann = media_cubica_riemann(v_range, k, c)
    cubica_trapezio = media_cubica_trapezio(v_range, k, c)
    cubica_simpson = media_cubica_simpson(v_range, k, c)
    cubica_analitica = media_cubica_analitica(k, c)

    pa_riemann = 0.5 * rho * cubica_riemann
    pa_trapezio = 0.5 * rho * cubica_trapezio
    pa_simpson = 0.5 * rho * cubica_simpson
    pa_analitica = 0.5 * rho * cubica_analitica

    return {
        "k_weibull": k,
        "c_weibull": c,
        "v_media_dados": np.mean(velocidades),
        "rho": rho,
        "media_cubica": {
            "analitica": cubica_analitica,
            "riemann": cubica_riemann,
            "trapezio": cubica_trapezio,
            "simpson": cubica_simpson,
        },
        "densidade_potencia": {
            "analitica": pa_analitica,
            "riemann": pa_riemann,
            "trapezio": pa_trapezio,
            "simpson": pa_simpson,
        },
    }


if __name__ == "__main__":
    from utils import csv_path

    df = pd.read_csv(csv_path(), parse_dates=["data_hora"])

    resultado = calcular_densidade_potencia(df)

    print(f"=== Ajuste de Weibull ===")
    print(f"  k (forma)  = {resultado['k_weibull']:.6f}")
    print(f"  c (escala) = {resultado['c_weibull']:.6f} m/s")
    print(f"  v_media    = {resultado['v_media_dados']:.2f} m/s")
    print()
    print(f"=== Media Cubica <v³> (m³/s³) ===")
    for metodo, val in resultado["media_cubica"].items():
        print(f"  {metodo:<12} {val:.6f}")
    print()
    print(f"=== Densidade de Potencia P/A (W/m²) ===")
    for metodo, val in resultado["densidade_potencia"].items():
        print(f"  {metodo:<12} {val:.6f}")
