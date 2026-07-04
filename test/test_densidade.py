import numpy as np
import pandas as pd
import pytest

from calculo_densidade import (
    ajustar_weibull,
    weibull_pdf,
    media_cubica_analitica,
    media_cubica_riemann,
    media_cubica_trapezio,
    media_cubica_simpson,
    calcular_densidade_potencia,
)


class TestWeibull:
    def test_ajuste_parametros(self):
        """Ajuste Weibull recupera k e c conhecidos para dados sintéticos."""
        np.random.seed(42)
        k_true, c_true = 2.0, 5.0
        dados = np.random.weibull(k_true, 1000) * c_true
        k_fit, c_fit = ajustar_weibull(dados)
        assert abs(k_fit - k_true) < 0.2
        assert abs(c_fit - c_true) < 0.5

    def test_pdf_integra_para_um(self):
        """PDF Weibull integra numericamente para 1.0 dentro de 1%."""
        k, c = 2.0, 5.0
        v = np.linspace(0.001, 30, 5000)
        pdf_vals = weibull_pdf(v, k, c)
        integral = np.trapz(pdf_vals, v)
        assert abs(integral - 1.0) < 0.01

    def test_media_cubica_analitica(self):
        """<v^3> analítico difere <1% da integração numérica direta."""
        k, c = 2.0, 5.0
        resultado = media_cubica_analitica(k, c)
        assert resultado > 0
        v = np.linspace(0.001, 30, 5000)
        numerico = np.trapz(v ** 3 * weibull_pdf(v, k, c), v)
        assert abs(resultado - numerico) / numerico < 0.01


class TestIntegracaoNumerica:
    def setup_method(self):
        """Configura parâmetros Weibull fixos para testes de integração."""
        self.k, self.c = 2.0, 5.0
        self.v = np.linspace(0.001, 25, 1000)
        self.analitica = media_cubica_analitica(self.k, self.c)

    def test_riemann_proximo_analitico(self):
        """Riemann <5% de erro relativo ao valor analítico."""
        resultado = media_cubica_riemann(self.v, self.k, self.c)
        assert abs(resultado - self.analitica) / self.analitica < 0.05

    def test_trapezio_proximo_analitico(self):
        """Trapézio <1% de erro relativo ao valor analítico."""
        resultado = media_cubica_trapezio(self.v, self.k, self.c)
        assert abs(resultado - self.analitica) / self.analitica < 0.01

    def test_simpson_proximo_analitico(self):
        """Simpson <1% de erro relativo ao valor analítico."""
        resultado = media_cubica_simpson(self.v, self.k, self.c)
        assert abs(resultado - self.analitica) / self.analitica < 0.01

    def test_simpson_proximo_analitico_apertado(self):
        """Simpson <0.1% de erro (tolerância mais apertada)."""
        r_simpson = media_cubica_simpson(self.v, self.k, self.c)
        erro_simpson = abs(r_simpson - self.analitica)
        assert erro_simpson / self.analitica < 0.001


class TestDensidadePotencia:
    def setup_method(self):
        """Gera DataFrame sintético Weibull para testes de densidade."""
        k_true, c_true = 2.0, 5.0
        dados = np.random.weibull(k_true, 5000) * c_true
        self.df = pd.DataFrame({
            "data_hora": pd.date_range("2025-01-01", periods=5000, freq="h"),
            "velocidade_vento": dados,
            "direcao_vento": np.random.uniform(0, 360, 5000),
        })

    def test_retorna_chaves_esperadas(self):
        """calcular_densidade_potencia retorna todas as chaves esperadas."""
        resultado = calcular_densidade_potencia(self.df)
        assert "k_weibull" in resultado
        assert "c_weibull" in resultado
        assert "densidade_potencia" in resultado
        assert "analitica" in resultado["densidade_potencia"]
        assert "riemann" in resultado["densidade_potencia"]
        assert "trapezio" in resultado["densidade_potencia"]
        assert "simpson" in resultado["densidade_potencia"]

    def test_todos_metodos_positivos(self):
        """Todos os métodos de densidade retornam valores positivos."""
        resultado = calcular_densidade_potencia(self.df)
        for metodo, val in resultado["densidade_potencia"].items():
            assert val > 0, f"Metodo {metodo} retornou valor nao positivo: {val}"

    def test_metodos_proximos(self):
        """Resultados dos 4 métodos diferem em menos de 1.0 W/m²."""
        resultado = calcular_densidade_potencia(self.df)
        vals = list(resultado["densidade_potencia"].values())
        assert max(vals) - min(vals) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
