from __future__ import annotations

import customtkinter as ctk

COLOR_BG = "#0B1020"
COLOR_BG_GRADIENT_TOP = "#101935"
COLOR_BG_GRADIENT_BOTTOM = "#070A16"
COLOR_SURFACE = "#141C32"
COLOR_SURFACE_ALT = "#1B2541"
COLOR_GLASS = "#18213C"
COLOR_GLASS_BORDER = "#2A3658"
COLOR_SIDEBAR = "#0D1428"
COLOR_PRIMARY = "#2D6CDF"
COLOR_PRIMARY_HOVER = "#3B7BF0"
COLOR_PRIMARY_DEEP = "#1B4DB1"
COLOR_ACCENT = "#4F8DFD"
COLOR_TEXT = "#EAF0FF"
COLOR_TEXT_MUTED = "#8A94AD"
COLOR_TEXT_FAINT = "#5B6480"
COLOR_INPUT_BG = "#0F1730"
COLOR_INPUT_BORDER = "#2A3658"
COLOR_SUCCESS = "#2EBD7E"
COLOR_WARNING = "#E0A82E"
COLOR_DANGER = "#E0563B"
COLOR_INFO = "#4F8DFD"
COLOR_DIVIDER = "#222C49"

SEVERITY_COLORS = {
    "Critical": "#C0182B",
    "High": "#E0561B",
    "Medium": "#C9911C",
    "Low": "#2E8B57",
    "Informational": "#2D6CDF",
}

BUSINESS_IMPACT_COLORS = {
    "Critical": "#C0182B",
    "High": "#E0561B",
    "Medium": "#C9911C",
    "Low": "#2E8B57",
}

STATUS_COLORS = {
    "SUCCESS": "#2EBD7E",
    "FAILED": "#E0563B",
    "LOCKED": "#E0A82E",
}

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"


def font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono_font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size, weight=weight)


def apply_appearance(theme: str) -> None:
    ctk.set_appearance_mode("dark" if theme == "dark" else "light")
    ctk.set_default_color_theme("blue")
