from __future__ import annotations

from app import config


def main() -> None:
    config.ensure_directories()
    from app.ui import launch

    launch()


if __name__ == "__main__":
    main()
