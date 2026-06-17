import os
from pathlib import Path

RHO = 1.225

PROJ_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_ROOT / "dados" / "raw"
PROCESSED_DIR = PROJ_ROOT / "dados" / "processed"

BASE_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos"
ESTACAO_PADRAO = "A303"
ANOS_PADRAO = [2025, 2026]
