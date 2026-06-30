import numpy as np
import pytest

from potencial_total import calcular_potencia
from utils import ROTOR_RAIO, RHO


class TestCalcularPotencia:
    def setup_method(self):
        self.densidade_teste = 100.0

    def test_retorna_dict(self):
        """calcular_potencia retorna dicionário."""
        resultado = calcular_potencia(self.densidade_teste)
        assert isinstance(resultado, dict)

    def test_chaves_esperadas(self):
        """Dicionário contém todas as chaves esperadas."""
        resultado = calcular_potencia(self.densidade_teste)
        chaves = {"raio_rotor_m", "area_varrida_m2", "densidade_potencia_w_m2",
                  "potencia_watts", "potencia_kw", "potencia_mw"}
        assert chaves.issubset(resultado.keys())

    def test_area_calculada(self):
        """Área = pi * R^2 com R = 60."""
        resultado = calcular_potencia(self.densidade_teste)
        area_esperada = np.pi * 60.0 ** 2
        assert resultado["area_varrida_m2"] == pytest.approx(area_esperada)

    def test_potencia_watts(self):
        """P = (P/A) * A."""
        resultado = calcular_potencia(self.densidade_teste)
        area = np.pi * 60.0 ** 2
        assert resultado["potencia_watts"] == pytest.approx(self.densidade_teste * area)

    def test_raiz_usapadrao(self):
        """Sem argumento R, usa ROTOR_RAIO (60.0 m)."""
        resultado = calcular_potencia(self.densidade_teste)
        assert resultado["raio_rotor_m"] == ROTOR_RAIO

    def test_raio_personalizado(self):
        """Argumento R personalizado é refletido no resultado."""
        R = 40.0
        resultado = calcular_potencia(self.densidade_teste, R=R)
        assert resultado["raio_rotor_m"] == R
        area_esperada = np.pi * R ** 2
        assert resultado["area_varrida_m2"] == pytest.approx(area_esperada)

    def test_conversoes_kw_mw(self):
        """1 kW = 1000 W, 1 MW = 1e6 W."""
        resultado = calcular_potencia(self.densidade_teste)
        assert resultado["potencia_kw"] == pytest.approx(resultado["potencia_watts"] / 1000)
        assert resultado["potencia_mw"] == pytest.approx(resultado["potencia_watts"] / 1e6)

    def test_densidade_zero(self):
        """Densidade zero resulta em potência zero."""
        resultado = calcular_potencia(0.0)
        assert resultado["potencia_watts"] == 0.0

    def test_densidade_negativa(self):
        """Densidade negativa resulta em potência negativa."""
        resultado = calcular_potencia(-50.0)
        assert resultado["potencia_watts"] < 0

    def test_potencia_cresce_com_R(self):
        """Raio maior produz área e potência maiores."""
        r_peq = calcular_potencia(self.densidade_teste, R=30.0)
        r_gde = calcular_potencia(self.densidade_teste, R=60.0)
        assert r_gde["potencia_watts"] > r_peq["potencia_watts"]
