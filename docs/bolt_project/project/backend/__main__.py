"""DAZY AI OS — local backend entrypoint. Runs on 127.0.0.1 by default."""
import uvicorn

from . import config


def main() -> None:
    print(f"[dazy] starting local backend on http://{config.HOST}:{config.PORT}")
    uvicorn.run("backend.api:app", host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
