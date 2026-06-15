import os
from pathlib import Path

RHO = 1.225
API_BASE = "https://apitempo.inmet.gov.br"

PROJ_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJ_ROOT / "dados" / "raw"
PROCESSED_DIR = PROJ_ROOT / "dados" / "processed"
