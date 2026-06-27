from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.components import Card, DistributionRow, SectionTitle, StatCard


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self._app = app
        principal = app.principal
        owner_id = None if principal.is_administrator else principal.id
        stats = app.container.assessments.dashboard_stats(owner_id)

        scope_label = "seluruh sistem" if principal.is_administrator else "milik Anda"
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(4, 18))
        SectionTitle(
            header,
            f"Selamat datang, {principal.full_name}",
            f"Ringkasan penilaian kerentanan {scope_label}.",
        ).pack(side="left", anchor="w")

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x")
        for index in range(4):
            cards.grid_columnconfigure(index, weight=1, uniform="stat")
        StatCard(cards, "Total Penilaian", str(stats.total_assessments), theme.COLOR_PRIMARY, "▤").grid(
            row=0, column=0, sticky="nsew", padx=(0, 8), pady=4
        )
        StatCard(cards, "Bulan Ini", str(stats.this_month), theme.COLOR_ACCENT, "◷").grid(
            row=0, column=1, sticky="nsew", padx=8, pady=4
        )
        StatCard(cards, "Rata-rata CVSS", f"{stats.average_score:.1f}", theme.COLOR_WARNING, "◈").grid(
            row=0, column=2, sticky="nsew", padx=8, pady=4
        )
        critical_high = stats.severity_counts.get("Critical", 0) + stats.severity_counts.get("High", 0)
        StatCard(cards, "Critical + High", str(critical_high), theme.COLOR_DANGER, "⚠").grid(
            row=0, column=3, sticky="nsew", padx=(8, 0), pady=4
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(18, 0))
        body.grid_columnconfigure(0, weight=3, uniform="body")
        body.grid_columnconfigure(1, weight=2, uniform="body")

        severity_card = Card(body)
        severity_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            severity_card, text="Distribusi Severity", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(
            severity_card, text="Sebaran tingkat keparahan temuan.", font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 12))
        total_sev = sum(stats.severity_counts.values()) or 1
        for label in ("Critical", "High", "Medium", "Low", "Informational"):
            DistributionRow(
                severity_card, label, stats.severity_counts.get(label, 0), total_sev, theme.SEVERITY_COLORS[label]
            ).pack(fill="x", padx=20, pady=6)
        ctk.CTkFrame(severity_card, height=8, fg_color="transparent").pack()

        impact_card = Card(body)
        impact_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(
            impact_card, text="Business Impact", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(
            impact_card, text="Dampak terhadap bisnis.", font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 12))
        total_impact = sum(stats.business_impact_counts.values()) or 1
        for label in ("Critical", "High", "Medium", "Low"):
            DistributionRow(
                impact_card, label, stats.business_impact_counts.get(label, 0), total_impact, theme.BUSINESS_IMPACT_COLORS[label]
            ).pack(fill="x", padx=20, pady=6)
        ctk.CTkFrame(impact_card, height=8, fg_color="transparent").pack()

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="both", expand=True, pady=(18, 8))
        bottom.grid_columnconfigure(0, weight=1, uniform="bottom")
        bottom.grid_columnconfigure(1, weight=1, uniform="bottom")

        top_card = Card(bottom)
        top_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            top_card, text="Temuan Terbanyak", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(18, 12))
        if stats.top_vulnerabilities:
            max_count = stats.top_vulnerabilities[0][1] or 1
            for name, count in stats.top_vulnerabilities:
                DistributionRow(top_card, name[:18], count, max_count, theme.COLOR_PRIMARY).pack(fill="x", padx=20, pady=6)
        else:
            ctk.CTkLabel(
                top_card, text="Belum ada data temuan.", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
            ).pack(anchor="w", padx=20, pady=(0, 18))
        ctk.CTkFrame(top_card, height=8, fg_color="transparent").pack()

        trend_card = Card(bottom)
        trend_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(
            trend_card, text="Tren Bulanan", font=theme.font(15, "bold"), text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=20, pady=(18, 12))
        if stats.monthly_trend:
            max_trend = max(count for _, count in stats.monthly_trend) or 1
            for month, count in stats.monthly_trend:
                DistributionRow(trend_card, month, count, max_trend, theme.COLOR_ACCENT).pack(fill="x", padx=20, pady=6)
        else:
            ctk.CTkLabel(
                trend_card, text="Belum ada data tren.", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
            ).pack(anchor="w", padx=20, pady=(0, 18))
        ctk.CTkFrame(trend_card, height=8, fg_color="transparent").pack()
