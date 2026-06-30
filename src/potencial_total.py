import numpy as np
from typing import Dict

from utils import RHO, ROTOR_RAIO


def calcular_potencia(densidade_potencia: float, R: float = ROTOR_RAIO) -> Dict:
    """Estima potência total de turbina eólica.

    P = (P/A) * A, com A = pi * R^2.
    Valores padrão para Vestas V120-2.2 MW (R = 60 m).

    Parameters
    ----------
    densidade_potencia : float
        Densidade de potência (W/m²).
    R : float
        Raio do rotor (m, default: 60.0).

    Returns
    -------
    dict
        Chaves: raio_rotor_m, area_varrida_m2, densidade_potencia_w_m2,
                potencia_watts, potencia_kw, potencia_mw.
    """
    area = np.pi * R ** 2
    potencia_watts = densidade_potencia * area
    potencia_kw = potencia_watts / 1_000
    potencia_mw = potencia_watts / 1_000_000

    return {
        "raio_rotor_m": R,
        "area_varrida_m2": area,
        "densidade_potencia_w_m2": densidade_potencia,
        "potencia_watts": potencia_watts,
        "potencia_kw": potencia_kw,
        "potencia_mw": potencia_mw,
    }


if __name__ == "__main__":
    from calculo_densidade import calcular_densidade_potencia
    from utils import csv_path
    import pandas as pd

    df = pd.read_csv(csv_path(), parse_dates=["data_hora"])

    densidade = calcular_densidade_potencia(df)
    pa = densidade["densidade_potencia"]["simpson"]

    resultado = calcular_potencia(pa)

    print(f"=== Potencia Total Estimada (Vestas V120-2.2 MW) ===")
    print(f"  Raio do rotor       = {resultado['raio_rotor_m']:.0f} m")
    print(f"  Area varrida        = {resultado['area_varrida_m2']:.2f} m²")
    print(f"  Densidade (Simpson) = {resultado['densidade_potencia_w_m2']:.4f} W/m²")
    print(f"  Potencia estimada   = {resultado['potencia_kw']:.2f} kW")
    print(f"                      = {resultado['potencia_mw']:.4f} MW")
    print(f"  Nominal             = 2.20 MW")
    print(f"  Fator de capacidade = {resultado['potencia_mw']/2.2*100:.2f}%")
