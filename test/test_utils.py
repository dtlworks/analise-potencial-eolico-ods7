import pytest
from pathlib import Path

from utils import (
    RHO, ROTOR_RAIO, PROJ_ROOT, RAW_DIR, PROCESSED_DIR,
    BASE_URL, ESTACAO_PADRAO, ANOS_PADRAO, csv_path,
)


class TestConstantes:
    def test_rho_positivo(self):
        """Densidade do ar deve ser positiva."""
        assert RHO > 0

    def test_rho_valor_padrao(self):
        """Densidade do ar padrão é 1.225 kg/m³ ao nível do mar."""
        assert RHO == 1.225

    def test_rotor_raio_valor(self):
        """Raio do rotor padrão é 60.0 m (Vestas V120)."""
        assert ROTOR_RAIO == 60.0

    def test_estacao_padrao(self):
        """Estação padrão é A303 (Maceió-AL)."""
        assert ESTACAO_PADRAO == "A303"

    def test_anos_padrao(self):
        """Período padrão é [2025, 2026]."""
        assert ANOS_PADRAO == [2025, 2026]

    def test_base_url(self):
        """URL base do INMET deve conter 'inmet' e 'dadoshistoricos'."""
        assert "inmet" in BASE_URL
        assert "dadoshistoricos" in BASE_URL

    def test_proj_root_existe(self):
        """PROJ_ROOT deve ser um diretório existente."""
        assert PROJ_ROOT.exists()

    def test_raw_dir_e_path(self):
        """RAW_DIR deve ser um Path abaixo de PROJ_ROOT."""
        assert isinstance(RAW_DIR, Path)
        assert str(RAW_DIR).startswith(str(PROJ_ROOT))

    def test_processed_dir_e_path(self):
        """PROCESSED_DIR deve ser um Path abaixo de PROJ_ROOT."""
        assert isinstance(PROCESSED_DIR, Path)
        assert str(PROCESSED_DIR).startswith(str(PROJ_ROOT))


class TestCsvPath:
    def test_sem_args(self):
        """csv_path() retorna caminho com defaults (A303, 2025-2026)."""
        caminho = csv_path()
        assert "A303" in str(caminho)
        assert "2025" in str(caminho)
        assert "2026" in str(caminho)
        assert caminho.suffix == ".csv"

    def test_estacao_personalizada(self):
        """csv_path(estacao='X999') reflete estação no nome."""
        caminho = csv_path(estacao="X999")
        assert "X999" in str(caminho)

    def test_anos_personalizados(self):
        """csv_path(anos=[2020, 2021]) reflete período no nome."""
        caminho = csv_path(anos=[2020, 2021])
        assert "2020_2021" in str(caminho)

    def test_retorna_path(self):
        """csv_path() retorna objeto Path."""
        assert isinstance(csv_path(), Path)

    def test_estacao_none_usapadrao(self):
        """csv_path(estacao=None) usa estação padrão A303."""
        assert "A303" in str(csv_path(estacao=None))

    def test_anos_none_usapadrao(self):
        """csv_path(anos=None) usa período padrão [2025, 2026]."""
        assert "2025_2026" in str(csv_path(anos=None))
