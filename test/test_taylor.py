import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from taylor_expansao import (
    coeficientes_taylor_v3,
    integrar_termos_weibull,
    expansao_taylor,
)


class TestCoeficientesTaylor:
    def test_expansao_exata_v3(self):
        v = 3.0
        coeffs = coeficientes_taylor_v3(v, 4)
        assert coeffs[0] == v ** 3
        assert coeffs[1] == 3 * v ** 2
        assert coeffs[2] == 3 * v
        assert coeffs[3] == 1.0

    def test_reconstrucao_v3(self):
        v_media = 4.0
        coeffs = coeficientes_taylor_v3(v_media, 4)
        for v_teste in [2.0, 3.0, 4.0, 5.0, 6.0]:
            reconstruido = sum(coeffs[n] * (v_teste - v_media) ** n for n in range(4))
            assert abs(reconstruido - v_teste ** 3) < 1e-10


class TestIntegracaoWeibull:
    def test_primeiro_termo_e_um(self):
        k, c = 2.0, 5.0
        termos = integrar_termos_weibull(3.0, k, c, n_termos=1)
        assert abs(termos[0] - 1.0) < 0.01

    def test_segundo_termo_omega1(self):
        k, c = 2.0, 5.0
        from calculo_densidade import weibull_pdf
        from scipy.integrate import quad

        v_media = 3.0
        omega1_esperado, _ = quad(lambda v: (v - v_media) * weibull_pdf(v, k, c), 0, c * 5)
        termos = integrar_termos_weibull(v_media, k, c, n_termos=2)
        assert abs(termos[1] - omega1_esperado) < 0.01


class TestExpansaoTaylor:
    def setup_method(self):
        np.random.seed(42)
        k_true, c_true = 2.0, 5.0
        dados = np.random.weibull(k_true, 5000) * c_true
        self.df = pd.DataFrame({
            "data_hora": pd.date_range("2025-01-01", periods=5000, freq="h"),
            "velocidade_vento": dados,
        })
        velocidades = dados[dados > 0]
        self.resultado = expansao_taylor(velocidades)

    def test_retorna_chaves_esperadas(self):
        assert "v_media" in self.resultado
        assert "v_cubica_analitica" in self.resultado
        assert "convergencia" in self.resultado

    def test_converge_para_analitico(self):
        ultimo = self.resultado["convergencia"][-1]
        assert ultimo["erro_relativo_pct"] < 1.0

    def test_erro_diminui_com_mais_termos(self):
        erros = [c["erro_relativo_pct"] for c in self.resultado["convergencia"]]
        assert erros[-1] <= erros[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
