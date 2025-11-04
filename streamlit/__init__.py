"""Minimal stub of the Streamlit API for offline testing."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


def set_page_config(**kwargs: Any) -> None:  # noqa: D401
    """Record page configuration (no-op for stub)."""


def title(text: str) -> None:
    print(f"[streamlit] title: {text}")


def subheader(text: str) -> None:
    print(f"[streamlit] subheader: {text}")


def header(text: str) -> None:
    print(f"[streamlit] header: {text}")


def markdown(text: str) -> None:
    print(f"[streamlit] markdown: {text}")


def code(content: str, language: str | None = None) -> None:
    print(f"[streamlit] code ({language or 'text'}):\n{content}")


def json_display(data: Any) -> None:
    print(f"[streamlit] json: {json.dumps(data, indent=2, sort_keys=True)}")


def json(data: Any) -> None:
    json_display(data)


def divider() -> None:
    print("[streamlit] divider")


def info(text: str) -> None:
    print(f"[streamlit] info: {text}")


def checkbox(label: str, value: bool = False) -> bool:
    print(f"[streamlit] checkbox: {label} (default={value})")
    return value


def text_input(label: str, value: str = "") -> str:
    print(f"[streamlit] text_input: {label} (default={value})")
    return value


@dataclass
class _Sidebar:
    """Simple container mimicking Streamlit's sidebar."""

    def header(self, text: str) -> None:
        header(text)

    def text_input(self, label: str, value: str = "") -> str:
        return text_input(label, value=value)

    def checkbox(self, label: str, value: bool = False) -> bool:
        return checkbox(label, value=value)


sidebar = _Sidebar()

__all__ = [
    "checkbox",
    "code",
    "divider",
    "header",
    "info",
    "json",
    "markdown",
    "set_page_config",
    "sidebar",
    "subheader",
    "text_input",
    "title",
]
