from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MANUAL_DIR = DATA_DIR / "manual"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = ROOT / "database"
DB_PATH = DB_DIR / "powerstack.duckdb"

for path in [RAW_DIR, MANUAL_DIR, PROCESSED_DIR, DB_DIR]:
    path.mkdir(parents=True, exist_ok=True)
