from __future__ import annotations

import os
import shutil

import customtkinter as ctk

from app import config
from app.ui import theme
from app.ui.components import (
    Card,
    ConfirmDialog,
    FormField,
    FormSelect,
    LabeledTextbox,
    SectionTitle,
    build_treeview,
    ghost_button,
    primary_button,
    style_treeview,
)
from app.utils.helpers import format_datetime

_THEMES = {"Gelap": "dark", "Terang": "light"}
_LANGUAGES = {"Indonesia": "id", "English": "en"}


def _reverse(mapping: dict, value: str) -> str:
    for label, mapped in mapping.items():
        if mapped == value:
            return label
    return next(iter(mapping))


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._settings = app.container.settings.load()
        self._logo_path = self._settings.report_logo_path

        SectionTitle(self, "Pengaturan", "Konfigurasi identitas instansi, tampilan, dan basis data.").pack(
            anchor="w", pady=(4, 16)
        )

        identity = Card(self)
        identity.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(identity, text="Identitas Instansi", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(18, 12)
        )
        grid = ctk.CTkFrame(identity, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 10))
        grid.grid_columnconfigure(0, weight=1, uniform="id")
        grid.grid_columnconfigure(1, weight=1, uniform="id")
        self.name_field = FormField(grid, "Nama Instansi")
        self.name_field.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.email_field = FormField(grid, "Email Instansi")
        self.email_field.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.phone_field = FormField(grid, "Telepon")
        self.phone_field.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.header_field = FormField(grid, "Judul Header Laporan")
        self.header_field.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.address_box = LabeledTextbox(identity, "Alamat Instansi", height=60)
        self.address_box.pack(fill="x", padx=20, pady=(0, 8))
        self.footer_box = LabeledTextbox(identity, "Footer Laporan", height=60)
        self.footer_box.pack(fill="x", padx=20, pady=(0, 8))

        logo_row = ctk.CTkFrame(identity, fg_color="transparent")
        logo_row.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkLabel(logo_row, text="Logo Laporan", font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED).pack(
            anchor="w", pady=(0, 4)
        )
        picker = ctk.CTkFrame(logo_row, fg_color="transparent")
        picker.pack(fill="x")
        self.logo_label = ctk.CTkLabel(
            picker, text=os.path.basename(self._logo_path) if self._logo_path else "Belum ada logo",
            font=theme.font(12), text_color=theme.COLOR_TEXT if self._logo_path else theme.COLOR_TEXT_MUTED,
            fg_color=theme.COLOR_INPUT_BG, corner_radius=10, height=40, anchor="w",
        )
        self.logo_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_button(picker, "Pilih Logo", self._pick_logo, width=130, icon="🖼").pack(side="left", padx=(0, 8))
        ghost_button(picker, "Hapus", self._clear_logo, width=90).pack(side="left")

        appearance = Card(self)
        appearance.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(appearance, text="Tampilan & Bahasa", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(18, 12)
        )
        appearance_grid = ctk.CTkFrame(appearance, fg_color="transparent")
        appearance_grid.pack(fill="x", padx=20, pady=(0, 18))
        appearance_grid.grid_columnconfigure(0, weight=1, uniform="ap")
        appearance_grid.grid_columnconfigure(1, weight=1, uniform="ap")
        self.theme_select = FormSelect(
            appearance_grid, "Tema Aplikasi", list(_THEMES), default=_reverse(_THEMES, self._settings.app_theme)
        )
        self.theme_select.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.language_select = FormSelect(
            appearance_grid, "Bahasa", list(_LANGUAGES), default=_reverse(_LANGUAGES, self._settings.app_language)
        )
        self.language_select.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)

        primary_button(self, "Simpan Pengaturan", self._save, width=220, icon="✓").pack(anchor="w", pady=(0, 18))

        backup = Card(self)
        backup.pack(fill="x", pady=(0, 24))
        ctk.CTkLabel(backup, text="Backup & Restore Basis Data", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(18, 4)
        )
        ctk.CTkLabel(
            backup, text="Buat salinan basis data atau pulihkan dari berkas backup.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=20, pady=(0, 12))
        backup_actions = ctk.CTkFrame(backup, fg_color="transparent")
        backup_actions.pack(fill="x", padx=20, pady=(0, 12))
        primary_button(backup_actions, "Buat Backup", self._create_backup, width=180, icon="💾").pack(side="left", padx=(0, 10))
        ghost_button(backup_actions, "Restore dari Berkas", self._restore_backup, width=200, icon="⟲").pack(side="left")

        style_treeview(self.winfo_toplevel())
        self.backup_tree = build_treeview(
            backup,
            [
                ("time", "Waktu", 170),
                ("action", "Aksi", 120),
                ("size", "Ukuran", 120),
                ("path", "Berkas", 360),
            ],
            height=6,
        )

        self._load_settings_into_fields()
        self._reload_backups()

    def _load_settings_into_fields(self) -> None:
        self.name_field.set(self._settings.institution_name)
        self.email_field.set(self._settings.institution_email)
        self.phone_field.set(self._settings.institution_phone)
        self.header_field.set(self._settings.report_header)
        self.address_box.set(self._settings.institution_address)
        self.footer_box.set(self._settings.report_footer)

    def _pick_logo(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="Pilih logo laporan", filetypes=[("Gambar", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not path:
            return
        config.ensure_directories()
        extension = os.path.splitext(path)[1].lower() or ".png"
        destination = os.path.join(str(config.UPLOAD_DIR), f"report_logo{extension}")
        try:
            shutil.copy2(path, destination)
        except OSError as error:
            self._app.notify(f"Gagal menyalin logo: {error}", "error")
            return
        self._logo_path = destination
        self.logo_label.configure(text=os.path.basename(destination), text_color=theme.COLOR_TEXT)

    def _clear_logo(self) -> None:
        self._logo_path = ""
        self.logo_label.configure(text="Belum ada logo", text_color=theme.COLOR_TEXT_MUTED)

    def _save(self) -> None:
        actor = self._app.principal.audit_context()
        new_theme = _THEMES[self.theme_select.get()]
        values = {
            "institution_name": self.name_field.get(),
            "institution_email": self.email_field.get(),
            "institution_phone": self.phone_field.get(),
            "institution_address": self.address_box.get(),
            "report_header": self.header_field.get() or "VULNERABILITY ASSESSMENT REPORT",
            "report_footer": self.footer_box.get(),
            "report_logo_path": self._logo_path,
            "app_theme": new_theme,
            "app_language": _LANGUAGES[self.language_select.get()],
        }
        self._app.container.settings.save(actor, values)
        self._settings = self._app.container.settings.load()
        self._app.apply_theme(new_theme)
        self._app.notify("Pengaturan berhasil disimpan.", "success")

    def _create_backup(self) -> None:
        actor = self._app.principal.audit_context()
        result = self._app.container.backups.create_backup(actor)
        self._app.notify(result.message, "success" if result.success else "error")
        self._reload_backups()

    def _restore_backup(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Pilih berkas backup", filetypes=[("Database", "*.db"), ("Semua", "*.*")])
        if not path:
            return

        def confirm() -> None:
            actor = self._app.principal.audit_context()
            result = self._app.container.backups.restore_backup(actor, path)
            self._app.notify(result.message, "success" if result.success else "error")
            self._reload_backups()

        ConfirmDialog(
            self, "Restore Basis Data",
            "Memulihkan basis data akan menimpa data saat ini. Lanjutkan?",
            confirm, danger=True,
        )

    def _reload_backups(self) -> None:
        self.backup_tree.delete(*self.backup_tree.get_children())
        for row in self._app.container.backups.history():
            size_kb = f"{row.size_bytes / 1024:.1f} KB"
            self.backup_tree.insert(
                "", "end",
                values=(format_datetime(row.created_at), row.action, size_kb, row.file_path),
            )
