"""Main entrypoint for Astro."""

from __future__ import annotations

from src.bootstrap import run_application


def main() -> None:
    """Entrypoint executed via ``python -m src.main``."""

    run_application()


if __name__ == "__main__":
    main()
