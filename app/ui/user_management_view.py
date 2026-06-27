from __future__ import annotations

import customtkinter as ctk

from app.models import ROLE_ADMINISTRATOR, ROLE_USER
from app.ui import theme
from app.ui.components import (
    ConfirmDialog,
    FormField,
    FormSelect,
    Pagination,
    SectionTitle,
    build_treeview,
    danger_button,
    ghost_button,
    primary_button,
    style_treeview,
)

_PAGE_SIZE = 10
_ROLE_FILTER = ("Semua Role", ROLE_ADMINISTRATOR, ROLE_USER)
_ACTIVE_FILTER = ("Semua Status", "Aktif", "Nonaktif")


class UserManagementView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._page = 1
        self._total_pages = 1
        self._search = ""
        self._role = None
        self._active = None
        self._row_ids: dict[str, int] = {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(4, 14))
        SectionTitle(header, "Manajemen User", "Kelola akun, peran, dan status pengguna sistem.").pack(side="left", anchor="w")
        primary_button(header, "Tambah User", self._open_create, width=170, icon="＋").pack(side="right")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Cari username, nama, atau email...", width=300, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, border_color=theme.COLOR_INPUT_BORDER, text_color=theme.COLOR_TEXT,
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda _e: self._apply_search())
        ghost_button(toolbar, "Cari", self._apply_search, width=90, icon="🔍").pack(side="left", padx=10)
        self.role_menu = self._filter_menu(toolbar, list(_ROLE_FILTER), self._on_role)
        self.role_menu.pack(side="left", padx=(0, 8))
        self.active_menu = self._filter_menu(toolbar, list(_ACTIVE_FILTER), self._on_active)
        self.active_menu.pack(side="left")
        ghost_button(toolbar, "Muat Ulang", self._reload, width=130, icon="↻").pack(side="right")

        style_treeview(self.winfo_toplevel())
        columns = [
            ("username", "Username", 140),
            ("name", "Nama Lengkap", 180),
            ("email", "Email", 200),
            ("role", "Role", 120),
            ("status", "Status", 90),
            ("last", "Login Terakhir", 150),
        ]
        self.tree = build_treeview(self, columns, height=11)
        self.tree.tag_configure("Nonaktif", foreground=theme.COLOR_TEXT_MUTED)
        self.tree.tag_configure(ROLE_ADMINISTRATOR, foreground=theme.COLOR_ACCENT)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 4))
        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.pack(side="left")
        ghost_button(actions, "Reset Password", self._reset_password, width=160, icon="⚷").pack(side="left", padx=(0, 8))
        ghost_button(actions, "Ubah Role", self._change_role, width=130, icon="⇅").pack(side="left", padx=(0, 8))
        ghost_button(actions, "Aktif/Nonaktif", self._toggle_active, width=150, icon="◐").pack(side="left", padx=(0, 8))
        danger_button(actions, "Hapus", self._delete_user, width=110, icon="🗑").pack(side="left")

        self.pagination = Pagination(footer, self._goto_page)
        self.pagination.pack(side="right")

        self._reload()

    def _filter_menu(self, master, values: list[str], command) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            master, values=values, width=150, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, button_color=theme.COLOR_PRIMARY_DEEP, button_hover_color=theme.COLOR_PRIMARY,
            text_color=theme.COLOR_TEXT, dropdown_fg_color=theme.COLOR_SURFACE_ALT, dropdown_text_color=theme.COLOR_TEXT,
            command=command,
        )
        menu.set(values[0])
        return menu

    def _apply_search(self) -> None:
        self._search = self.search_entry.get().strip()
        self._page = 1
        self._reload()

    def _on_role(self, value: str) -> None:
        self._role = None if value == "Semua Role" else value
        self._page = 1
        self._reload()

    def _on_active(self, value: str) -> None:
        self._active = None if value == "Semua Status" else (value == "Aktif")
        self._page = 1
        self._reload()

    def _goto_page(self, page: int) -> None:
        self._page = page
        self._reload()

    def _reload(self) -> None:
        rows, total = self._app.container.users.list_users(
            page=self._page, page_size=_PAGE_SIZE, search=self._search, role=self._role, active=self._active
        )
        self._total_pages = max((total + _PAGE_SIZE - 1) // _PAGE_SIZE, 1)
        self._row_ids.clear()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            tags = [row.role_name]
            if not row.is_active:
                tags.append("Nonaktif")
            last_login = row.last_login_at.strftime("%d-%m-%Y %H:%M") if row.last_login_at else "-"
            row_id = self.tree.insert(
                "", "end",
                values=(
                    row.username,
                    row.full_name or "-",
                    row.email or "-",
                    row.role_name,
                    "Aktif" if row.is_active else "Nonaktif",
                    last_login,
                ),
                tags=tuple(tags),
            )
            self._row_ids[row_id] = row.id
        self.pagination.update_state(self._page, self._total_pages)

    def _selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            self._app.notify("Pilih salah satu user terlebih dahulu.", "warning")
            return None
        return self._row_ids.get(selection[0])

    def _open_create(self) -> None:
        CreateUserDialog(self, self._app, on_done=self._reload)

    def _reset_password(self) -> None:
        user_id = self._selected_id()
        if user_id is None:
            return
        ResetPasswordDialog(self, self._app, user_id, on_done=self._reload)

    def _change_role(self) -> None:
        user_id = self._selected_id()
        if user_id is None:
            return
        row = self._app.container.users.get_row(user_id)
        if row is None:
            return
        new_role = ROLE_USER if row.role_name == ROLE_ADMINISTRATOR else ROLE_ADMINISTRATOR

        def confirm() -> None:
            actor = self._app.principal.audit_context()
            result = self._app.container.users.change_role(actor, user_id, new_role)
            self._app.notify(result.message, "success" if result.success else "error")
            self._reload()

        ConfirmDialog(self, "Ubah Role", f"Ubah role {row.username} menjadi {new_role}?", confirm)

    def _toggle_active(self) -> None:
        user_id = self._selected_id()
        if user_id is None:
            return
        row = self._app.container.users.get_row(user_id)
        if row is None:
            return
        actor = self._app.principal.audit_context()
        result = self._app.container.users.set_active(actor, user_id, not row.is_active)
        self._app.notify(result.message, "success" if result.success else "error")
        self._reload()

    def _delete_user(self) -> None:
        user_id = self._selected_id()
        if user_id is None:
            return
        row = self._app.container.users.get_row(user_id)
        if row is None:
            return

        def confirm() -> None:
            actor = self._app.principal.audit_context()
            result = self._app.container.users.delete_user(actor, user_id)
            self._app.notify(result.message, "success" if result.success else "error")
            self._reload()

        ConfirmDialog(self, "Hapus User", f"Yakin menghapus user {row.username}? Tindakan permanen.", confirm, danger=True)


class CreateUserDialog(ctk.CTkToplevel):
    def __init__(self, master, app, on_done) -> None:
        super().__init__(master)
        self._app = app
        self._on_done = on_done
        self.title("Tambah User")
        self.geometry("460x620")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Tambah User Baru", font=theme.font(18, "bold"), text_color=theme.COLOR_TEXT).pack(pady=(22, 4))
        ctk.CTkLabel(
            self, text="User wajib mengganti password saat login pertama.", font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
        ).pack(pady=(0, 14))
        body = ctk.CTkScrollableFrame(self, fg_color="transparent", width=400, height=420)
        body.pack(fill="both", expand=True, padx=20)
        self.username = FormField(body, "Username", width=360)
        self.username.pack(fill="x", pady=6)
        self.full_name = FormField(body, "Nama Lengkap", width=360)
        self.full_name.pack(fill="x", pady=6)
        self.email = FormField(body, "Email", width=360)
        self.email.pack(fill="x", pady=6)
        self.phone = FormField(body, "Nomor HP", width=360)
        self.phone.pack(fill="x", pady=6)
        self.instansi = FormField(body, "Instansi", width=360)
        self.instansi.pack(fill="x", pady=6)
        self.jabatan = FormField(body, "Jabatan", width=360)
        self.jabatan.pack(fill="x", pady=6)
        self.password = FormField(body, "Password", show="•", width=360)
        self.password.pack(fill="x", pady=6)
        self.role = FormSelect(body, "Role", [ROLE_USER, ROLE_ADMINISTRATOR], default=ROLE_USER, width=360)
        self.role.pack(fill="x", pady=6)

        self.message = ctk.CTkLabel(self, text="", font=theme.font(12), text_color=theme.COLOR_DANGER, wraplength=400)
        self.message.pack(pady=(6, 0))
        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=14)
        ghost_button(button_row, "Batal", self._close, width=150).pack(side="left", padx=8)
        primary_button(button_row, "Simpan", self._save, width=180, icon="✓").pack(side="left", padx=8)

    def _save(self) -> None:
        actor = self._app.principal.audit_context()
        result = self._app.container.users.create_user(
            actor,
            self.username.get(),
            self.password.entry.get(),
            self.full_name.get(),
            self.email.get(),
            self.phone.get(),
            self.instansi.get(),
            self.jabatan.get(),
            self.role.get(),
        )
        if result.success:
            self._app.notify(result.message, "success")
            self._on_done()
            self._close()
            return
        self.message.configure(text=result.message)

    def _close(self) -> None:
        self.grab_release()
        self.destroy()


class ResetPasswordDialog(ctk.CTkToplevel):
    def __init__(self, master, app, user_id: int, on_done) -> None:
        super().__init__(master)
        self._app = app
        self._user_id = user_id
        self._on_done = on_done
        self.title("Reset Password")
        self.geometry("420x300")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Reset Password", font=theme.font(18, "bold"), text_color=theme.COLOR_TEXT).pack(pady=(24, 4))
        ctk.CTkLabel(
            self, text="Password baru akan dipaksa diganti saat user login.", font=theme.font(11),
            text_color=theme.COLOR_TEXT_MUTED, wraplength=360,
        ).pack(pady=(0, 16))
        self.password = FormField(self, "Password Baru", show="•", width=340)
        self.password.pack(padx=24, pady=6, fill="x")
        self.message = ctk.CTkLabel(self, text="", font=theme.font(12), text_color=theme.COLOR_DANGER, wraplength=360)
        self.message.pack(pady=(6, 0))
        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=16)
        ghost_button(button_row, "Batal", self._close, width=140).pack(side="left", padx=8)
        primary_button(button_row, "Reset", self._save, width=160, icon="⚷").pack(side="left", padx=8)

    def _save(self) -> None:
        actor = self._app.principal.audit_context()
        result = self._app.container.users.reset_password(actor, self._user_id, self.password.entry.get())
        if result.success:
            self._app.notify(result.message, "success")
            self._on_done()
            self._close()
            return
        self.message.configure(text=result.message)

    def _close(self) -> None:
        self.grab_release()
        self.destroy()
