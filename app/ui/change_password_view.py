from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk

from app.ui import theme
from app.ui.components import FormField, Toast, primary_button


class ChangePasswordView(ctk.CTkFrame):
    def __init__(self, master, container, principal, on_done: Callable[[], None], forced: bool = True) -> None:
        super().__init__(master, fg_color=theme.COLOR_BG)
        self._container = container
        self._principal = principal
        self._on_done = on_done
        self._busy = False

        card = ctk.CTkFrame(
            self, fg_color=theme.COLOR_GLASS, corner_radius=22, border_width=1, border_color=theme.COLOR_GLASS_BORDER
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=40)

        ctk.CTkLabel(
            inner, text=" ⚷ ", font=theme.font(24, "bold"), text_color="#FFFFFF",
            fg_color=theme.COLOR_PRIMARY, corner_radius=14, width=54, height=54,
        ).pack(pady=(0, 14))
        title = "Ganti Password Wajib" if forced else "Ganti Password"
        ctk.CTkLabel(inner, text=title, font=theme.font(20, "bold"), text_color=theme.COLOR_TEXT).pack()
        subtitle = (
            "Demi keamanan, Anda wajib mengganti password default sebelum melanjutkan."
            if forced
            else "Perbarui password akun Anda."
        )
        ctk.CTkLabel(
            inner, text=subtitle, font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED, wraplength=340, justify="center"
        ).pack(pady=(6, 22))

        self.current_field = FormField(inner, "Password Saat Ini", show="•", width=340)
        self.current_field.pack(fill="x", pady=(0, 12))
        self.new_field = FormField(inner, "Password Baru", show="•", width=340)
        self.new_field.pack(fill="x", pady=(0, 12))
        self.confirm_field = FormField(inner, "Konfirmasi Password Baru", show="•", width=340)
        self.confirm_field.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text="Minimal 8 karakter, mengandung huruf besar, huruf kecil, dan angka.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED, wraplength=340, justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.message_label = ctk.CTkLabel(inner, text="", font=theme.font(12), text_color=theme.COLOR_DANGER, wraplength=340)
        self.message_label.pack(anchor="w", pady=(0, 8))

        self.submit_button = primary_button(inner, "Simpan Password", self._submit, width=340, icon="✓")
        self.submit_button.pack(fill="x")

    def _submit(self) -> None:
        if self._busy:
            return
        current = self.current_field.entry.get()
        new_password = self.new_field.entry.get()
        confirm = self.confirm_field.entry.get()
        if not current or not new_password or not confirm:
            self.message_label.configure(text="Semua kolom wajib diisi.", text_color=theme.COLOR_DANGER)
            return
        self._busy = True
        self.submit_button.configure(state="disabled", text="Menyimpan...")

        def worker() -> None:
            result = self._container.auth.change_password(self._principal.id, current, new_password, confirm)
            self.after(0, lambda: self._finish(result))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, result) -> None:
        self._busy = False
        self.submit_button.configure(state="normal", text="✓  Simpan Password")
        if result.success:
            toast = Toast(self, "Password berhasil diperbarui.", "success")
            toast.place(relx=0.5, rely=0.92, anchor="center")
            self.after(900, self._on_done)
            return
        self.message_label.configure(text=result.message, text_color=theme.COLOR_DANGER)
