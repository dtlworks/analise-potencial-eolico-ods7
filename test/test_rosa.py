import numpy as np
import pandas as pd
import pytest

from rosa_dos_ventos import calcular_rosa, SETOR_NAMES


class TestCalcularRosa:
    def setup_method(self):
        np.random.seed(42)
        n = 1000
        self.df = pd.DataFrame({
            "direcao_vento": np.random.uniform(0, 360, n),
            "velocidade_vento": np.random.weibull(2.0, n) * 5.0,
        })

    def test_retorna_dict(self):
        """calcular_rosa retorna dicionário."""
        rosa = calcular_rosa(self.df)
        assert isinstance(rosa, dict)

    def test_chaves_esperadas(self):
        """Dicionário contém todas as chaves esperadas."""
        rosa = calcular_rosa(self.df)
        chaves = {"n_setores", "angulo_setor", "nomes", "contagem",
                  "frequencia_pct", "velocidade_media", "total_registros"}
        assert chaves.issubset(rosa.keys())

    def test_numero_setores(self):
        """Número padrão de setores é 16."""
        rosa = calcular_rosa(self.df)
        assert rosa["n_setores"] == 16

    def test_setores_personalizados(self):
        """Argumento n_setores altera o número de setores."""
        rosa = calcular_rosa(self.df, n_setores=8)
        assert rosa["n_setores"] == 8
        assert len(rosa["nomes"]) == 8
        assert len(rosa["contagem"]) == 8

    def test_nomes_cardinais(self):
        """Nomes dos setores começam em N e seguem ordem cardinal."""
        rosa = calcular_rosa(self.df)
        assert rosa["nomes"][0] == "N"
        assert rosa["nomes"][4] == "E"
        assert rosa["nomes"][8] == "S"
        assert rosa["nomes"][12] == "W"

    def test_angulo_setor(self):
        """Ângulo do setor = 360 / n_setores."""
        rosa = calcular_rosa(self.df)
        assert rosa["angulo_setor"] == pytest.approx(360 / 16)

    def test_total_registros(self):
        """total_registros soma todas as contagens."""
        rosa = calcular_rosa(self.df)
        assert rosa["total_registros"] == rosa["contagem"].sum()
        assert rosa["total_registros"] > 0

    def test_frequencia_soma_100(self):
        """Soma das frequências percentuais é 100%."""
        rosa = calcular_rosa(self.df)
        assert rosa["frequencia_pct"].sum() == pytest.approx(100.0, abs=0.01)

    def test_frequencia_positiva(self):
        """Todas as frequências são >= 0."""
        rosa = calcular_rosa(self.df)
        assert (rosa["frequencia_pct"] >= 0).all()

    def test_velocidade_media_positiva(self):
        """Velocidades médias são >= 0."""
        rosa = calcular_rosa(self.df)
        assert (rosa["velocidade_media"] >= 0).all()

    def test_angulo_setor_personalizado(self):
        """Ângulo do setor com n_setores personalizado."""
        for n in [4, 8, 16, 32]:
            rosa = calcular_rosa(self.df, n_setores=n)
            assert rosa["angulo_setor"] == pytest.approx(360 / n)

    def test_dados_com_nan(self):
        """Valores NaN em direção são ignorados."""
        df_com_nan = self.df.copy()
        df_com_nan.loc[0:4, "direcao_vento"] = np.nan
        rosa = calcular_rosa(df_com_nan)
        assert rosa["total_registros"] == len(df_com_nan.dropna(subset=["direcao_vento"]))

    def test_frequencia_nao_zero_total(self):
        """Com dados uniformes, nenhum setor deve ter frequência zero."""
        rosa = calcular_rosa(self.df)
        assert (rosa["frequencia_pct"] > 0).all()

    def test_setor_names_matches_constante(self):
        """Nomes dos setores correspondem a SETOR_NAMES."""
        rosa = calcular_rosa(self.df)
        assert rosa["nomes"] == SETOR_NAMES[:16]
