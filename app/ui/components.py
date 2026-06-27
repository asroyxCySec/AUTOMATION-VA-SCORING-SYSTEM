from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

import customtkinter as ctk

from app.ui import theme


class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=kwargs.pop("fg_color", theme.COLOR_GLASS),
            corner_radius=kwargs.pop("corner_radius", 16),
            border_width=kwargs.pop("border_width", 1),
            border_color=kwargs.pop("border_color", theme.COLOR_GLASS_BORDER),
            **kwargs,
        )


class SectionTitle(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "", icon: str = "") -> None:
        super().__init__(master, fg_color="transparent")
        text = f"{icon}  {title}" if icon else title
        ctk.CTkLabel(
            self, text=text, font=theme.font(18, "bold"), text_color=theme.COLOR_TEXT, anchor="w"
        ).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle, font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
            ).pack(anchor="w", pady=(2, 0))


class FormField(ctk.CTkFrame):
    def __init__(
        self,
        master,
        label: str,
        placeholder: str = "",
        show: str = "",
        width: int = 260,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=label, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            show=show,
            width=width,
            height=40,
            corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG,
            border_color=theme.COLOR_INPUT_BORDER,
            text_color=theme.COLOR_TEXT,
            font=theme.font(13),
        )
        self.entry.pack(fill="x")

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def configure_state(self, state: str) -> None:
        self.entry.configure(state=state)


class FormSelect(ctk.CTkFrame):
    def __init__(self, master, label: str, values: list[str], default: str = "", width: int = 260) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=label, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        self.variable = ctk.StringVar(value=default or (values[0] if values else ""))
        self.menu = ctk.CTkOptionMenu(
            self,
            values=values,
            variable=self.variable,
            width=width,
            height=40,
            corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG,
            button_color=theme.COLOR_PRIMARY_DEEP,
            button_hover_color=theme.COLOR_PRIMARY,
            text_color=theme.COLOR_TEXT,
            dropdown_fg_color=theme.COLOR_SURFACE_ALT,
            dropdown_text_color=theme.COLOR_TEXT,
            dropdown_hover_color=theme.COLOR_PRIMARY_DEEP,
            font=theme.font(13),
        )
        self.menu.pack(fill="x")

    def get(self) -> str:
        return self.variable.get()

    def set(self, value: str) -> None:
        self.variable.set(value)


class LabeledTextbox(ctk.CTkFrame):
    def __init__(self, master, label: str, height: int = 90, width: int = 260) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=label, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        self.box = ctk.CTkTextbox(
            self,
            height=height,
            width=width,
            corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG,
            border_color=theme.COLOR_INPUT_BORDER,
            border_width=2,
            text_color=theme.COLOR_TEXT,
            font=theme.font(13),
        )
        self.box.pack(fill="x")

    def get(self) -> str:
        return self.box.get("1.0", "end").strip()

    def set(self, value: str) -> None:
        self.box.delete("1.0", "end")
        self.box.insert("1.0", value)


class Badge(ctk.CTkLabel):
    def __init__(self, master, text: str, color: str, text_color: str = "#FFFFFF") -> None:
        super().__init__(
            master,
            text=f"  {text}  ",
            font=theme.font(12, "bold"),
            fg_color=color,
            text_color=text_color,
            corner_radius=8,
            height=28,
        )


class StatCard(Card):
    def __init__(self, master, title: str, value: str, accent: str, icon: str = "") -> None:
        super().__init__(master, corner_radius=14)
        self.grid_columnconfigure(0, weight=1)
        bar = ctk.CTkFrame(self, fg_color=accent, width=6, corner_radius=3)
        bar.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 0), pady=14)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=16, pady=14)
        header = f"{icon}  {title}" if icon else title
        ctk.CTkLabel(
            container, text=header, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w")
        self.value_label = ctk.CTkLabel(
            container, text=value, font=theme.font(26, "bold"), text_color=theme.COLOR_TEXT, anchor="w"
        )
        self.value_label.pack(anchor="w", pady=(4, 0))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)


class DistributionRow(ctk.CTkFrame):
    def __init__(self, master, label: str, value: int, total: int, color: str) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            self, text=label, font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT, width=110, anchor="w"
        ).grid(row=0, column=0, sticky="w")
        progress = ctk.CTkProgressBar(
            self, height=12, corner_radius=6, progress_color=color, fg_color=theme.COLOR_SURFACE_ALT
        )
        ratio = (value / total) if total else 0.0
        progress.set(ratio)
        progress.grid(row=0, column=1, sticky="ew", padx=10)
        ctk.CTkLabel(
            self, text=str(value), font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, width=36, anchor="e"
        ).grid(row=0, column=2, sticky="e")


class Toast(ctk.CTkFrame):
    def __init__(self, master, message: str, kind: str = "success") -> None:
        color = {
            "success": theme.COLOR_SUCCESS,
            "error": theme.COLOR_DANGER,
            "info": theme.COLOR_INFO,
            "warning": theme.COLOR_WARNING,
        }.get(kind, theme.COLOR_INFO)
        icon = {"success": "✓", "error": "✕", "info": "i", "warning": "!"}.get(kind, "i")
        super().__init__(
            master, fg_color=theme.COLOR_SURFACE_ALT, corner_radius=12, border_width=1, border_color=color
        )
        dot = ctk.CTkLabel(
            self, text=f" {icon} ", font=theme.font(14, "bold"), text_color="#FFFFFF", fg_color=color, corner_radius=8
        )
        dot.pack(side="left", padx=(10, 8), pady=10)
        ctk.CTkLabel(
            self, text=message, font=theme.font(13), text_color=theme.COLOR_TEXT, wraplength=320, justify="left"
        ).pack(side="left", padx=(0, 14), pady=10)


class LoadingOverlay(ctk.CTkFrame):
    def __init__(self, master, message: str = "Memproses...") -> None:
        super().__init__(master, fg_color=theme.COLOR_BG, corner_radius=0)
        center = ctk.CTkFrame(self, fg_color=theme.COLOR_GLASS, corner_radius=18, border_width=1, border_color=theme.COLOR_GLASS_BORDER)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self.bar = ctk.CTkProgressBar(
            center, width=220, height=10, corner_radius=5, mode="indeterminate", progress_color=theme.COLOR_PRIMARY
        )
        self.bar.pack(padx=36, pady=(32, 14))
        ctk.CTkLabel(center, text=message, font=theme.font(14, "bold"), text_color=theme.COLOR_TEXT).pack(
            padx=36, pady=(0, 32)
        )

    def start(self) -> None:
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bar.start()
        self.lift()

    def stop(self) -> None:
        self.bar.stop()
        self.place_forget()


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, on_confirm: Callable[[], None], danger: bool = False) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)
        self.grab_set()
        accent = theme.COLOR_DANGER if danger else theme.COLOR_PRIMARY
        ctk.CTkLabel(self, text=title, font=theme.font(17, "bold"), text_color=theme.COLOR_TEXT).pack(pady=(26, 8))
        ctk.CTkLabel(
            self, text=message, font=theme.font(13), text_color=theme.COLOR_TEXT_MUTED, wraplength=360, justify="center"
        ).pack(padx=24, pady=(0, 18))
        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(4, 20))
        ctk.CTkButton(
            button_row, text="Batal", width=140, height=40, corner_radius=10,
            fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_DIVIDER, text_color=theme.COLOR_TEXT,
            font=theme.font(13, "bold"), command=self._cancel,
        ).pack(side="left", padx=8)

        def _confirm() -> None:
            self._close()
            on_confirm()

        ctk.CTkButton(
            button_row, text="Konfirmasi", width=140, height=40, corner_radius=10,
            fg_color=accent, hover_color=theme.COLOR_PRIMARY_HOVER, text_color="#FFFFFF",
            font=theme.font(13, "bold"), command=_confirm,
        ).pack(side="left", padx=8)
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _cancel(self) -> None:
        self._close()

    def _close(self) -> None:
        self.grab_release()
        self.destroy()


class Pagination(ctk.CTkFrame):
    def __init__(self, master, on_change: Callable[[int], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_change = on_change
        self._page = 1
        self._total_pages = 1
        self.prev_button = ctk.CTkButton(
            self, text="‹ Sebelumnya", width=120, height=34, corner_radius=8,
            fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_DIVIDER, text_color=theme.COLOR_TEXT,
            font=theme.font(12, "bold"), command=self._prev,
        )
        self.prev_button.pack(side="left", padx=4)
        self.label = ctk.CTkLabel(self, text="1 / 1", font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, width=80)
        self.label.pack(side="left", padx=8)
        self.next_button = ctk.CTkButton(
            self, text="Berikutnya ›", width=120, height=34, corner_radius=8,
            fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_DIVIDER, text_color=theme.COLOR_TEXT,
            font=theme.font(12, "bold"), command=self._next,
        )
        self.next_button.pack(side="left", padx=4)

    def update_state(self, page: int, total_pages: int) -> None:
        self._page = page
        self._total_pages = max(total_pages, 1)
        self.label.configure(text=f"{self._page} / {self._total_pages}")
        self.prev_button.configure(state="normal" if self._page > 1 else "disabled")
        self.next_button.configure(state="normal" if self._page < self._total_pages else "disabled")

    def _prev(self) -> None:
        if self._page > 1:
            self._on_change(self._page - 1)

    def _next(self) -> None:
        if self._page < self._total_pages:
            self._on_change(self._page + 1)


def primary_button(master, text: str, command: Callable[[], None], width: int = 200, icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(
        master, text=label, command=command, width=width, height=44, corner_radius=12,
        fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER, text_color="#FFFFFF",
        font=theme.font(14, "bold"),
    )


def ghost_button(master, text: str, command: Callable[[], None], width: int = 160, icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(
        master, text=label, command=command, width=width, height=42, corner_radius=12,
        fg_color=theme.COLOR_SURFACE_ALT, hover_color=theme.COLOR_DIVIDER, text_color=theme.COLOR_TEXT,
        border_width=1, border_color=theme.COLOR_GLASS_BORDER, font=theme.font(13, "bold"),
    )


def danger_button(master, text: str, command: Callable[[], None], width: int = 160, icon: str = "") -> ctk.CTkButton:
    label = f"{icon}  {text}" if icon else text
    return ctk.CTkButton(
        master, text=label, command=command, width=width, height=42, corner_radius=12,
        fg_color=theme.COLOR_DANGER, hover_color="#F06A4E", text_color="#FFFFFF", font=theme.font(13, "bold"),
    )


def style_treeview(widget_root: tk.Misc) -> ttk.Style:
    style = ttk.Style(widget_root)
    style.theme_use("clam")
    style.configure(
        "VulnScore.Treeview",
        background=theme.COLOR_SURFACE,
        foreground=theme.COLOR_TEXT,
        fieldbackground=theme.COLOR_SURFACE,
        rowheight=38,
        borderwidth=0,
        font=(theme.FONT_FAMILY, 10),
    )
    style.configure(
        "VulnScore.Treeview.Heading",
        background=theme.COLOR_SIDEBAR,
        foreground=theme.COLOR_TEXT,
        relief="flat",
        font=(theme.FONT_FAMILY, 10, "bold"),
        padding=(8, 8),
    )
    style.map(
        "VulnScore.Treeview",
        background=[("selected", theme.COLOR_PRIMARY_DEEP)],
        foreground=[("selected", "#FFFFFF")],
    )
    style.map("VulnScore.Treeview.Heading", background=[("active", theme.COLOR_SURFACE_ALT)])
    return style


def build_treeview(master, columns: list[tuple[str, str, int]], height: int = 12) -> ttk.Treeview:
    frame = ctk.CTkFrame(master, fg_color=theme.COLOR_SURFACE, corner_radius=12)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(
        frame,
        columns=[c[0] for c in columns],
        show="headings",
        style="VulnScore.Treeview",
        height=height,
    )
    for key, title, width in columns:
        tree.heading(key, text=title)
        tree.column(key, width=width, anchor="w", stretch=True)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)
    return tree
