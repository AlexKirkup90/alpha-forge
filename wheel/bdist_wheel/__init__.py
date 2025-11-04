"""Stub implementation of the bdist_wheel command."""
from __future__ import annotations

from setuptools import Command


class bdist_wheel(Command):  # type: ignore[misc]
    """No-op command used when the real wheel package is unavailable."""

    description = "create a wheel distribution (stub)"
    user_options: list[tuple[str, str | None, str]] = []

    def initialize_options(self) -> None:  # pragma: no cover
        pass

    def finalize_options(self) -> None:  # pragma: no cover
        pass

    def run(self) -> None:  # pragma: no cover
        pass

    @staticmethod
    def egg2dist(egg_info_dir, dist_info_dir):
        import os
        import shutil

        if os.path.exists(dist_info_dir):
            shutil.rmtree(dist_info_dir)
        shutil.copytree(egg_info_dir, dist_info_dir, dirs_exist_ok=True)

    @staticmethod
    def write_wheelfile(dist_info_dir):
        from pathlib import Path

        path = Path(dist_info_dir) / 'WHEEL'
        path.write_text('Wheel-Version: 1.0\nGenerator: stub\nRoot-Is-Purelib: true\nTag: py3-none-any\n')


__all__ = ["bdist_wheel"]
