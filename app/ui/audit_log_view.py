from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.components import (
    Pagination,
    SectionTitle,
    build_treeview,
    ghost_button,
    style_treeview,
)
from app.utils.helpers import format_datetime

_PAGE_SIZE = 25
_STATUS_FILTER = ("Semua Status", "SUCCESS", "FAILED", "LOCKED")


class AuditLogView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._page = 1
        self._total_pages = 1
        self._username = None
        self._action = None
        self._status = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(4, 14))
        SectionTitle(header, "Audit Log", "Jejak aktivitas pengguna dan peristiwa keamanan sistem.").pack(side="left", anchor="w")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))
        self.username_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Filter username...", width=220, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, border_color=theme.COLOR_INPUT_BORDER, text_color=theme.COLOR_TEXT,
        )
        self.username_entry.pack(side="left")
        self.username_entry.bind("<Return>", lambda _e: self._apply_filters())

        actions = ["Semua Aksi", *app.container.audit.distinct_actions()]
        self.action_menu = ctk.CTkOptionMenu(
            toolbar, values=actions, width=200, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, button_color=theme.COLOR_PRIMARY_DEEP, button_hover_color=theme.COLOR_PRIMARY,
            text_color=theme.COLOR_TEXT, dropdown_fg_color=theme.COLOR_SURFACE_ALT, dropdown_text_color=theme.COLOR_TEXT,
            command=self._on_action,
        )
        self.action_menu.set("Semua Aksi")
        self.action_menu.pack(side="left", padx=8)
        self.status_menu = ctk.CTkOptionMenu(
            toolbar, values=list(_STATUS_FILTER), width=160, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, button_color=theme.COLOR_PRIMARY_DEEP, button_hover_color=theme.COLOR_PRIMARY,
            text_color=theme.COLOR_TEXT, dropdown_fg_color=theme.COLOR_SURFACE_ALT, dropdown_text_color=theme.COLOR_TEXT,
            command=self._on_status,
        )
        self.status_menu.set("Semua Status")
        self.status_menu.pack(side="left")
        ghost_button(toolbar, "Terapkan", self._apply_filters, width=120, icon="🔍").pack(side="left", padx=8)
        ghost_button(toolbar, "Muat Ulang", self._reload, width=130, icon="↻").pack(side="right")

        style_treeview(self.winfo_toplevel())
        columns = [
            ("time", "Waktu", 150),
            ("user", "User", 110),
            ("role", "Role", 110),
            ("action", "Aksi", 160),
            ("status", "Status", 90),
            ("ip", "IP", 120),
            ("host", "Host", 120),
            ("detail", "Detail", 260),
        ]
        self.tree = build_treeview(self, columns, height=14)
        for status, color in theme.STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=color)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 4))
        self.pagination = Pagination(footer, self._goto_page)
        self.pagination.pack(side="right")

        self._reload()

    def _apply_filters(self) -> None:
        username = self.username_entry.get().strip()
        self._username = username or None
        self._page = 1
        self._reload()

    def _on_action(self, value: str) -> None:
        self._action = None if value == "Semua Aksi" else value
        self._page = 1
        self._reload()

    def _on_status(self, value: str) -> None:
        self._status = None if value == "Semua Status" else value
        self._page = 1
        self._reload()

    def _goto_page(self, page: int) -> None:
        self._page = page
        self._reload()

    def _reload(self) -> None:
        logs, total = self._app.container.audit.list_logs(
            page=self._page, page_size=_PAGE_SIZE, username=self._username, action=self._action, status=self._status
        )
        self._total_pages = max((total + _PAGE_SIZE - 1) // _PAGE_SIZE, 1)
        self.tree.delete(*self.tree.get_children())
        for log in logs:
            self.tree.insert(
                "", "end",
                values=(
                    format_datetime(log.created_at),
                    log.username,
                    log.role or "-",
                    log.action,
                    log.status,
                    log.ip_address or "-",
                    log.hostname or "-",
                    log.detail or "-",
                ),
                tags=(log.status,),
            )
        self.pagination.update_state(self._page, self._total_pages)
        if not logs:
            self.tree.insert("", "end", values=("Belum ada catatan audit.", "", "", "", "", "", "", ""))
