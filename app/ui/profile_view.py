from __future__ import annotations

import os
import shutil

import customtkinter as ctk

from app import config
from app.ui import theme
from app.ui.components import Card, FormField, SectionTitle, ghost_button, primary_button
from app.utils.helpers import format_datetime


class ProfileView(ctk.CTkScrollableFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._row = app.container.users.get_row(app.principal.id)

        SectionTitle(self, "Profil Saya", "Perbarui informasi akun dan keamanan Anda.").pack(anchor="w", pady=(4, 16))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        top.grid_columnconfigure(0, weight=1, uniform="profile")
        top.grid_columnconfigure(1, weight=2, uniform="profile")

        identity = Card(top)
        identity.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        avatar_holder = ctk.CTkFrame(identity, fg_color="transparent")
        avatar_holder.pack(pady=(26, 8))
        initials = (self._row.full_name[:1] or self._row.username[:1]).upper() if self._row else "?"
        self.avatar = ctk.CTkLabel(
            avatar_holder, text=initials, font=theme.font(34, "bold"), text_color="#FFFFFF",
            fg_color=theme.COLOR_PRIMARY_DEEP, corner_radius=50, width=96, height=96,
        )
        self.avatar.pack()
        ctk.CTkLabel(
            identity, text=self._row.full_name if self._row else "", font=theme.font(16, "bold"), text_color=theme.COLOR_TEXT
        ).pack(pady=(10, 0))
        ctk.CTkLabel(
            identity, text=f"@{self._row.username}" if self._row else "", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
        ).pack()
        ctk.CTkLabel(
            identity, text=app.principal.role_name, font=theme.font(12, "bold"), text_color=theme.COLOR_ACCENT
        ).pack(pady=(4, 8))
        ghost_button(identity, "Unggah Foto", self._upload_photo, width=160, icon="📷").pack(pady=(2, 8))
        meta = ctk.CTkFrame(identity, fg_color="transparent")
        meta.pack(fill="x", padx=20, pady=(6, 22))
        created = format_datetime(self._row.created_at) if self._row else "-"
        last = format_datetime(self._row.last_login_at) if self._row and self._row.last_login_at else "-"
        self._meta_line(meta, "Bergabung", created)
        self._meta_line(meta, "Login Terakhir", last)

        edit_card = Card(top)
        edit_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(edit_card, text="Informasi Akun", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(18, 12)
        )
        grid = ctk.CTkFrame(edit_card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 12))
        grid.grid_columnconfigure(0, weight=1, uniform="edit")
        grid.grid_columnconfigure(1, weight=1, uniform="edit")
        self.full_name = FormField(grid, "Nama Lengkap")
        self.full_name.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.email = FormField(grid, "Email")
        self.email.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.phone = FormField(grid, "Nomor HP")
        self.phone.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.instansi = FormField(grid, "Instansi")
        self.instansi.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.jabatan = FormField(grid, "Jabatan")
        self.jabatan.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=8)
        if self._row:
            self.full_name.set(self._row.full_name or "")
            self.email.set(self._row.email or "")
            self.phone.set(self._row.phone or "")
            self.instansi.set(self._row.instansi or "")
            self.jabatan.set(self._row.jabatan or "")
        primary_button(edit_card, "Simpan Perubahan", self._save_profile, width=200, icon="✓").pack(anchor="w", padx=20, pady=(6, 20))

        password_card = Card(self)
        password_card.pack(fill="x", pady=(16, 24))
        ctk.CTkLabel(password_card, text="Ubah Password", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(18, 4)
        )
        ctk.CTkLabel(
            password_card, text="Minimal 8 karakter dengan huruf besar, huruf kecil, dan angka.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))
        pwd_grid = ctk.CTkFrame(password_card, fg_color="transparent")
        pwd_grid.pack(fill="x", padx=20, pady=(0, 8))
        for column in range(3):
            pwd_grid.grid_columnconfigure(column, weight=1, uniform="pwd")
        self.current_pwd = FormField(pwd_grid, "Password Saat Ini", show="•")
        self.current_pwd.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        self.new_pwd = FormField(pwd_grid, "Password Baru", show="•")
        self.new_pwd.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        self.confirm_pwd = FormField(pwd_grid, "Konfirmasi", show="•")
        self.confirm_pwd.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=4)
        primary_button(password_card, "Perbarui Password", self._change_password, width=200, icon="⚷").pack(
            anchor="w", padx=20, pady=(10, 20)
        )

    def _meta_line(self, master, label: str, value: str) -> None:
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(row, text=label, font=theme.font(11, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=value, font=theme.font(11), text_color=theme.COLOR_TEXT, anchor="e").pack(side="right")

    def _upload_photo(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="Pilih foto profil", filetypes=[("Gambar", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not path:
            return
        config.ensure_directories()
        extension = os.path.splitext(path)[1].lower() or ".png"
        destination = os.path.join(str(config.UPLOAD_DIR), f"profile_{self._app.principal.id}{extension}")
        try:
            shutil.copy2(path, destination)
        except OSError as error:
            self._app.notify(f"Gagal menyalin foto: {error}", "error")
            return
        actor = self._app.principal.audit_context()
        result = self._app.container.users.set_photo(actor, self._app.principal.id, destination)
        self._app.notify(result.message, "success" if result.success else "error")

    def _save_profile(self) -> None:
        actor = self._app.principal.audit_context()
        result = self._app.container.users.update_profile(
            actor,
            self._app.principal.id,
            self.full_name.get(),
            self.email.get(),
            self.phone.get(),
            self.instansi.get(),
            self.jabatan.get(),
        )
        self._app.notify(result.message, "success" if result.success else "error")

    def _change_password(self) -> None:
        result = self._app.container.auth.change_password(
            self._app.principal.id,
            self.current_pwd.entry.get(),
            self.new_pwd.entry.get(),
            self.confirm_pwd.entry.get(),
        )
        if result.success:
            self.current_pwd.set("")
            self.new_pwd.set("")
            self.confirm_pwd.set("")
        self._app.notify(result.message, "success" if result.success else "error")
