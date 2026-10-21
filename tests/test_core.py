# SPDX-License-Identifier: GPL-3.0-or-later
"""Core tests that run without a display or a running fcitx5."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vietfox.core import backend as backend_module
from vietfox.core.backend import Backend
from vietfox.core.store import BOOL, HOTKEY, INT, TEXT, Store
from vietfox.ui.helpers import normalize, pretty_hotkey


class TextTest(unittest.TestCase):
    def test_search_ignores_case_and_accents(self):
        self.assertIn("dau", normalize("Dấu thanh"))
        self.assertIn("ung dung", normalize("ỨNG DỤNG"))
        self.assertEqual(normalize("Đặc biệt"), "dac biet")

    def test_hotkey_labels(self):
        self.assertEqual(pretty_hotkey("grave"), "`")
        self.assertEqual(pretty_hotkey("Control+grave"), "Ctrl + `")
        self.assertEqual(pretty_hotkey(""), "")


class StoreTest(unittest.TestCase):
    class FakeBackend:
        def __init__(self):
            self.values = {"Mode": "Sen", "SpellCheck": "True", "WaitMs": "50"}
            self.saves = 0

        def save_main(self):
            self.saves += 1

    def make_store(self):
        store = Store(self.FakeBackend())
        store.register("Mode", TEXT, "Sen", "Chế độ")
        store.register("SpellCheck", BOOL, True, "Chính tả")
        store.register("WaitMs", INT, 50, "Chờ")
        store.register("MenuKey", HOTKEY, "grave", "Menu")
        return store

    def test_reads_typed_values(self):
        store = self.make_store()
        self.assertEqual(store.get("Mode"), "Sen")
        self.assertIs(store.get("SpellCheck"), True)
        self.assertEqual(store.get("WaitMs"), 50)
        self.assertEqual(store.get("MenuKey"), "grave")

    def test_missing_values_fall_back_to_defaults(self):
        store = self.make_store()
        self.assertEqual(store.get("UnknownLater"), "")

    def test_set_encodes_and_returns_old_value(self):
        store = self.make_store()
        old = store.set("SpellCheck", False)
        self.assertIs(old, True)
        self.assertEqual(store.backend.values["SpellCheck"], "False")
        self.assertIs(store.get("SpellCheck"), False)
        self.assertEqual(store.backend.saves, 1)

    def test_hotkey_is_stored_as_key_list(self):
        store = self.make_store()
        store.set("MenuKey", "Control+space")
        self.assertEqual(store.backend.values["MenuKey"], {"0": "Control+space"})
        store.set("MenuKey", "")
        self.assertEqual(store.backend.values["MenuKey"], "")

    def test_reset_uses_declared_defaults(self):
        store = self.make_store()
        store.set_many({"SpellCheck": False, "WaitMs": 80})
        old = store.reset()
        self.assertIs(old["SpellCheck"], False)
        self.assertIs(store.get("SpellCheck"), True)
        self.assertEqual(store.get("WaitMs"), 50)
        self.assertEqual(store.get("MenuKey"), "grave")


class OfflineBackendTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_config = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self.temp.name
        os.environ["VIETFOX_OFFLINE"] = "1"

    def tearDown(self):
        os.environ.pop("VIETFOX_OFFLINE", None)
        if self.old_config is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.old_config
        self.temp.cleanup()

    def test_values_survive_without_fcitx5(self):
        backend = Backend()
        self.assertFalse(backend.online)
        backend.values = {"Mode": "Preedit", "MenuKey": {"0": "grave"}}
        backend.save_main()

        again = Backend()
        self.assertFalse(again.online)
        self.assertEqual(again.values["Mode"], "Preedit")
        self.assertEqual(again.values["MenuKey"], {"0": "grave"})
        self.assertTrue(os.path.exists(backend_module.state_path()))

    def test_macros_and_rules_use_the_local_file(self):
        backend = Backend()
        backend.set_macros([{"Key": "vf", "Value": "Vietfox"}])
        backend.set_rules([{"App": "zalo", "Mode": "5"}])
        again = Backend()
        self.assertEqual(again.get_macros(), [{"Key": "vf", "Value": "Vietfox"}])
        self.assertEqual(again.get_rules(), [{"App": "zalo", "Mode": "5"}])


if __name__ == "__main__":
    unittest.main()
