import os

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
import matplotlib.pyplot as plt

from graficos import (
    _caminho_salvar, DIR_SAIDA,
    grafico_histograma_weibull,
    grafico_serie_temporal,
    grafico_convergencia_taylor,
    gerar_todos_graficos,
)
from calculo_densidade import calcular_densidade_potencia
from taylor_expansao import expansao_taylor


class TestCaminhoSalvar:
    def test_none_retorna_none(self):
        """_caminho_salvar(None) retorna None."""
        assert _caminho_salvar(None) is None

    def test_nome_simples_prefixia_dir(self):
        """Nome simples recebe prefixo DIR_SAIDA."""
        resultado = _caminho_salvar("figura.png")
        assert resultado == os.path.join(DIR_SAIDA, "figura.png")

    def test_caminho_absoluto_mantido(self):
        """Caminho absoluto não é modificado."""
        caminho = "/tmp/figura.png"
        assert _caminho_salvar(caminho) == caminho


class TestGraficoHistogramaWeibull:
    def setup_method(self):
        self.velocidades = np.random.weibull(2.0, 1000) * 5.0
        self.k, self.c = 2.0, 5.0

    def test_retorna_figure(self):
        """Retorna objeto Figure do matplotlib."""
        fig = grafico_histograma_weibull(self.velocidades, self.k, self.c)
        assert isinstance(fig, plt.Figure)

    def test_eixos_possuem_dados(self):
        """Figura possui pelo menos um eixo com dados."""
        fig = grafico_histograma_weibull(self.velocidades, self.k, self.c)
        assert len(fig.axes) > 0

    def test_com_salvar_string(self):
        """Salvar com nome simples não levanta erro."""
        fig = grafico_histograma_weibull(self.velocidades, self.k, self.c, salvar="test_hist.png")
        fig.savefig(DIR_SAIDA + "/test_hist.png")


class TestGraficoSerieTemporal:
    def setup_method(self):
        self.df = pd.DataFrame({
            "data_hora": pd.date_range("2025-01-01", periods=100, freq="h"),
            "velocidade_vento": np.random.weibull(2.0, 100) * 5.0,
        })

    def test_retorna_figure(self):
        """Retorna objeto Figure do matplotlib."""
        fig = grafico_serie_temporal(self.df)
        assert isinstance(fig, plt.Figure)


class TestGraficoConvergenciaTaylor:
    def setup_method(self):
        np.random.seed(42)
        v = np.random.weibull(2.0, 5000) * 5.0
        v = v[v > 0]
        self.resultado = expansao_taylor(v)

    def test_retorna_figure(self):
        """Retorna objeto Figure do matplotlib."""
        fig = grafico_convergencia_taylor(self.resultado)
        assert isinstance(fig, plt.Figure)


class TestGerarTodosGraficos:
    def setup_method(self):
        np.random.seed(42)
        n = 500
        self.df = pd.DataFrame({
            "data_hora": pd.date_range("2025-01-01", periods=n, freq="h"),
            "velocidade_vento": np.random.weibull(2.0, n) * 5.0,
            "direcao_vento": np.random.uniform(0, 360, n),
        })
        self.densidade = calcular_densidade_potencia(self.df)
        v = self.df["velocidade_vento"].dropna().values
        v = v[v > 0]
        self.taylor = expansao_taylor(v)

    def test_salvar_true_nao_levanta_erro(self):
        """gerar_todos_graficos(salvar=True) executa sem erro."""
        gerar_todos_graficos(self.df, self.densidade, self.taylor, salvar=True)

    def test_salvar_false_nao_levanta_erro(self):
        """gerar_todos_graficos(salvar=False) executa sem erro."""
        gerar_todos_graficos(self.df, self.densidade, self.taylor, salvar=False)
        plt.close("all")
