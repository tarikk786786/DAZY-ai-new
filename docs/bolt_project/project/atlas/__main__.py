"""Atlas entrypoint: python3 -m atlas"""
import uvicorn

from . import config


def main() -> None:
    from . import db, seed
    db.migrate()
    print("[atlas] seeding:", seed.seed())
    print(f"[atlas] dashboard on http://127.0.0.1:{config.PORT}")
    uvicorn.run("atlas.api:app", host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
