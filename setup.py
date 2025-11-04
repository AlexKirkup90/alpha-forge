from __future__ import annotations

from setuptools import setup

cmdclass = {}
try:  # pragma: no cover - exercised during packaging
    from wheel.bdist_wheel import bdist_wheel  # type: ignore
except Exception:  # pragma: no cover
    bdist_wheel = None  # type: ignore
else:  # pragma: no cover
    cmdclass["bdist_wheel"] = bdist_wheel

setup(cmdclass=cmdclass)
