# VulnScore — Automatic Vulnerability Assessment Scoring System

Aplikasi desktop untuk penilaian kerentanan otomatis berbasis CVSS v3.1, lengkap dengan autentikasi, RBAC, audit log, dan ekspor laporan profesional (DOCX & PDF). Dibangun dengan Python + CustomTkinter, arsitektur modular (core / models / services / exports / ui) dengan dependency injection.

## Fitur Utama

- **Skoring CVSS v3.1 resmi** — implementasi formula FIRST.org (bukan if-else sederhana), menghasilkan base score, vector string, dan severity otomatis.
- **Severity chaining** — peningkatan severity otomatis untuk kombinasi kondisi (phpinfo + CVE aktif, dev server + kredensial bocor, version disclosure + CVE kritikal, entry point berantai), disertai alasan.
- **Remediasi & deadline otomatis** — basis pengetahuan 15+ kelas kerentanan (OWASP/CWE/CAPEC) dengan deadline mengikuti severity (Critical 24 jam, High 7 hari, Medium/Low 30 hari).
- **Laporan profesional** — ekspor DOCX (python-docx) dan PDF (ReportLab) dengan cover, badge severity, tabel modern, header/footer, dan nomor halaman. Nama berkas otomatis: `Target_NamaTemuan_Tanggal`.
- **Autentikasi & RBAC** — login dengan hashing bcrypt, role Administrator & User, brute-force protection (5 gagal → kunci 15 menit), idle session timeout 30 menit.
- **Manajemen user** — CRUD, reset password, aktif/nonaktif, ubah role, pencarian, filter, dan paginasi.
- **Audit log** — pencatatan timestamp, user, role, IP, hostname, aksi, dan status.
- **Dashboard** — statistik dengan cakupan berbeda untuk admin (seluruh sistem) dan user (milik sendiri).
- **Backup & restore** basis data, serta pengaturan identitas instansi, logo, tema, dan bahasa.

## Persyaratan

- Python 3.10 atau lebih baru (diuji pada 3.12)
- Sistem operasi: Windows, Linux, atau macOS
- Pada Linux, pastikan Tkinter tersedia: `sudo apt install python3-tk`

## Instalasi

```bash
# 1. Masuk ke direktori proyek
cd va_scoring_system

# 2. (Opsional, disarankan) buat virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Pasang dependensi
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
python main.py
```

Saat pertama dijalankan, basis data SQLite dibuat otomatis di folder `data/` beserta akun admin default:

- **Username:** `admin`
- **Password:** `admin123`

Password default **wajib diganti** pada login pertama.

## Struktur Proyek

```
va_scoring_system/
├── main.py                  Entry point aplikasi
├── requirements.txt
├── app/
│   ├── config.py            Konfigurasi & path (PyInstaller-aware)
│   ├── core/                Logika murni: CVSS, severity, remediasi, deadline, scoring, security
│   ├── models/              Model SQLAlchemy (user, role, permission, assessment, audit, dst.)
│   ├── services/            Service layer + dependency injection container
│   ├── exports/             Generator laporan DOCX & PDF
│   ├── ui/                  Antarmuka CustomTkinter (login, dashboard, form, dll.)
│   └── assets/              Aset statis
└── data/                    Basis data, laporan, backup, unggahan (dibuat otomatis)
```

## Mengganti ke PostgreSQL

Secara default aplikasi memakai SQLite. Untuk PostgreSQL, set variabel lingkungan `VULNSCORE_DATABASE_URL` sebelum menjalankan aplikasi:

```bash
# Linux / macOS
export VULNSCORE_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/vulnscore"
# Windows (PowerShell)
$env:VULNSCORE_DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/vulnscore"
```

Pasang juga driver-nya: `pip install "psycopg[binary]"`.

## Membangun Executable (.exe) dengan PyInstaller

```bash
# 1. Pasang PyInstaller
pip install pyinstaller

# 2. Bangun single-file executable
pyinstaller --noconfirm --windowed --onefile ^
  --name VulnScore ^
  --collect-all customtkinter ^
  --collect-all ttkbootstrap ^
  main.py
```

Pada Linux/macOS gunakan tanda sambung baris `\` menggantikan `^`:

```bash
pyinstaller --noconfirm --windowed --onefile \
  --name VulnScore \
  --collect-all customtkinter \
  --collect-all ttkbootstrap \
  main.py
```

Hasilnya berada di folder `dist/`. Flag `--collect-all customtkinter` penting agar tema dan aset CustomTkinter ikut terbundel. Basis data dan folder `data/` akan dibuat di samping executable saat dijalankan.

> Catatan: jalankan PyInstaller pada sistem operasi target (executable Windows dibangun di Windows, dan seterusnya).

## Catatan Keamanan

- Password disimpan sebagai hash bcrypt (cost 12), bukan teks biasa.
- Aktivitas sensitif tercatat di audit log beserta IP dan hostname.
- Administrator aktif terakhir tidak dapat dihapus, dinonaktifkan, atau diturunkan perannya demi mencegah penguncian sistem.
