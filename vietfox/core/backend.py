# SPDX-License-Identifier: GPL-3.0-or-later
"""Settings backend for Vietfox.

The settings live in the fcitx5 addon while fcitx5 is running.  Vietfox talks to
``org.fcitx.Fcitx.Controller1`` so a change reaches the typing engine at once.
When fcitx5 is not running the same values are kept in
``~/.config/vietfox/state.json`` and are applied the next time the window opens
with fcitx5 available.
"""

from __future__ import annotations

import json
import os

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

FCITX_NAME = "org.fcitx.Fcitx5"
FCITX_PATH = "/controller"
FCITX_IFACE = "org.fcitx.Fcitx.Controller1"
ADDON_NAMES = ("ngosen", "vietfox")


class BackendError(Exception):
    """A change could not be written."""


def _config_home() -> str:
    return os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))


def _data_home() -> str:
    return os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))


def state_path() -> str:
    return os.path.join(_config_home(), "vietfox", "state.json")


def dictionary_path() -> str:
    """The dictionary the engine reads for custom words."""
    return os.path.join(_data_home(), "fcitx5", "ngosen", "vietnamese.cm.dict")


class Backend:
    """Reads and writes the fcitx5 addon configuration."""

    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.online = False
        self.addon = ADDON_NAMES[0]
        self._proxy: Gio.DBusProxy | None = None
        self._local: dict[str, object] = {}
        self._load()

    # ------------------------------------------------------------------ setup
    def _load(self) -> None:
        self._load_local()
        if os.environ.get("VIETFOX_OFFLINE"):
            return
        try:
            self._proxy = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                None,
                FCITX_NAME,
                FCITX_PATH,
                FCITX_IFACE,
                None,
            )
        except GLib.Error:
            self._proxy = None
            return
        if not self._proxy.get_name_owner():
            self._proxy = None
            return
        for addon in ADDON_NAMES:
            try:
                values = self._get_config(addon)
            except GLib.Error:
                continue
            self.addon = addon
            self.values = dict(values)
            self.online = True
            self._apply_pending()
            return

    def _apply_pending(self) -> None:
        """Offline edits are written to fcitx5 as soon as it is reachable."""
        if not self._local.get("pending"):
            return
        settings = self._local.get("settings")
        if isinstance(settings, dict):
            self.values.update(settings)
        try:
            self.save_main()
            if isinstance(self._local.get("macros"), list):
                self.set_macros(
                    [_clean_pair(item, "Key", "Value") for item in self._local["macros"] if isinstance(item, dict)]
                )
            if isinstance(self._local.get("rules"), list):
                self.set_rules(
                    [_clean_pair(item, "App", "Mode") for item in self._local["rules"] if isinstance(item, dict)]
                )
        except BackendError:
            return
        self._local = {}
        try:
            os.remove(state_path())
        except OSError:
            pass

    def _load_local(self) -> None:
        try:
            with open(state_path(), encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        self._local = data
        settings = data.get("settings")
        if isinstance(settings, dict):
            self.values = dict(settings)

    def _get_config(self, addon: str, sub: str | None = None) -> dict:
        assert self._proxy is not None
        path = f"fcitx://config/addon/{addon}"
        if sub:
            path += f"/{sub}"
        result = self._proxy.call_sync(
            "GetConfig",
            GLib.Variant("(s)", (path,)),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        variant = result.get_child_value(0).get_variant()
        unpacked = variant.unpack()
        return unpacked if isinstance(unpacked, dict) else {}

    # ------------------------------------------------------------------- save
    def save_main(self) -> None:
        """Writes every value back, so fcitx5 sees one consistent config."""
        if not self.online:
            self._write_local()
            return
        assert self._proxy is not None
        payload: dict[str, GLib.Variant] = {}
        for key, value in self.values.items():
            if isinstance(value, dict):
                payload[str(key)] = GLib.Variant(
                    "a{sv}",
                    {str(k): GLib.Variant("s", str(v)) for k, v in value.items()},
                )
            elif isinstance(value, bool):
                payload[str(key)] = GLib.Variant("s", "True" if value else "False")
            else:
                payload[str(key)] = GLib.Variant("s", str(value))
        path = f"fcitx://config/addon/{self.addon}"
        try:
            self._proxy.call_sync(
                "SetConfig",
                GLib.Variant("(sv)", (path, GLib.Variant("a{sv}", payload))),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error as error:
            raise BackendError(str(error)) from error

    def _write_local(self) -> None:
        self._local["settings"] = self.values
        self._local["pending"] = True
        self._write_local_file()

    def _write_local_file(self) -> None:
        path = state_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self._local, handle, indent=2, ensure_ascii=False)
        except OSError as error:
            raise BackendError(str(error)) from error

    # --------------------------------------------------------------- subconfig
    def get_macros(self) -> list[dict[str, str]]:
        if not self.online:
            macros = self._local.get("macros", [])
            return [_clean_pair(item, "Key", "Value") for item in macros if isinstance(item, dict)]
        try:
            data = self._get_config(self.addon, "ngosen-macro")
        except GLib.Error:
            return []
        return _dict_list(data.get("Macro"), "Key", "Value")

    def set_macros(self, macros: list[dict[str, str]]) -> None:
        if not self.online:
            self._local["macros"] = macros
            self._local["pending"] = True
            self._write_local_file()
            return
        self._set_sub("ngosen-macro", "Macro", macros, ("Key", "Value"))

    def get_rules(self) -> list[dict[str, str]]:
        if not self.online:
            rules = self._local.get("rules", [])
            return [_clean_pair(item, "App", "Mode") for item in rules if isinstance(item, dict)]
        try:
            data = self._get_config(self.addon, "app_rules")
        except GLib.Error:
            return []
        return _dict_list(data.get("Rules"), "App", "Mode")

    def set_rules(self, rules: list[dict[str, str]]) -> None:
        if not self.online:
            self._local["rules"] = rules
            self._local["pending"] = True
            self._write_local_file()
            return
        self._set_sub("app_rules", "Rules", rules, ("App", "Mode"))

    def _set_sub(
        self,
        sub: str,
        root_key: str,
        rows: list[dict[str, str]],
        fields: tuple[str, str],
    ) -> None:
        assert self._proxy is not None
        path = f"fcitx://config/addon/{self.addon}/{sub}"
        if rows:
            wrapped = GLib.Variant(
                "a{sv}",
                {
                    str(index): GLib.Variant(
                        "a{sv}", {name: GLib.Variant("s", str(row.get(name, ""))) for name in fields}
                    )
                    for index, row in enumerate(rows)
                },
            )
        else:
            wrapped = GLib.Variant("s", "")
        try:
            self._proxy.call_sync(
                "SetConfig",
                GLib.Variant("(sv)", (path, GLib.Variant("a{sv}", {root_key: wrapped}))),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error as error:
            raise BackendError(str(error)) from error

    def reload_addon(self) -> None:
        if not self.online or self._proxy is None:
            return
        try:
            self._proxy.call_sync(
                "ReloadAddonConfig",
                GLib.Variant("(s)", (self.addon,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error:
            pass

    # -------------------------------------------------------------- dictionary
    def get_dictionary(self) -> list[str]:
        try:
            with open(dictionary_path(), encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        except OSError:
            return []

    def set_dictionary(self, words: list[str]) -> None:
        path = dictionary_path()
        try:
            if words:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(words) + "\n")
            elif os.path.exists(path):
                os.remove(path)
        except OSError as error:
            raise BackendError(str(error)) from error
        self.reload_addon()

    # ----------------------------------------------------------------- backup
    def snapshot(self) -> dict:
        return {
            "meta": {"version": 1, "app": "Vietfox"},
            "settings": dict(self.values),
            "macros": self.get_macros(),
            "rules": self.get_rules(),
            "dictionary": self.get_dictionary(),
        }

    def restore(self, data: dict) -> None:
        # Accept both Vietfox backups and backups written by the old Ngó Sen window.
        settings = data.get("settings") if isinstance(data.get("settings"), dict) else data.get("config")
        if isinstance(settings, dict):
            self.values = dict(settings)
            self.save_main()
        if isinstance(data.get("macros"), list):
            self.set_macros(
                [_clean_pair(item, "Key", "Value") for item in data["macros"] if isinstance(item, dict)]
            )
        if isinstance(data.get("rules"), list):
            self.set_rules(
                [_clean_pair(item, "App", "Mode") for item in data["rules"] if isinstance(item, dict)]
            )
        words = data.get("dictionary")
        if isinstance(words, str):
            words = words.splitlines()
        if isinstance(words, list):
            self.set_dictionary([str(word).strip() for word in words if str(word).strip()])


def _clean_pair(item: dict, first: str, second: str) -> dict[str, str]:
    return {first: str(item.get(first, "")), second: str(item.get(second, ""))}


def _dict_list(value: object, first: str, second: str) -> list[dict[str, str]]:
    """fcitx5 sends a list option as an index -> fields dictionary."""
    if isinstance(value, dict):
        ordered = sorted(
            value.items(),
            key=lambda item: (0, int(item[0])) if str(item[0]).isdigit() else (1, str(item[0])),
        )
        rows = []
        for _, entry in ordered:
            if isinstance(entry, dict):
                rows.append(_clean_pair(entry, first, second))
        return rows
    if isinstance(value, list):
        return [_clean_pair(item, first, second) for item in value if isinstance(item, dict)]
    return []
