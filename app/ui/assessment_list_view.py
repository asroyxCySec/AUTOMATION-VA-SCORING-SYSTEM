from __future__ import annotations

import threading

import customtkinter as ctk

from app.ui import theme
from app.ui.components import (
    ConfirmDialog,
    Pagination,
    SectionTitle,
    build_treeview,
    danger_button,
    ghost_button,
    primary_button,
    style_treeview,
)

_PAGE_SIZE = 10
_SEVERITIES = ("Semua", "Critical", "High", "Medium", "Low", "Informational")


class AssessmentListView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._page = 1
        self._total_pages = 1
        self._search = ""
        self._severity_filter = None
        self._row_ids: dict[str, int] = {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(4, 14))
        SectionTitle(header, "Daftar Penilaian", "Kelola, tinjau, dan ekspor laporan penilaian.").pack(side="left", anchor="w")
        primary_button(header, "Penilaian Baru", lambda: app.navigate("assessment"), width=180, icon="＋").pack(side="right")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 12))
        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Cari target atau nama temuan...", width=320, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, border_color=theme.COLOR_INPUT_BORDER, text_color=theme.COLOR_TEXT,
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<Return>", lambda _e: self._apply_search())
        ghost_button(toolbar, "Cari", self._apply_search, width=100, icon="🔍").pack(side="left", padx=10)
        self.severity_menu = ctk.CTkOptionMenu(
            toolbar, values=list(_SEVERITIES), width=160, height=40, corner_radius=10,
            fg_color=theme.COLOR_INPUT_BG, button_color=theme.COLOR_PRIMARY_DEEP, button_hover_color=theme.COLOR_PRIMARY,
            text_color=theme.COLOR_TEXT, dropdown_fg_color=theme.COLOR_SURFACE_ALT, dropdown_text_color=theme.COLOR_TEXT,
            command=self._on_severity,
        )
        self.severity_menu.set("Semua")
        self.severity_menu.pack(side="left")
        ghost_button(toolbar, "Muat Ulang", self._reload, width=130, icon="↻").pack(side="right")

        style_treeview(self.winfo_toplevel())
        columns = [
            ("target", "Target", 200),
            ("finding", "Nama Temuan", 220),
            ("score", "CVSS", 70),
            ("severity", "Severity", 110),
            ("impact", "Impact", 90),
            ("deadline", "Deadline", 90),
            ("owner", "Pemilik", 110),
            ("date", "Tanggal", 100),
        ]
        self.tree = build_treeview(self, columns, height=12)
        self.tree.bind("<Double-1>", lambda _e: self._open_selected())

        for severity, color in theme.SEVERITY_COLORS.items():
            self.tree.tag_configure(severity, foreground=color)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 4))
        actions = ctk.CTkFrame(footer, fg_color="transparent")
        actions.pack(side="left")
        ghost_button(actions, "Lihat / Edit", self._open_selected, width=140, icon="✎").pack(side="left", padx=(0, 8))
        primary_button(actions, "Export DOCX", lambda: self._export_selected("docx"), width=150, icon="⬇").pack(side="left", padx=(0, 8))
        primary_button(actions, "Export PDF", lambda: self._export_selected("pdf"), width=150, icon="⬇").pack(side="left", padx=(0, 8))
        if app.principal.can("assessment.delete") or app.principal.is_administrator:
            danger_button(actions, "Hapus", self._delete_selected, width=110, icon="🗑").pack(side="left")

        self.pagination = Pagination(footer, self._goto_page)
        self.pagination.pack(side="right")

        self._reload()

    def _apply_search(self) -> None:
        self._search = self.search_entry.get().strip()
        self._page = 1
        self._reload()

    def _on_severity(self, value: str) -> None:
        self._severity_filter = None if value == "Semua" else value
        self._page = 1
        self._reload()

    def _goto_page(self, page: int) -> None:
        self._page = page
        self._reload()

    def _reload(self) -> None:
        principal = self._app.principal
        owner_id = None if principal.is_administrator else principal.id
        summaries, total = self._app.container.assessments.list_summaries(
            page=self._page, page_size=_PAGE_SIZE, owner_id=owner_id, search=self._search, severity=self._severity_filter
        )
        self._total_pages = max((total + _PAGE_SIZE - 1) // _PAGE_SIZE, 1)
        self._row_ids.clear()
        self.tree.delete(*self.tree.get_children())
        for summary in summaries:
            row_id = self.tree.insert(
                "", "end",
                values=(
                    summary.target,
                    summary.finding_name,
                    f"{summary.cvss_score:.1f}",
                    summary.final_severity,
                    summary.business_impact,
                    summary.deadline_label,
                    summary.owner_username,
                    summary.found_on.strftime("%d-%m-%Y"),
                ),
                tags=(summary.final_severity,),
            )
            self._row_ids[row_id] = summary.id
        self.pagination.update_state(self._page, self._total_pages)
        if not summaries:
            self.tree.insert("", "end", values=("Belum ada data penilaian.", "", "", "", "", "", "", ""))

    def _selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            self._app.notify("Pilih salah satu baris terlebih dahulu.", "warning")
            return None
        return self._row_ids.get(selection[0])

    def _open_selected(self) -> None:
        assessment_id = self._selected_id()
        if assessment_id is None:
            return
        view = self._app.container.assessments.get_view(assessment_id)
        if view is None:
            self._app.notify("Penilaian tidak ditemukan.", "error")
            return
        self._app.open_assessment_editor(view)

    def _export_selected(self, kind: str) -> None:
        assessment_id = self._selected_id()
        if assessment_id is None:
            return
        view = self._app.container.assessments.get_view(assessment_id)
        if view is None:
            self._app.notify("Penilaian tidak ditemukan.", "error")
            return
        settings = self._app.container.settings.load()
        self._app.notify(f"Mengekspor {kind.upper()}...", "info")

        def worker() -> None:
            try:
                if kind == "docx":
                    from app.exports import export_docx

                    path = export_docx(view, settings)
                else:
                    from app.exports import export_pdf

                    path = export_pdf(view, settings)
                self.after(0, lambda: self._app.notify(f"Tersimpan: {path.split('/')[-1]}", "success"))
            except Exception as error:  # noqa: BLE001
                message = str(error)
                self.after(0, lambda: self._app.notify(f"Gagal export: {message}", "error"))

        threading.Thread(target=worker, daemon=True).start()

    def _delete_selected(self) -> None:
        assessment_id = self._selected_id()
        if assessment_id is None:
            return

        def confirm() -> None:
            actor = self._app.principal.audit_context()
            result = self._app.container.assessments.delete(actor, assessment_id)
            self._app.notify(result.message, "success" if result.success else "error")
            self._reload()

        ConfirmDialog(
            self, "Hapus Penilaian", "Yakin ingin menghapus penilaian ini? Tindakan ini tidak dapat dibatalkan.",
            confirm, danger=True,
        )
