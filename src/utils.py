import os
from pathlib import Path
from typing import List, Optional

RHO = 1.225

PROJ_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_ROOT / "dados" / "raw"
PROCESSED_DIR = PROJ_ROOT / "dados" / "processed"

BASE_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos"
ESTACAO_PADRAO = "A303"
ANOS_PADRAO = [2025, 2026]


def csv_path(estacao: Optional[str] = None, anos: Optional[List[int]] = None) -> Path:
    """Gera o caminho do CSV limpo com base na estação e anos."""
    estacao = estacao or ESTACAO_PADRAO
    anos = anos or ANOS_PADRAO
    periodo = f"{anos[0]}_{anos[-1]}"
    return PROCESSED_DIR / f"{estacao}_{periodo}_limpo.csv"
