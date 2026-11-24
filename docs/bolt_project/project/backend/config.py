"""Central configuration. Env vars win; a .env next to the backend is honored."""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = Path(os.environ.get("DAZY_DATA_DIR", BACKEND_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "dazy.db"


def _load_env_file() -> None:
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


GEMINI_API_KEY = env("GEMINI_API_KEY")
GROQ_API_KEY = env("GROQ_API_KEY")
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY")
DEEPSEEK_API_KEY = env("DEEPSEEK_API_KEY")

GEMINI_MODEL = env("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = env("GROQ_MODEL", "qwen/qwen3.8-27b")
OPENROUTER_MODEL = env("OPENROUTER_MODEL", "openai/gpt-4o-mini")
DEEPSEEK_MODEL = env("DEEPSEEK_MODEL", "deepseek-chat")

# Optional local runtime (Ollama or any OpenAI-compatible server). Never required.
LOCAL_LLM_URL = env("LOCAL_LLM_URL")
LOCAL_LLM_MODEL = env("LOCAL_LLM_MODEL", "llama3.2")

HOST = env("DAZY_HOST", "127.0.0.1")
PORT = int(env("DAZY_PORT", "8787"))
MAX_TURNS = int(env("DAZY_RATE_MAX_TURNS", "30"))
WINDOW_SECS = int(env("DAZY_RATE_WINDOW_SECS", "300"))
