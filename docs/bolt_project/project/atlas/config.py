"""Atlas configuration."""
import os
from pathlib import Path

ATLAS_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("ATLAS_DATA_DIR", ATLAS_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "atlas.db"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_API = "https://api.github.com"
USER_AGENT = "UniversalCapabilityAtlas/0.1 (research catalog; contact via repo owner)"

HOST = os.environ.get("ATLAS_HOST", "127.0.0.1")
PORT = int(os.environ.get("ATLAS_PORT", "8790"))
