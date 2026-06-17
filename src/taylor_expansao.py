import numpy as np
from scipy.special import gamma as gamma_func
from typing import Dict, List

from calculo_densidade import ajustar_weibull, weibull_pdf, media_cubica_analitica


def coeficientes_taylor_v3(v_media: float, n_termos: int = 4) -> List[float]:
    coeffs = [0.0] * n_termos
    coeffs[0] = v_media ** 3
    if n_termos > 1:
        coeffs[1] = 3 * v_media ** 2
    if n_termos > 2:
        coeffs[2] = 3 * v_media
    if n_termos > 3:
        coeffs[3] = 1.0
    return coeffs


def integrar_termos_weibull(v_media: float, k: float, c: float, n_termos: int = 4) -> List[float]:
    from scipy.integrate import quad

    resultados = []
    for n in range(n_termos):
        integrando = lambda v, n=n: (v - v_media) ** n * weibull_pdf(v, k, c)
        val, _ = quad(integrando, 0, c * 5)
        resultados.append(val)
    return resultados


def expansao_taylor(velocidades: np.ndarray, n_termos_max: int = 8) -> Dict:
    k, c = ajustar_weibull(velocidades)
    v_media = np.mean(velocidades)
    v_cubica_analitica = media_cubica_analitica(k, c)

    termos_weibull = integrar_termos_weibull(v_media, k, c, n_termos_max)
    coeffs = coeficientes_taylor_v3(v_media, n_termos_max)

    convergencia = []
    soma_parcial = 0.0
    for n in range(n_termos_max):
        contribuicao = coeffs[n] * termos_weibull[n]
        soma_parcial += contribuicao
        erro_abs = abs(soma_parcial - v_cubica_analitica)
        erro_rel = erro_abs / v_cubica_analitica * 100 if v_cubica_analitica != 0 else 0
        convergencia.append({
            "n_termos": n + 1,
            "ultimo_termo": contribuicao,
            "soma_parcial": soma_parcial,
            "erro_absoluto": erro_abs,
            "erro_relativo_pct": erro_rel,
        })

    return {
        "v_media": v_media,
        "k_weibull": k,
        "c_weibull": c,
        "v_cubica_analitica": v_cubica_analitica,
        "coeficientes": coeffs,
        "termos_weibull": termos_weibull,
        "convergencia": convergencia,
    }


if __name__ == "__main__":
    from utils import PROCESSED_DIR
    import pandas as pd

    csv_path = PROCESSED_DIR / "A303_2025_2026_limpo.csv"
    df = pd.read_csv(csv_path, parse_dates=["data_hora"])

    velocidades = df["velocidade_vento"].dropna().values
    velocidades = velocidades[velocidades > 0]

    resultado = expansao_taylor(velocidades)

    print(f"=== Expansao de Taylor de v³ ===")
    print(f"  v̄ (media)          = {resultado['v_media']:.4f} m/s")
    print(f"  <v³> analitico     = {resultado['v_cubica_analitica']:.4f} m³/s³")
    print()
    print(f"  {'Termos':<8} {'Ultimo termo':<15} {'Soma parcial':<15} {'Erro absoluto':<15} {'Erro %':<10}")
    for c in resultado["convergencia"]:
        print(f"  {c['n_termos']:<8} {c['ultimo_termo']:<15.6f} {c['soma_parcial']:<15.6f} {c['erro_absoluto']:<15.6f} {c['erro_relativo_pct']:<10.4f}")
