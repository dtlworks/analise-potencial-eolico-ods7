import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from utils import csv_path
from calculo_densidade import calcular_densidade_potencia
from taylor_expansao import expansao_taylor
from potencial_total import calcular_potencia
from rosa_dos_ventos import calcular_rosa
from graficos import gerar_todos_graficos


def main():
    """Orquestra a pipeline completa de análise de potencial eólico.

    Executa em sequência:
    1. Carrega CSV processado de dados de vento do INMET
    2. Calcula densidade de potência (Weibull + 4 métodos de integração)
    3. Expansão em série de Taylor de ⟨v³⟩
    4. Potência total para turbina Vestas V120-2.2 MW
    5. Estatísticas da rosa dos ventos
    6. Geração e salvamento de gráficos
    """
    caminho = csv_path()
    print(f"Carregando dados de: {caminho}")
    df = pd.read_csv(caminho, parse_dates=["data_hora"])
    print(f"  Registros: {len(df)}")
    print(f"  Periodo:   {df['data_hora'].min()} a {df['data_hora'].max()}")
    print()

    print("=" * 55)
    print("  1. DENSIDADE DE POTENCIA (Weibull + Integracao Numerica)")
    print("=" * 55)
    resultado_densidade = calcular_densidade_potencia(df)
    print(f"  Weibull: k={resultado_densidade['k_weibull']:.6f}, c={resultado_densidade['c_weibull']:.6f} m/s")
    print()
    print(f"  {'Metodo':<12} {'<v^3> (m^3/s^3)':<16} {'P/A (W/m^2)':<12}")
    print(f"  {'-'*40}")
    for metodo in ["analitica", "riemann", "trapezio", "simpson"]:
        cubica = resultado_densidade["media_cubica"][metodo]
        pa = resultado_densidade["densidade_potencia"][metodo]
        print(f"  {metodo:<12} {cubica:<16.6f} {pa:<12.6f}")
    print()

    print("=" * 55)
    print("  2. EXPANSAO EM SERIE DE TAYLOR")
    print("=" * 55)
    velocidades = df["velocidade_vento"].dropna().values
    velocidades = velocidades[velocidades > 0]
    resultado_taylor = expansao_taylor(velocidades)
    print(f"  v_media = {resultado_taylor['v_media']:.6f} m/s")
    print(f"  <v^3> analitico = {resultado_taylor['v_cubica_analitica']:.6f} m^3/s^3")
    print()
    print(f"  {'Termos':<8} {'Soma parcial':<16} {'Erro %':<10}")
    print(f"  {'-'*34}")
    for c in resultado_taylor["convergencia"]:
        print(f"  {c['n_termos']:<8} {c['soma_parcial']:<16.6f} {c['erro_relativo_pct']:<10.4f}")
    print()

    print("=" * 55)
    print("  3. POTENCIA TOTAL (Vestas V120-2.2 MW)")
    print("=" * 55)
    pa_simpson = resultado_densidade["densidade_potencia"]["simpson"]
    resultado_potencia = calcular_potencia(pa_simpson)
    print(f"  Raio do rotor       = {resultado_potencia['raio_rotor_m']:.0f} m")
    print(f"  Area varrida        = {resultado_potencia['area_varrida_m2']:.2f} m²")
    print(f"  Potencia estimada   = {resultado_potencia['potencia_mw']:.6f} MW")
    print(f"  Nominal             = 2.20 MW")
    print(f"  Fator de capacidade = {resultado_potencia['potencia_mw']/2.2*100:.2f}%")
    print()

    print("=" * 55)
    print("  4. ROSA DOS VENTOS")
    print("=" * 55)
    rosa = calcular_rosa(df)
    print(f"  {'Direcao':<6} {'Freq %':<10} {'Vel Media (m/s)':<16}")
    print(f"  {'-'*32}")
    for i in range(rosa["n_setores"]):
        print(f"  {rosa['nomes'][i]:<6} {rosa['frequencia_pct'][i]:<10.2f} {rosa['velocidade_media'][i]:<16.2f}")
    print()

    print("=" * 55)
    print("  5. GERANDO GRAFICOS")
    print("=" * 55)
    gerar_todos_graficos(df, resultado_densidade, resultado_taylor, salvar=True)


if __name__ == "__main__":
    main()
