# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed view over the raw fcitx5 configuration."""

from __future__ import annotations

from .backend import Backend, BackendError

BOOL = "bool"
INT = "int"
TEXT = "text"
HOTKEY = "hotkey"

_TRUE = {"true", "1", "yes", "on"}


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in _TRUE


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _as_hotkey(value: object) -> str:
    """A fcitx KeyList is a dictionary of index -> key name."""
    if isinstance(value, dict):
        return " ".join(str(value[key]) for key in sorted(value, key=lambda k: _as_int(k)))
    return str(value or "")


class Store:
    """The settings used by the window, with the defaults each page declares."""

    def __init__(self, backend: Backend | None = None) -> None:
        self.backend = backend or Backend()
        self._kinds: dict[str, str] = {}
        self._defaults: dict[str, object] = {}
        self._titles: dict[str, str] = {}

    # ----------------------------------------------------------------- schema
    def register(self, key: str, kind: str, default: object, title: str = "") -> None:
        self._kinds[key] = kind
        self._defaults[key] = default
        if title:
            self._titles[key] = title

    def keys(self):
        return list(self._kinds)

    def kind(self, key: str) -> str:
        return self._kinds.get(key, TEXT)

    def title(self, key: str) -> str:
        return self._titles.get(key, key)

    # ------------------------------------------------------------------ read
    def get(self, key: str):
        kind = self.kind(key)
        default = self._defaults.get(key, "")
        present = key in self.backend.values
        raw = self.backend.values.get(key)
        if kind == BOOL:
            return _as_bool(raw) if present and raw is not None else bool(default)
        if kind == INT:
            return _as_int(raw, _as_int(default)) if present else _as_int(default)
        if kind == HOTKEY:
            return _as_hotkey(raw) if present else _as_hotkey(default)
        if not present or raw is None:
            return str(default)
        return str(raw)

    def raw_snapshot(self) -> dict:
        return dict(self.backend.values)

    # ----------------------------------------------------------------- write
    def set(self, key: str, value) -> object:
        """Stores one value and returns the previous one, for undo."""
        old = self.get(key)
        self.set_many({key: value})
        return old

    def set_many(self, values: dict[str, object]) -> dict[str, object]:
        old = {key: self.get(key) for key in values}
        previous_raw = {key: self.backend.values.get(key) for key in values}
        for key, value in values.items():
            self.backend.values[key] = self._encode(key, value)
        try:
            self.backend.save_main()
        except BackendError:
            for key, raw in previous_raw.items():
                if raw is None:
                    self.backend.values.pop(key, None)
                else:
                    self.backend.values[key] = raw
            raise
        return old

    def _encode(self, key: str, value) -> object:
        kind = self.kind(key)
        if kind == BOOL:
            return "True" if value else "False"
        if kind == INT:
            return str(int(value))
        if kind == HOTKEY:
            text = str(value or "").strip()
            return {"0": text} if text else ""
        return str(value)

    def defaults(self) -> dict[str, object]:
        return {key: self._defaults[key] for key in self._kinds if key in self._defaults}

    def reset(self) -> dict[str, object]:
        """Sets every registered setting back to its default."""
        return self.set_many(self.defaults())
