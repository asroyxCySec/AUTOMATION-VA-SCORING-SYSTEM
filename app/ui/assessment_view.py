from __future__ import annotations

import os
import threading
from datetime import date, datetime

import customtkinter as ctk

from app.core.cvss import (
    AttackComplexity,
    AttackVector,
    Impact,
    PrivilegesRequired,
    Scope,
    UserInteraction,
)
from app.core.scoring import ScoringInput
from app.services.audit_service import AuditContext
from app.ui import theme
from app.ui.components import (
    Badge,
    Card,
    FormField,
    FormSelect,
    LabeledTextbox,
    LoadingOverlay,
    SectionTitle,
    Toast,
    ghost_button,
    primary_button,
)

_AV = {"Network (N)": AttackVector.NETWORK, "Adjacent (A)": AttackVector.ADJACENT, "Local (L)": AttackVector.LOCAL, "Physical (P)": AttackVector.PHYSICAL}
_AC = {"Low (L)": AttackComplexity.LOW, "High (H)": AttackComplexity.HIGH}
_PR = {"None (N)": PrivilegesRequired.NONE, "Low (L)": PrivilegesRequired.LOW, "High (H)": PrivilegesRequired.HIGH}
_UI = {"None (N)": UserInteraction.NONE, "Required (R)": UserInteraction.REQUIRED}
_S = {"Unchanged (U)": Scope.UNCHANGED, "Changed (C)": Scope.CHANGED}
_IMPACT = {"None (N)": Impact.NONE, "Low (L)": Impact.LOW, "High (H)": Impact.HIGH}
_REGULATIONS = ("UU PDP", "PP SPBE", "SNI ISO 27001", "Lainnya")
_BUSINESS = ("Low", "Medium", "High", "Critical")


def _reverse(mapping: dict, enum_value: str) -> str:
    for label, member in mapping.items():
        if member.value == enum_value:
            return label
    return next(iter(mapping))


class AssessmentView_Form(ctk.CTkFrame):
    def __init__(self, master, app, edit_view=None) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        self._edit_view = edit_view
        self._current_view = None
        self._regulation_vars: dict[str, ctk.BooleanVar] = {}
        self._loading = LoadingOverlay(self, "Menghitung skor & menyimpan...")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        title_text = "Edit Penilaian" if edit_view else "Penilaian Kerentanan Baru"
        subtitle = "Perbarui data temuan dan hitung ulang skor." if edit_view else "Isi parameter temuan untuk perhitungan CVSS otomatis."
        SectionTitle(scroll, title_text, subtitle).pack(anchor="w", pady=(4, 16))

        self._build_info_section(scroll)
        self._build_parameter_section(scroll)
        self._build_exploit_section(scroll)
        self._build_impact_section(scroll)
        self._build_chaining_section(scroll)

        action_row = ctk.CTkFrame(scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=(8, 4))
        self.submit_button = primary_button(
            action_row, "Hitung & Simpan" if not edit_view else "Hitung & Perbarui", self._submit, width=220, icon="⚡"
        )
        self.submit_button.pack(side="left")
        ghost_button(action_row, "Reset Form", self._reset, width=150, icon="↺").pack(side="left", padx=10)

        self.result_card = Card(scroll)
        self._build_result_placeholder()

        if edit_view:
            self._prefill(edit_view)

    def _build_info_section(self, master) -> None:
        card = Card(master)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Informasi Temuan", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(16, 12)
        )
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 18))
        grid.grid_columnconfigure(0, weight=1, uniform="info")
        grid.grid_columnconfigure(1, weight=1, uniform="info")
        self.target_field = FormField(grid, "Target / URL", placeholder="https://contoh.go.id")
        self.target_field.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.finding_field = FormField(grid, "Nama Temuan", placeholder="SQL Injection pada login")
        self.finding_field.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.date_field = FormField(grid, "Tanggal Ditemukan (YYYY-MM-DD)", placeholder=date.today().isoformat())
        self.date_field.set(date.today().isoformat())
        self.date_field.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=8)
        self.researcher_field = FormField(grid, "Peneliti / Handle", placeholder="handle")
        self.researcher_field.set(self._app.principal.username)
        self.researcher_field.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=8)

    def _build_parameter_section(self, master) -> None:
        card = Card(master)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Parameter CVSS v3.1", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(16, 12)
        )
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 18))
        for column in range(4):
            grid.grid_columnconfigure(column, weight=1, uniform="param")
        self.av_select = FormSelect(grid, "Attack Vector", list(_AV), default="Network (N)")
        self.av_select.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=8)
        self.ac_select = FormSelect(grid, "Attack Complexity", list(_AC), default="Low (L)")
        self.ac_select.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        self.pr_select = FormSelect(grid, "Privileges Required", list(_PR), default="None (N)")
        self.pr_select.grid(row=0, column=2, sticky="ew", padx=6, pady=8)
        self.ui_select = FormSelect(grid, "User Interaction", list(_UI), default="None (N)")
        self.ui_select.grid(row=0, column=3, sticky="ew", padx=(6, 0), pady=8)
        self.scope_select = FormSelect(grid, "Scope", list(_S), default="Unchanged (U)")
        self.scope_select.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=8)
        self.c_select = FormSelect(grid, "Confidentiality", list(_IMPACT), default="High (H)")
        self.c_select.grid(row=1, column=1, sticky="ew", padx=6, pady=8)
        self.i_select = FormSelect(grid, "Integrity", list(_IMPACT), default="High (H)")
        self.i_select.grid(row=1, column=2, sticky="ew", padx=6, pady=8)
        self.a_select = FormSelect(grid, "Availability", list(_IMPACT), default="High (H)")
        self.a_select.grid(row=1, column=3, sticky="ew", padx=(6, 0), pady=8)

    def _build_exploit_section(self, master) -> None:
        card = Card(master)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Exploitability", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(16, 12)
        )
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 14))
        grid.grid_columnconfigure(0, weight=1, uniform="exp")
        grid.grid_columnconfigure(1, weight=1, uniform="exp")
        self.cve_field = FormField(grid, "CVE ID (opsional)", placeholder="CVE-2024-1234")
        self.cve_field.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        poc_frame = ctk.CTkFrame(grid, fg_color="transparent")
        poc_frame.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        ctk.CTkLabel(
            poc_frame, text="Lampiran PoC (opsional)", font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        picker = ctk.CTkFrame(poc_frame, fg_color="transparent")
        picker.pack(fill="x")
        self.poc_path_label = ctk.CTkLabel(
            picker, text="Belum ada file", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED, anchor="w",
            fg_color=theme.COLOR_INPUT_BG, corner_radius=10, height=40,
        )
        self.poc_path_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_button(picker, "Pilih", self._pick_poc, width=80, icon="📎").pack(side="left")
        self._poc_path = ""

        toggles = ctk.CTkFrame(card, fg_color="transparent")
        toggles.pack(fill="x", padx=20, pady=(0, 18))
        self.public_exploit_var = ctk.BooleanVar(value=False)
        self.reproducible_var = ctk.BooleanVar(value=True)
        self.poc_available_var = ctk.BooleanVar(value=False)
        self._switch(toggles, "Public Exploit / CVE tersedia", self.public_exploit_var).pack(side="left", padx=(0, 24))
        self._switch(toggles, "Dapat direproduksi", self.reproducible_var).pack(side="left", padx=(0, 24))
        self._switch(toggles, "PoC tersedia", self.poc_available_var).pack(side="left")

    def _build_impact_section(self, master) -> None:
        card = Card(master)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Detail Dampak", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(16, 12)
        )
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 12))
        grid.grid_columnconfigure(0, weight=1, uniform="imp")
        grid.grid_columnconfigure(1, weight=1, uniform="imp")
        self.impacted_box = LabeledTextbox(grid, "Data Terdampak", height=70)
        self.impacted_box.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=8)
        right = ctk.CTkFrame(grid, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=8)
        self.users_field = FormField(right, "Estimasi Jumlah User")
        self.users_field.pack(fill="x", pady=(0, 8))
        self.business_select = FormSelect(right, "Business Impact", list(_BUSINESS), default="Medium")
        self.business_select.pack(fill="x")

        reg_frame = ctk.CTkFrame(card, fg_color="transparent")
        reg_frame.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkLabel(
            reg_frame, text="Regulasi Terkait", font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w"
        ).pack(anchor="w", pady=(0, 6))
        checks = ctk.CTkFrame(reg_frame, fg_color="transparent")
        checks.pack(fill="x")
        for regulation in _REGULATIONS:
            var = ctk.BooleanVar(value=False)
            self._regulation_vars[regulation] = var
            ctk.CTkCheckBox(
                checks, text=regulation, variable=var, font=theme.font(12), text_color=theme.COLOR_TEXT,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER, corner_radius=6,
                checkbox_width=20, checkbox_height=20,
            ).pack(side="left", padx=(0, 18))

    def _build_chaining_section(self, master) -> None:
        card = Card(master)
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(card, text="Severity Chaining", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT).pack(
            anchor="w", padx=20, pady=(16, 4)
        )
        ctk.CTkLabel(
            card,
            text="Centang kondisi yang berlaku. Sistem akan menaikkan severity secara otomatis bila relevan.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED, anchor="w", wraplength=820, justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))
        container = ctk.CTkFrame(card, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=(0, 18))
        container.grid_columnconfigure(0, weight=1, uniform="chain")
        container.grid_columnconfigure(1, weight=1, uniform="chain")
        self.chain_phpinfo_var = ctk.BooleanVar(value=False)
        self.chain_credentials_var = ctk.BooleanVar(value=False)
        self.chain_version_var = ctk.BooleanVar(value=False)
        self.chain_entry_var = ctk.BooleanVar(value=False)
        self._switch(container, "phpinfo + CVE aktif", self.chain_phpinfo_var).grid(row=0, column=0, sticky="w", pady=6)
        self._switch(container, "Dev server + kredensial bocor", self.chain_credentials_var).grid(row=0, column=1, sticky="w", pady=6)
        self._switch(container, "Version disclosure + CVE kritikal", self.chain_version_var).grid(row=1, column=0, sticky="w", pady=6)
        self._switch(container, "Menjadi entry point serangan berantai", self.chain_entry_var).grid(row=1, column=1, sticky="w", pady=6)

    def _switch(self, master, text: str, variable: ctk.BooleanVar) -> ctk.CTkSwitch:
        return ctk.CTkSwitch(
            master, text=text, variable=variable, font=theme.font(12), text_color=theme.COLOR_TEXT,
            progress_color=theme.COLOR_PRIMARY, button_color="#FFFFFF", button_hover_color="#E5E9F5",
        )

    def _build_result_placeholder(self) -> None:
        for widget in self.result_card.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.result_card,
            text="Hasil perhitungan akan muncul di sini setelah Anda menekan tombol Hitung & Simpan.",
            font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED, wraplength=820, justify="left",
        ).pack(anchor="w", padx=20, pady=20)
        self.result_card.pack(fill="x", pady=(6, 30))

    def _pick_poc(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(title="Pilih lampiran PoC")
        if path:
            self._poc_path = path
            self.poc_path_label.configure(text=os.path.basename(path), text_color=theme.COLOR_TEXT)

    def _prefill(self, view) -> None:
        self.target_field.set(view.target)
        self.finding_field.set(view.finding_name)
        self.date_field.set(view.found_on.isoformat())
        self.researcher_field.set(view.researcher)
        self.av_select.set(_reverse(_AV, view.metric_codes["AV"]))
        self.ac_select.set(_reverse(_AC, view.metric_codes["AC"]))
        self.pr_select.set(_reverse(_PR, view.metric_codes["PR"]))
        self.ui_select.set(_reverse(_UI, view.metric_codes["UI"]))
        self.scope_select.set(_reverse(_S, view.metric_codes["S"]))
        self.c_select.set(_reverse(_IMPACT, view.metric_codes["C"]))
        self.i_select.set(_reverse(_IMPACT, view.metric_codes["I"]))
        self.a_select.set(_reverse(_IMPACT, view.metric_codes["A"]))
        self.cve_field.set(view.cve_id)
        self.impacted_box.set(view.impacted_data)
        self.users_field.set(view.estimated_users)
        self.business_select.set(view.business_impact)
        self.public_exploit_var.set(view.public_exploit)
        self.reproducible_var.set(view.reproducible)
        self.poc_available_var.set(view.poc_available)
        self.chain_phpinfo_var.set(view.chain_phpinfo_cve)
        self.chain_credentials_var.set(view.chain_dev_credentials)
        self.chain_version_var.set(view.chain_version_critical_cve)
        self.chain_entry_var.set(view.chain_entry_point)
        if view.poc_attachment_path:
            self._poc_path = view.poc_attachment_path
            self.poc_path_label.configure(text=os.path.basename(view.poc_attachment_path), text_color=theme.COLOR_TEXT)
        for regulation, var in self._regulation_vars.items():
            var.set(regulation in view.regulations)

    def _reset(self) -> None:
        self._app.navigate("assessment")

    def _collect(self) -> ScoringInput | None:
        target = self.target_field.get()
        finding = self.finding_field.get()
        researcher = self.researcher_field.get()
        raw_date = self.date_field.get()
        if not target or not finding or not researcher:
            self._notify("Target, nama temuan, dan peneliti wajib diisi.", "error")
            return None
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            self._notify("Format tanggal harus YYYY-MM-DD.", "error")
            return None
        regulations = tuple(reg for reg, var in self._regulation_vars.items() if var.get())
        return ScoringInput(
            target=target,
            finding_name=finding,
            found_on=parsed_date,
            researcher=researcher,
            attack_vector=_AV[self.av_select.get()],
            attack_complexity=_AC[self.ac_select.get()],
            privileges_required=_PR[self.pr_select.get()],
            user_interaction=_UI[self.ui_select.get()],
            scope=_S[self.scope_select.get()],
            confidentiality=_IMPACT[self.c_select.get()],
            integrity=_IMPACT[self.i_select.get()],
            availability=_IMPACT[self.a_select.get()],
            public_exploit=self.public_exploit_var.get(),
            cve_id=self.cve_field.get(),
            reproducible=self.reproducible_var.get(),
            poc_available=self.poc_available_var.get(),
            poc_attachment_path=self._poc_path,
            impacted_data=self.impacted_box.get(),
            estimated_users=self.users_field.get(),
            regulations=regulations,
            business_impact=self.business_select.get(),
            chain_phpinfo_cve=self.chain_phpinfo_var.get(),
            chain_dev_credentials=self.chain_credentials_var.get(),
            chain_version_critical_cve=self.chain_version_var.get(),
            chain_entry_point=self.chain_entry_var.get(),
        )

    def _submit(self) -> None:
        data = self._collect()
        if data is None:
            return
        self.submit_button.configure(state="disabled")
        self._loading.start()
        actor = self._app.principal.audit_context()

        def worker() -> None:
            if self._edit_view is not None:
                result = self._app.container.assessments.update(actor, self._edit_view.id, data)
                assessment_id = self._edit_view.id if result.success else None
            else:
                result = self._app.container.assessments.create(actor, self._app.principal.id, data)
                assessment_id = result.assessment_id
            view = self._app.container.assessments.get_view(assessment_id) if assessment_id else None
            self.after(0, lambda: self._finish(result, view))

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, result, view) -> None:
        self._loading.stop()
        self.submit_button.configure(state="normal")
        if not result.success or view is None:
            self._notify(result.message or "Gagal menyimpan penilaian.", "error")
            return
        self._current_view = view
        self._render_result(view)
        self._notify(result.message, "success")

    def _render_result(self, view) -> None:
        for widget in self.result_card.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(self.result_card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 8))
        ctk.CTkLabel(header, text="Hasil Penilaian", font=theme.font(16, "bold"), text_color=theme.COLOR_TEXT).pack(side="left")
        Badge(header, f"{view.final_severity}", theme.SEVERITY_COLORS.get(view.final_severity, theme.COLOR_PRIMARY)).pack(side="right")

        score_row = ctk.CTkFrame(self.result_card, fg_color="transparent")
        score_row.pack(fill="x", padx=20, pady=(4, 8))
        for column in range(3):
            score_row.grid_columnconfigure(column, weight=1, uniform="score")
        self._result_metric(score_row, "Base Score", f"{view.cvss_score:.1f}", theme.COLOR_PRIMARY).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self._result_metric(score_row, "Severity Akhir", view.final_severity, theme.SEVERITY_COLORS.get(view.final_severity, theme.COLOR_PRIMARY)).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        self._result_metric(score_row, "Deadline Remediasi", view.deadline_label, theme.COLOR_WARNING).grid(
            row=0, column=2, sticky="ew", padx=(8, 0)
        )

        vector = ctk.CTkLabel(
            self.result_card, text=view.cvss_vector, font=theme.mono_font(12, "bold"), text_color=theme.COLOR_ACCENT,
            fg_color=theme.COLOR_INPUT_BG, corner_radius=8, anchor="w",
        )
        vector.pack(fill="x", padx=20, pady=(6, 8), ipady=8, ipadx=10)

        if view.severity_upgraded and view.severity_reasons:
            note = ctk.CTkFrame(self.result_card, fg_color=theme.COLOR_SURFACE_ALT, corner_radius=10)
            note.pack(fill="x", padx=20, pady=(2, 8))
            ctk.CTkLabel(
                note, text="Severity dinaikkan otomatis:", font=theme.font(12, "bold"), text_color=theme.COLOR_WARNING, anchor="w"
            ).pack(anchor="w", padx=12, pady=(10, 2))
            for reason in view.severity_reasons:
                ctk.CTkLabel(
                    note, text=f"•  {reason}", font=theme.font(12), text_color=theme.COLOR_TEXT, anchor="w", wraplength=780, justify="left"
                ).pack(anchor="w", padx=12, pady=(0, 2))
            ctk.CTkFrame(note, height=6, fg_color="transparent").pack()

        rem = ctk.CTkFrame(self.result_card, fg_color="transparent")
        rem.pack(fill="x", padx=20, pady=(2, 6))
        ctk.CTkLabel(
            rem, text=f"Remediasi: {view.remediation_name}  ·  {view.remediation_owasp}  ·  {view.remediation_cwe}",
            font=theme.font(12, "bold"), text_color=theme.COLOR_TEXT_MUTED, anchor="w", wraplength=800, justify="left",
        ).pack(anchor="w")

        export_row = ctk.CTkFrame(self.result_card, fg_color="transparent")
        export_row.pack(fill="x", padx=20, pady=(10, 18))
        self.docx_button = primary_button(export_row, "Export DOCX", lambda: self._export("docx"), width=170, icon="⬇")
        self.docx_button.pack(side="left", padx=(0, 10))
        self.pdf_button = primary_button(export_row, "Export PDF", lambda: self._export("pdf"), width=170, icon="⬇")
        self.pdf_button.pack(side="left", padx=(0, 10))
        ghost_button(export_row, "Buka Folder Laporan", self._open_reports, width=200, icon="📂").pack(side="left")

    def _result_metric(self, master, label: str, value: str, color: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(master, fg_color=theme.COLOR_SURFACE_ALT, corner_radius=12)
        ctk.CTkLabel(frame, text=label, font=theme.font(11, "bold"), text_color=theme.COLOR_TEXT_MUTED).pack(
            anchor="w", padx=14, pady=(12, 0)
        )
        ctk.CTkLabel(frame, text=value, font=theme.font(20, "bold"), text_color=color).pack(anchor="w", padx=14, pady=(2, 12))
        return frame

    def _export(self, kind: str) -> None:
        if self._current_view is None:
            return
        button = self.docx_button if kind == "docx" else self.pdf_button
        button.configure(state="disabled", text="Mengekspor...")
        settings = self._app.container.settings.load()
        view = self._current_view

        def worker() -> None:
            try:
                if kind == "docx":
                    from app.exports import export_docx

                    path = export_docx(view, settings)
                else:
                    from app.exports import export_pdf

                    path = export_pdf(view, settings)
                self.after(0, lambda: self._export_done(kind, path, None))
            except Exception as error:  # noqa: BLE001
                message = str(error)
                self.after(0, lambda: self._export_done(kind, None, message))

        threading.Thread(target=worker, daemon=True).start()

    def _export_done(self, kind: str, path: str | None, error: str | None) -> None:
        button = self.docx_button if kind == "docx" else self.pdf_button
        button.configure(state="normal", text=f"⬇  Export {kind.upper()}")
        if error or not path:
            self._notify(f"Gagal export {kind.upper()}: {error}", "error")
            return
        self._notify(f"Laporan {kind.upper()} tersimpan: {os.path.basename(path)}", "success")

    def _open_reports(self) -> None:
        from app import config

        config.ensure_directories()
        self._notify(f"Folder laporan: {config.EXPORT_DIR}", "info")
        self._reveal(str(config.EXPORT_DIR))

    def _reveal(self, path: str) -> None:
        import subprocess
        import sys

        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            pass

    def _notify(self, message: str, kind: str) -> None:
        self._app.notify(message, kind)
