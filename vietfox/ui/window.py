# SPDX-License-Identifier: GPL-3.0-or-later
"""The main Vietfox window."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from ..core.backend import Backend, BackendError
from ..core.store import Store
from ..version import APP_ID, APP_NAME, VERSION
from .helpers import normalize
from .pages.about import AboutPage
from .pages.apps import AppsPage
from .pages.base import Page
from .pages.macros import MacrosPage
from .pages.shortcuts import ShortcutsPage
from .pages.typing import TypingPage

PAGE_CLASSES = (TypingPage, MacrosPage, ShortcutsPage, AppsPage, AboutPage)


class VietfoxWindow(Adw.ApplicationWindow):
    def __init__(self, application) -> None:
        super().__init__(application=application)
        self.set_title(APP_NAME)
        self.set_default_size(1000, 760)
        self.set_size_request(360, 420)

        self.store = Store()
        self.backend = self.store.backend
        self.pages: list[Page] = []
        self._current = 0
        self._selecting = False

        self._load_css()
        self._build_shell()
        self._build_pages()
        self._build_navigation()
        self._select_page(0)

    # ------------------------------------------------------------------- css
    def _load_css(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "style.css")
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(path)
        except GLib.Error:
            return
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    # ----------------------------------------------------------------- shell
    def _build_shell(self) -> None:
        self.split_view = Adw.NavigationSplitView()
        self.split_view.set_min_sidebar_width(250)
        self.split_view.set_max_sidebar_width(340)
        self.split_view.set_sidebar_width_fraction(0.3)
        self.set_content(self.split_view)

        narrow = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 580sp"))
        narrow.add_setter(self.split_view, "collapsed", True)
        self.add_breakpoint(narrow)

        # Sidebar ----------------------------------------------------------
        self.sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_title_widget(Adw.WindowTitle(title=APP_NAME))
        self.search_button = Gtk.ToggleButton()
        self.search_button.set_icon_name("system-search-symbolic")
        self.search_button.add_css_class("flat")
        self.search_button.set_tooltip_text("Tìm cài đặt (Ctrl+F)")
        sidebar_header.pack_end(self.search_button)
        self.sidebar_toolbar.add_top_bar(sidebar_header)

        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.search_revealer = Gtk.Revealer()
        self.search_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        search_holder = Gtk.Box()
        search_holder.set_margin_start(12)
        search_holder.set_margin_end(12)
        search_holder.set_margin_top(4)
        search_holder.set_margin_bottom(6)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Tìm cài đặt")
        self.search_entry.set_hexpand(True)
        search_holder.append(self.search_entry)
        self.search_revealer.set_child(search_holder)
        sidebar_box.append(self.search_revealer)

        self.sidebar_stack = Gtk.Stack()
        self.sidebar_stack.set_vexpand(True)
        self.sidebar_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.sidebar_stack.set_transition_duration(120)

        self.nav_list = Gtk.ListBox()
        self.nav_list.add_css_class("navigation-sidebar")
        self.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.nav_list.set_margin_start(6)
        self.nav_list.set_margin_end(6)
        self.nav_list.set_margin_top(2)
        self.nav_list.set_margin_bottom(8)
        self.nav_list.connect("row-selected", self._on_nav_selected)
        nav_scroller = Gtk.ScrolledWindow()
        nav_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        nav_scroller.set_child(self.nav_list)
        self.sidebar_stack.add_named(nav_scroller, "pages")

        self.results_list = Gtk.ListBox()
        self.results_list.add_css_class("navigation-sidebar")
        self.results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_list.set_margin_start(6)
        self.results_list.set_margin_end(6)
        self.results_list.set_margin_top(2)
        results_scroller = Gtk.ScrolledWindow()
        results_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        results_scroller.set_child(self.results_list)
        self.sidebar_stack.add_named(results_scroller, "results")

        sidebar_box.append(self.sidebar_stack)

        self.status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_box.set_margin_start(16)
        self.status_box.set_margin_end(16)
        self.status_box.set_margin_top(6)
        self.status_box.set_margin_bottom(12)
        self.status_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
        self.status_icon.set_pixel_size(14)
        self.status_label = Gtk.Label()
        self.status_label.add_css_class("caption")
        self.status_label.add_css_class("dim-label")
        self.status_label.set_xalign(0)
        self.status_box.append(self.status_icon)
        self.status_box.append(self.status_label)
        sidebar_box.append(self.status_box)
        self.sidebar_toolbar.set_content(sidebar_box)
        self._update_status()

        sidebar_nav = Adw.NavigationPage(child=self.sidebar_toolbar, title=APP_NAME)
        self.split_view.set_sidebar(sidebar_nav)

        # Content ----------------------------------------------------------
        self.content_toolbar = Adw.ToolbarView()
        self.content_header = Adw.HeaderBar()
        self.content_title = Adw.WindowTitle(title="Gõ chữ")
        self.content_header.set_title_widget(self.content_title)
        self.content_toolbar.add_top_bar(self.content_header)

        self.banner = Adw.Banner(
            title="Chưa kết nối được fcitx5 — thay đổi sẽ áp dụng khi fcitx5 chạy lại."
        )
        if hasattr(self.banner, "set_button_label"):
            self.banner.set_button_label("Thử lại")
            self.banner.connect("button-clicked", lambda _banner: self._retry_backend())
        self.banner.set_revealed(not self.backend.online)
        self.content_toolbar.add_top_bar(self.banner)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(140)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.stack)
        self.content_toolbar.set_content(self.toast_overlay)

        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menu chính")
        menu_button.set_menu_model(self._build_menu())
        self.content_header.pack_end(menu_button)

        self._install_actions()
        self.content_nav = Adw.NavigationPage(child=self.content_toolbar, title="Gõ chữ")
        self.split_view.set_content(self.content_nav)

        # Search wiring ----------------------------------------------------
        self.search_button.connect("notify::active", self._on_search_toggled)
        self.search_entry.connect("search-changed", lambda _entry: self._run_search())
        self.search_entry.connect("activate", lambda _entry: self._open_first_result())
        self.search_entry.connect("stop-search", lambda _entry: self._toggle_search(False))
        self.results_list.connect("row-activated", self._on_result_activated)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key)
        self.add_controller(key_controller)

    def _build_menu(self) -> Gio.Menu:
        menu = Gio.Menu()
        backup = Gio.MenuItem.new("Sao lưu cấu hình…", "win.backup")
        restore = Gio.MenuItem.new("Khôi phục cấu hình…", "win.restore")
        backup_section = Gio.Menu()
        backup_section.append_item(backup)
        backup_section.append_item(restore)
        menu.append_section(None, backup_section)

        reset_section = Gio.Menu()
        reset_section.append("Đặt lại về mặc định", "win.reset")
        menu.append_section(None, reset_section)

        last = Gio.Menu()
        last.append("Giới thiệu Vietfox", "win.about")
        last.append("Thoát", "win.quit")
        menu.append_section(None, last)
        return menu

    def _install_actions(self) -> None:
        group = Gio.SimpleActionGroup()
        actions = {
            "backup": self._backup,
            "restore": self._restore,
            "reset": self._reset,
            "about": lambda: self.show_about(),
            "quit": lambda: self.close(),
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _action, _param, cb=callback: cb())
            group.add_action(action)
        self.insert_action_group("win", group)

    def _build_pages(self) -> None:
        for cls in PAGE_CLASSES:
            page = cls(self)
            self.pages.append(page)
            self.stack.add_named(page.widget, page.ident)

    def _build_navigation(self) -> None:
        self._selecting = True
        for row in list(self.nav_list):
            self.nav_list.remove(row)
        for index, page in enumerate(self.pages):
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(7)
            box.set_margin_bottom(7)
            box.set_margin_start(12)
            box.set_margin_end(12)
            icon = Gtk.Image.new_from_icon_name(page.icon)
            icon.set_pixel_size(18)
            label = Gtk.Label(label=page.title, xalign=0)
            box.append(icon)
            box.append(label)
            row.set_child(box)
            row.page_index = index
            self.nav_list.append(row)
        self._selecting = False

    # --------------------------------------------------------------- navigation
    def _on_nav_selected(self, _list, row) -> None:
        if row is None or self._selecting:
            return
        index = getattr(row, "page_index", 0)
        self._select_page(index)

    def _select_page(self, index: int) -> None:
        if not self.pages:
            return
        index = max(0, min(index, len(self.pages) - 1))
        page = self.pages[index]
        self._current = index
        self.stack.set_visible_child_name(page.ident)
        self.content_title.set_title(page.title)
        self.content_nav.set_title(page.title)
        row = self.nav_list.get_row_at_index(index)
        if row is not None and self.nav_list.get_selected_row() is not row:
            self._selecting = True
            self.nav_list.select_row(row)
            self._selecting = False
        if self.split_view.get_collapsed():
            self.split_view.set_show_content(True)

    def reload_pages(self) -> None:
        ident = self.pages[self._current].ident if self.pages else "typing"
        for page in self.pages:
            page.discard_pending()
            self.stack.remove(page.widget)
        self.pages = []
        self._build_pages()
        self._build_navigation()
        index = next((i for i, page in enumerate(self.pages) if page.ident == ident), 0)
        self._select_page(index)
        self._toggle_search(False)

    # ------------------------------------------------------------------ search
    def _on_search_toggled(self, button, _pspec) -> None:
        active = button.get_active()
        self.search_revealer.set_reveal_child(active)
        if active:
            self.search_entry.grab_focus()
        else:
            self.search_entry.set_text("")
            self.sidebar_stack.set_visible_child_name("pages")

    def _toggle_search(self, active: bool) -> None:
        self.search_button.set_active(active)
        if not active:
            self.search_revealer.set_reveal_child(False)
            self.search_entry.set_text("")
            self.sidebar_stack.set_visible_child_name("pages")

    def _run_search(self) -> None:
        query = normalize(self.search_entry.get_text().strip())
        for row in list(self.results_list):
            self.results_list.remove(row)
        if not query:
            self.sidebar_stack.set_visible_child_name("pages")
            return

        matches = []
        for page_index, page in enumerate(self.pages):
            for row, title, subtitle, keywords in page.items:
                haystack = normalize(" ".join((title, subtitle, keywords, page.title)))
                if query in haystack:
                    score = 0 if normalize(title).startswith(query) else 1
                    matches.append((score, page_index, row, title, subtitle, page))
        matches.sort(key=lambda item: (item[0], normalize(item[3])))

        if not matches:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label="Không tìm thấy cài đặt nào")
            label.add_css_class("dim-label")
            label.set_margin_top(18)
            label.set_margin_bottom(18)
            row.set_child(label)
            row.set_activatable(False)
            self.results_list.append(row)
        else:
            for _score, page_index, target, title, subtitle, page in matches[:60]:
                self.results_list.append(
                    self._result_row(page_index, target, title, subtitle, page)
                )
        self.sidebar_stack.set_visible_child_name("results")

    def _result_row(self, page_index, target, title, subtitle, page) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.result = (page_index, target)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(7)
        box.set_margin_bottom(7)
        box.set_margin_start(10)
        box.set_margin_end(10)
        icon = Gtk.Image.new_from_icon_name(page.icon)
        icon.set_pixel_size(16)
        icon.set_valign(Gtk.Align.START)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.set_wrap(True)
        detail = Gtk.Label(label=subtitle or page.title, xalign=0)
        detail.set_wrap(True)
        detail.add_css_class("caption")
        detail.add_css_class("dim-label")
        texts.append(title_label)
        texts.append(detail)
        box.append(icon)
        box.append(texts)
        row.set_child(box)
        return row

    def _open_first_result(self) -> None:
        row = self.results_list.get_row_at_index(0)
        if row is not None and getattr(row, "result", None):
            self._open_result(*row.result)

    def _on_result_activated(self, _list, row) -> None:
        result = getattr(row, "result", None)
        if result:
            self._open_result(*result)

    def _open_result(self, page_index: int, target) -> None:
        self._toggle_search(False)
        self._select_page(page_index)

        def reveal() -> bool:
            try:
                parent = target.get_parent()
                while parent is not None:
                    if isinstance(parent, Adw.ExpanderRow):
                        parent.set_expanded(True)
                    parent = parent.get_parent()
                target.grab_focus()
                target.add_css_class("vf-highlight")
                GLib.timeout_add(1400, lambda: target.remove_css_class("vf-highlight"))
            except Exception:  # the row may have been rebuilt, e.g. macros
                pass
            return False

        GLib.idle_add(reveal)

    # ------------------------------------------------------------------ toasts
    def show_saved(self, title: str, undo) -> None:
        toast = Adw.Toast.new(f"Đã lưu “{title}”.")
        toast.set_button_label("Hoàn tác")
        toast.set_timeout(5)
        toast.connect("button-clicked", lambda _toast: undo())
        self.toast_overlay.add_toast(toast)

    def show_undone(self, title: str) -> None:
        toast = Adw.Toast.new(f"Đã hoàn tác {title}.")
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def show_toast(self, message: str) -> None:
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def show_error(self, message: str) -> None:
        print(f"Vietfox: {message}", file=sys.stderr)
        text = message.strip().splitlines()[0] if message.strip() else "Không lưu được cài đặt."
        if len(text) > 110:
            text = text[:107] + "…"
        toast = Adw.Toast.new(text)
        toast.set_timeout(6)
        toast.set_priority(Adw.ToastPriority.HIGH)
        self.toast_overlay.add_toast(toast)

    def confirm(self, heading: str, body: str, label: str, callback, destructive: bool = False) -> None:
        dialog = Adw.AlertDialog(heading=heading, body=body)
        dialog.add_response("cancel", "Huỷ")
        dialog.add_response("confirm", label)
        if destructive:
            dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        else:
            dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def on_response(_dialog, response) -> None:
            if response == "confirm":
                callback()

        dialog.connect("response", on_response)
        dialog.present(self)

    # ------------------------------------------------------------------ status
    def _update_status(self) -> None:
        if self.backend.online:
            self.status_label.set_text("Đang kết nối fcitx5")
            self.status_icon.set_from_icon_name("emblem-ok-symbolic")
            self.status_box.set_tooltip_text(f"Addon: {self.backend.addon}")
        else:
            self.status_label.set_text("Chưa kết nối fcitx5")
            self.status_icon.set_from_icon_name("dialog-warning-symbolic")
            self.status_box.set_tooltip_text("Thay đổi được lưu tạm, áp dụng khi fcitx5 chạy lại.")

    def _retry_backend(self) -> None:
        backend = Backend()
        self.store = Store(backend)
        self.backend = backend
        self.banner.set_revealed(not backend.online)
        self._update_status()
        self.reload_pages()
        self.show_toast(
            "Đã kết nối fcitx5." if backend.online else "Vẫn chưa kết nối được fcitx5."
        )

    # ------------------------------------------------------------------ dialog
    def show_about(self) -> None:
        about = Adw.AboutDialog(
            application_name=APP_NAME,
            application_icon=APP_ID,
            version=VERSION,
            developer_name="Vietfox",
            comments="Bộ gõ tiếng Việt cho Linux, giao diện theo chuẩn GNOME.",
            website="https://github.com/ngosen/ngosen",
            issue_url="https://github.com/ngosen/ngosen/issues",
            copyright="© 2026 Vietfox contributors",
            license_type=Gtk.License.GPL_3_0,
            developers=["Vietfox contributors"],
        )
        about.add_credit_section(
            "Dựa trên",
            [
                "Ngó Sen — Nguyễn Hoàng Kỳ https://github.com/ngosen/ngosen",
                "Bamboo — https://github.com/BambooEngine/ibus-bamboo",
                "fcitx5 — https://fcitx-im.org",
            ],
        )
        about.present(self)

    # ------------------------------------------------------------------ backup
    def _backup(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Sao lưu cấu hình Vietfox")
        dialog.set_initial_name(f"vietfox-{datetime.now():%Y-%m-%d}.json")

        def done(source, result) -> None:
            try:
                file = source.save_finish(result)
            except GLib.Error:
                return
            path = file.get_path()
            if not path:
                self.show_error("Không ghi được tệp này.")
                return
            try:
                data = self.backend.snapshot()
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(data, handle, indent=2, ensure_ascii=False)
            except (OSError, BackendError) as error:
                self.show_error(str(error))
                return
            self.show_toast("Đã sao lưu cấu hình.")

        dialog.save(self, None, done)

    def _restore(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Khôi phục cấu hình Vietfox")

        def done(source, result) -> None:
            try:
                file = source.open_finish(result)
            except GLib.Error:
                return
            path = file.get_path()
            if not path:
                return
            try:
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError) as error:
                self.show_error(f"Tệp không hợp lệ: {error}")
                return
            if not isinstance(data, dict) or not any(
                key in data for key in ("settings", "config", "macros", "rules", "dictionary")
            ):
                self.show_error("Tệp không phải bản sao lưu của Vietfox.")
                return

            def confirmed() -> None:
                try:
                    self.backend.restore(data)
                except BackendError as error:
                    self.show_error(str(error))
                    return
                self.reload_pages()
                self.show_toast("Đã khôi phục cấu hình.")

            self.confirm(
                "Khôi phục cấu hình?",
                "Cài đặt hiện tại sẽ được thay bằng cấu hình trong tệp.",
                "Khôi phục",
                confirmed,
            )

        dialog.open(self, None, done)

    def _reset(self) -> None:
        snapshot = self.store.raw_snapshot()

        def confirmed() -> None:
            try:
                self.store.reset()
            except BackendError as error:
                self.show_error(str(error))
                return
            self.reload_pages()
            toast = Adw.Toast.new("Đã đặt lại cài đặt về mặc định.")
            toast.set_button_label("Hoàn tác")
            toast.set_timeout(6)

            def undo(_toast) -> None:
                try:
                    self.backend.values = dict(snapshot)
                    self.backend.save_main()
                except BackendError as error:
                    self.show_error(str(error))
                    return
                self.reload_pages()
                self.show_undone("cài đặt mặc định")

            toast.connect("button-clicked", undo)
            self.toast_overlay.add_toast(toast)

        self.confirm(
            "Đặt lại về mặc định?",
            "Mọi cài đặt trên các trang sẽ trở về giá trị ban đầu.",
            "Đặt lại",
            confirmed,
            destructive=True,
        )

    # ----------------------------------------------------------------- keyboard
    def _on_key(self, _controller, keyval, _keycode, state) -> bool:
        control = bool(state & Gdk.ModifierType.CONTROL_MASK)
        if control and keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self._toggle_search(True)
            self.search_entry.grab_focus()
            return True
        if control and keyval in (Gdk.KEY_q, Gdk.KEY_Q, Gdk.KEY_w, Gdk.KEY_W):
            self.close()
            return True
        if keyval == Gdk.KEY_Escape and self.search_revealer.get_reveal_child():
            self._toggle_search(False)
            return True
        return False

    def do_close_request(self) -> bool:
        for page in self.pages:
            page.flush()
        return False
