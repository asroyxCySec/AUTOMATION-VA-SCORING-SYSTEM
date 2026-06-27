from __future__ import annotations

import customtkinter as ctk

from app import config
from app.services.container import ServiceContainer
from app.ui import theme
from app.ui.assessment_list_view import AssessmentListView
from app.ui.assessment_view import AssessmentView_Form
from app.ui.audit_log_view import AuditLogView
from app.ui.change_password_view import ChangePasswordView
from app.ui.components import Toast
from app.ui.dashboard_view import DashboardView
from app.ui.login_view import LoginView
from app.ui.profile_view import ProfileView
from app.ui.settings_view import SettingsView
from app.ui.sidebar import Sidebar
from app.ui.user_management_view import UserManagementView

_TITLES = {
    "dashboard": ("Dashboard", "Ringkasan penilaian kerentanan."),
    "assessment": ("Penilaian Baru", "Hitung CVSS otomatis dari parameter temuan."),
    "assessments": ("Daftar Penilaian", "Kelola dan ekspor laporan."),
    "users": ("Manajemen User", "Kelola akun dan peran."),
    "audit": ("Audit Log", "Jejak aktivitas sistem."),
    "settings": ("Pengaturan", "Konfigurasi aplikasi."),
    "profile": ("Profil", "Informasi akun Anda."),
}

_SESSION_POLL_MS = 5000


class VulnScoreApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        config.ensure_directories()
        self.container = ServiceContainer()
        self.principal = None
        self._settings = self.container.settings.load()

        theme.apply_appearance(self._settings.app_theme)
        self.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(1100, 720)
        self.configure(fg_color=theme.COLOR_BG)

        self._shell = None
        self._sidebar = None
        self._content = None
        self._content_view = None
        self._header_title = None
        self._header_subtitle = None
        self._timer_label = None
        self._active_toast = None
        self._session_job = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind_all("<Button-1>", self._on_activity, add="+")
        self.bind_all("<Key>", self._on_activity, add="+")

        self._show_login()

    def _clear_root(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def _show_login(self) -> None:
        self._stop_session_watch()
        self._clear_root()
        self._shell = None
        login = LoginView(self, self.container, self._on_login_success)
        login.pack(fill="both", expand=True)

    def _on_login_success(self, result) -> None:
        self.principal = result.principal
        if result.must_change_password:
            self._show_forced_change()
        else:
            self._enter_app()

    def _show_forced_change(self) -> None:
        self._clear_root()
        view = ChangePasswordView(self, self.container, self.principal, self._on_forced_done, forced=True)
        view.pack(fill="both", expand=True)

    def _on_forced_done(self) -> None:
        self.principal = self._refresh_principal()
        self._enter_app()

    def _refresh_principal(self):
        from app.services.auth_service import Principal
        from app.models import User
        from sqlalchemy import select

        with self.container.database.session() as session:
            user = session.scalar(select(User).where(User.id == self.principal.id))
            return Principal(
                id=user.id,
                username=user.username,
                full_name=user.full_name or user.username,
                role_name=user.role_name,
                permissions=frozenset(user.permission_codes()),
                must_change_password=user.must_change_password,
                is_administrator=user.is_administrator(),
            )

    def _enter_app(self) -> None:
        self._clear_root()
        self.container.session.start()
        self._build_shell()
        self.navigate("dashboard")
        self._start_session_watch()

    def _build_shell(self) -> None:
        self._shell = ctk.CTkFrame(self, fg_color=theme.COLOR_BG, corner_radius=0)
        self._shell.pack(fill="both", expand=True)
        self._shell.grid_columnconfigure(1, weight=1)
        self._shell.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(self._shell, self.principal, self.navigate, self._logout)
        self._sidebar.grid(row=0, column=0, sticky="ns")

        main = ctk.CTkFrame(self._shell, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(main, fg_color=theme.COLOR_SURFACE, corner_radius=0, height=72)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w", padx=28, pady=14)
        self._header_title = ctk.CTkLabel(title_box, text="", font=theme.font(20, "bold"), text_color=theme.COLOR_TEXT, anchor="w")
        self._header_title.pack(anchor="w")
        self._header_subtitle = ctk.CTkLabel(title_box, text="", font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self._header_subtitle.pack(anchor="w")

        session_box = ctk.CTkFrame(header, fg_color=theme.COLOR_SURFACE_ALT, corner_radius=10)
        session_box.grid(row=0, column=1, sticky="e", padx=28, pady=18)
        ctk.CTkLabel(session_box, text="Sesi:", font=theme.font(11, "bold"), text_color=theme.COLOR_TEXT_MUTED).pack(
            side="left", padx=(12, 4), pady=8
        )
        self._timer_label = ctk.CTkLabel(session_box, text="30:00", font=theme.mono_font(13, "bold"), text_color=theme.COLOR_ACCENT)
        self._timer_label.pack(side="left", padx=(0, 12), pady=8)

        self._content = ctk.CTkFrame(main, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew", padx=24, pady=(18, 18))
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

    def navigate(self, key: str, edit_view=None) -> None:
        if self._content is None:
            return
        if self._content_view is not None:
            self._content_view.destroy()
        title, subtitle = _TITLES.get(key, (config.APP_NAME, ""))
        self._header_title.configure(text=title)
        self._header_subtitle.configure(text=subtitle)
        self._sidebar.set_active(key)

        view = self._build_view(key, edit_view)
        view.grid(row=0, column=0, sticky="nsew")
        self._content_view = view
        self.container.session.touch()

    def _build_view(self, key: str, edit_view):
        if key == "dashboard":
            return DashboardView(self._content, self)
        if key == "assessment":
            return AssessmentView_Form(self._content, self, edit_view=edit_view)
        if key == "assessments":
            return AssessmentListView(self._content, self)
        if key == "users" and self.principal.is_administrator:
            return UserManagementView(self._content, self)
        if key == "audit" and self.principal.is_administrator:
            return AuditLogView(self._content, self)
        if key == "settings" and self.principal.is_administrator:
            return SettingsView(self._content, self)
        if key == "profile":
            return ProfileView(self._content, self)
        return DashboardView(self._content, self)

    def open_assessment_editor(self, view) -> None:
        title, subtitle = ("Edit Penilaian", "Perbarui data dan hitung ulang skor.")
        if self._content_view is not None:
            self._content_view.destroy()
        self._header_title.configure(text=title)
        self._header_subtitle.configure(text=subtitle)
        self._sidebar.set_active("assessments")
        editor = AssessmentView_Form(self._content, self, edit_view=view)
        editor.grid(row=0, column=0, sticky="nsew")
        self._content_view = editor

    def notify(self, message: str, kind: str = "info") -> None:
        if self._active_toast is not None:
            try:
                self._active_toast.destroy()
            except Exception:  # noqa: BLE001
                pass
        toast = Toast(self, message, kind)
        toast.place(relx=0.5, rely=0.06, anchor="n")
        toast.lift()
        self._active_toast = toast
        self.after(3600, lambda t=toast: self._dismiss_toast(t))

    def _dismiss_toast(self, toast) -> None:
        try:
            toast.destroy()
        except Exception:  # noqa: BLE001
            pass
        if self._active_toast is toast:
            self._active_toast = None

    def apply_theme(self, value: str) -> None:
        theme.apply_appearance(value)

    def _on_activity(self, _event=None) -> None:
        if self.container.session.active:
            self.container.session.touch()

    def _start_session_watch(self) -> None:
        self._tick_session()

    def _stop_session_watch(self) -> None:
        if self._session_job is not None:
            try:
                self.after_cancel(self._session_job)
            except Exception:  # noqa: BLE001
                pass
            self._session_job = None

    def _tick_session(self) -> None:
        if not self.container.session.active:
            return
        if self.container.session.is_expired():
            self._handle_timeout()
            return
        remaining = self.container.session.remaining_seconds()
        minutes, seconds = divmod(remaining, 60)
        if self._timer_label is not None:
            color = theme.COLOR_DANGER if remaining <= 120 else theme.COLOR_ACCENT
            self._timer_label.configure(text=f"{minutes:02d}:{seconds:02d}", text_color=color)
        self._session_job = self.after(_SESSION_POLL_MS, self._tick_session)

    def _handle_timeout(self) -> None:
        self._stop_session_watch()
        if self.principal is not None:
            self.container.auth.logout(self.principal)
        self.container.session.stop()
        self.principal = None
        self._show_login()
        self.after(200, lambda: self.notify("Sesi berakhir karena tidak ada aktivitas. Silakan masuk kembali.", "warning"))

    def _logout(self) -> None:
        self._stop_session_watch()
        if self.principal is not None:
            self.container.auth.logout(self.principal)
        self.container.session.stop()
        self.principal = None
        self._show_login()
        self.after(150, lambda: self.notify("Anda telah keluar.", "info"))

    def _on_close(self) -> None:
        self._stop_session_watch()
        if self.principal is not None:
            try:
                self.container.auth.logout(self.principal)
            except Exception:  # noqa: BLE001
                pass
        self.destroy()


def launch() -> None:
    app = VulnScoreApp()
    app.mainloop()
