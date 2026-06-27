from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app import config
from app.ui import theme


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, principal, on_navigate: Callable[[str], None], on_logout: Callable[[], None]) -> None:
        super().__init__(master, fg_color=theme.COLOR_SIDEBAR, corner_radius=0, width=248)
        self.grid_propagate(False)
        self._on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active: str | None = None

        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(26, 8))
        logo = ctk.CTkLabel(
            brand, text=" V ", font=theme.font(22, "bold"), text_color="#FFFFFF",
            fg_color=theme.COLOR_PRIMARY, corner_radius=12, width=44, height=44,
        )
        logo.pack(side="left")
        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left", padx=10)
        ctk.CTkLabel(brand_text, text=config.APP_NAME, font=theme.font(18, "bold"), text_color=theme.COLOR_TEXT).pack(anchor="w")
        ctk.CTkLabel(
            brand_text, text=f"v{config.APP_VERSION}", font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w")

        ctk.CTkFrame(self, height=1, fg_color=theme.COLOR_DIVIDER).pack(fill="x", padx=18, pady=(8, 12))

        nav_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        nav_container.pack(fill="both", expand=True, padx=10)

        items = self._items_for(principal)
        for key, label, icon in items:
            button = ctk.CTkButton(
                nav_container,
                text=f"   {icon}    {label}",
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color="transparent",
                hover_color=theme.COLOR_SURFACE_ALT,
                text_color=theme.COLOR_TEXT_MUTED,
                font=theme.font(13, "bold"),
                command=lambda k=key: self._on_navigate(k),
            )
            button.pack(fill="x", pady=3)
            self._buttons[key] = button

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=14, pady=14)
        user_card = ctk.CTkFrame(footer, fg_color=theme.COLOR_SURFACE, corner_radius=12)
        user_card.pack(fill="x", pady=(0, 10))
        initials = (principal.full_name[:1] or principal.username[:1]).upper()
        ctk.CTkLabel(
            user_card, text=initials, font=theme.font(16, "bold"), text_color="#FFFFFF",
            fg_color=theme.COLOR_PRIMARY_DEEP, corner_radius=10, width=40, height=40,
        ).pack(side="left", padx=10, pady=10)
        info = ctk.CTkFrame(user_card, fg_color="transparent")
        info.pack(side="left", padx=(0, 8), pady=10, fill="x", expand=True)
        ctk.CTkLabel(
            info, text=principal.full_name, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT, anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=principal.role_name, font=theme.font(11), text_color=theme.COLOR_ACCENT, anchor="w"
        ).pack(anchor="w")
        ctk.CTkButton(
            footer, text="   ⏻    Logout", anchor="w", height=42, corner_radius=10,
            fg_color="transparent", hover_color=theme.COLOR_DANGER, text_color=theme.COLOR_TEXT_MUTED,
            font=theme.font(13, "bold"), command=on_logout,
        ).pack(fill="x")

    @staticmethod
    def _items_for(principal) -> list[tuple[str, str, str]]:
        items = [
            ("dashboard", "Dashboard", "▤"),
            ("assessment", "Penilaian Baru", "＋"),
            ("assessments", "Daftar Penilaian", "☰"),
        ]
        if principal.is_administrator:
            items.append(("users", "Manajemen User", "♟"))
            items.append(("audit", "Audit Log", "❑"))
            items.append(("settings", "Pengaturan", "⚙"))
        items.append(("profile", "Profil", "◉"))
        return items

    def set_active(self, key: str) -> None:
        if self._active and self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED
            )
        if key in self._buttons:
            self._buttons[key].configure(fg_color=theme.COLOR_PRIMARY, text_color="#FFFFFF")
            self._active = key
