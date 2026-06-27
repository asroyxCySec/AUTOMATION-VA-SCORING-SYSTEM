from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk

from app import config
from app.services.auth_service import AuthResult
from app.ui import theme
from app.ui.components import FormField, Toast, primary_button


class LoginView(ctk.CTkFrame):
    def __init__(self, master, container, on_success: Callable[[AuthResult], None]) -> None:
        super().__init__(master, fg_color=theme.COLOR_BG)
        self._container = container
        self._on_success = on_success
        self._busy = False

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        brand = ctk.CTkFrame(wrapper, fg_color="transparent")
        brand.pack(pady=(0, 18))
        ctk.CTkLabel(
            brand, text=" V ", font=theme.font(30, "bold"), text_color="#FFFFFF",
            fg_color=theme.COLOR_PRIMARY, corner_radius=16, width=64, height=64,
        ).pack()
        ctk.CTkLabel(brand, text=config.APP_NAME, font=theme.font(26, "bold"), text_color=theme.COLOR_TEXT).pack(pady=(12, 0))
        ctk.CTkLabel(
            brand, text="Automatic Vulnerability Assessment Scoring", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
        ).pack(pady=(2, 0))

        card = ctk.CTkFrame(
            wrapper, fg_color=theme.COLOR_GLASS, corner_radius=22, border_width=1, border_color=theme.COLOR_GLASS_BORDER
        )
        card.pack()
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=42, pady=38)

        ctk.CTkLabel(inner, text="Masuk ke Akun Anda", font=theme.font(18, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", pady=(0, 4)
        )
        ctk.CTkLabel(
            inner, text="Gunakan kredensial yang telah terdaftar.", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", pady=(0, 22))

        self.username_field = FormField(inner, "Username", placeholder="Masukkan username", width=320)
        self.username_field.pack(fill="x", pady=(0, 14))
        self.password_field = FormField(inner, "Password", placeholder="Masukkan password", show="•", width=320)
        self.password_field.pack(fill="x", pady=(0, 8))

        self.message_label = ctk.CTkLabel(inner, text="", font=theme.font(12), text_color=theme.COLOR_DANGER, wraplength=320)
        self.message_label.pack(anchor="w", pady=(2, 8))

        self.login_button = primary_button(inner, "Masuk", self._submit, width=320, icon="→")
        self.login_button.pack(fill="x", pady=(6, 0))

        hint = ctk.CTkFrame(inner, fg_color=theme.COLOR_SURFACE, corner_radius=10)
        hint.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(
            hint,
            text="Default admin: admin / admin123 (wajib ganti saat pertama login).",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED, wraplength=300, justify="left",
        ).pack(padx=12, pady=10)

        self.password_field.entry.bind("<Return>", lambda _event: self._submit())
        self.username_field.entry.bind("<Return>", lambda _event: self.password_field.entry.focus_set())
        self.after(120, self.username_field.entry.focus_set)

    def _set_message(self, text: str, color: str) -> None:
        self.message_label.configure(text=text, text_color=color)

    def _submit(self) -> None:
        if self._busy:
            return
        username = self.username_field.get()
        password = self.password_field.entry.get()
        if not username or not password:
            self._set_message("Username dan password wajib diisi.", theme.COLOR_DANGER)
            return
        self._busy = True
        self.login_button.configure(state="disabled", text="Memverifikasi...")
        self._set_message("", theme.COLOR_DANGER)

        def worker() -> None:
            result = self._container.auth.authenticate(username, password)
            self.after(0, lambda: self._finish(result))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, result: AuthResult) -> None:
        self._busy = False
        self.login_button.configure(state="normal", text="→  Masuk")
        if result.success:
            self._on_success(result)
            return
        color = theme.COLOR_WARNING if result.locked else theme.COLOR_DANGER
        self._set_message(result.message, color)
        toast = Toast(self, result.message, "warning" if result.locked else "error")
        toast.place(relx=0.5, rely=0.93, anchor="center")
        self.after(3200, toast.destroy)
