from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RemediationEntry:
    name: str
    steps: tuple[str, ...]
    owasp: str
    cwe: str
    capec: str
    references: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RemediationMatch:
    entry: RemediationEntry
    matched_keyword: str


_KNOWLEDGE_BASE: tuple[tuple[tuple[str, ...], RemediationEntry], ...] = (
    (
        ("sql injection", "sqli", "sql"),
        RemediationEntry(
            name="SQL Injection",
            steps=(
                "Gunakan prepared statement dengan parameterized query pada seluruh akses basis data.",
                "Terapkan input validation dengan allowlist tipe dan panjang data pada setiap parameter.",
                "Jalankan aplikasi dengan akun database least privilege tanpa hak DDL atau akses lintas skema.",
                "Aktifkan escaping output dan nonaktifkan pesan error database yang verbose ke pengguna.",
                "Pasang WAF rule untuk pola injeksi dan lakukan code review pada lapisan data access.",
            ),
            owasp="A03:2021 Injection",
            cwe="CWE-89",
            capec="CAPEC-66",
            references=(
                "OWASP SQL Injection Prevention Cheat Sheet",
                "OWASP ASVS V5 Validation, Sanitization and Encoding",
            ),
        ),
    ),
    (
        ("stored xss", "reflected xss", "dom xss", "cross site scripting", "cross-site scripting", "xss"),
        RemediationEntry(
            name="Cross-Site Scripting (XSS)",
            steps=(
                "Terapkan output encoding kontekstual untuk HTML, atribut, JavaScript, dan URL.",
                "Validasi input dengan allowlist dan tolak markup yang tidak diharapkan.",
                "Aktifkan Content Security Policy yang ketat tanpa unsafe-inline dan unsafe-eval.",
                "Set atribut HttpOnly dan SameSite pada cookie sesi agar tidak terbaca skrip.",
                "Gunakan template engine dengan auto-escaping dan hindari penyisipan HTML mentah.",
            ),
            owasp="A03:2021 Injection",
            cwe="CWE-79",
            capec="CAPEC-63",
            references=(
                "OWASP Cross Site Scripting Prevention Cheat Sheet",
                "OWASP DOM based XSS Prevention Cheat Sheet",
            ),
        ),
    ),
    (
        ("idor", "insecure direct object reference", "broken access control", "bola", "broken object level"),
        RemediationEntry(
            name="Insecure Direct Object Reference / Broken Access Control",
            steps=(
                "Lakukan otorisasi per objek di sisi server berbasis kepemilikan dan peran pengguna.",
                "Hindari identifier yang dapat ditebak dengan memetakan ke referensi tidak langsung per sesi.",
                "Terapkan kebijakan deny by default pada seluruh endpoint dan fungsi sensitif.",
                "Catat dan pantau percobaan akses lintas objek untuk deteksi penyalahgunaan.",
                "Tambahkan pengujian otorisasi otomatis pada pipeline integrasi berkelanjutan.",
            ),
            owasp="A01:2021 Broken Access Control",
            cwe="CWE-639",
            capec="CAPEC-122",
            references=(
                "OWASP Authorization Cheat Sheet",
                "OWASP Insecure Direct Object Reference Prevention Cheat Sheet",
            ),
        ),
    ),
    (
        ("path traversal", "directory traversal", "lfi", "local file inclusion", "../"),
        RemediationEntry(
            name="Path Traversal / Local File Inclusion",
            steps=(
                "Kanonikalisasi path lalu verifikasi tetap berada di dalam direktori dasar yang diizinkan.",
                "Gunakan allowlist nama berkas dan tolak karakter traversal serta null byte.",
                "Pisahkan penyimpanan berkas pengguna dari root aplikasi dan batasi hak baca proses.",
                "Hindari memasukkan input pengguna langsung ke fungsi include atau pembukaan berkas.",
                "Terapkan sandbox atau chroot untuk membatasi cakupan akses berkas.",
            ),
            owasp="A01:2021 Broken Access Control",
            cwe="CWE-22",
            capec="CAPEC-126",
            references=(
                "OWASP Path Traversal Prevention",
                "OWASP File System Access Control Guidance",
            ),
        ),
    ),
    (
        ("rce", "remote code execution", "command injection", "os command", "code injection"),
        RemediationEntry(
            name="Remote Code Execution / Command Injection",
            steps=(
                "Hilangkan pemanggilan shell dinamis dan gunakan API berparameter tanpa interpretasi shell.",
                "Validasi input dengan allowlist ketat untuk argumen yang sah saja.",
                "Jalankan komponen rentan dengan privilege minimum di dalam kontainer atau sandbox terisolasi.",
                "Terapkan patch terbaru pada runtime, library, dan dependensi yang terdampak.",
                "Aktifkan monitoring eksekusi proses dan blokir biner yang tidak dikenal.",
            ),
            owasp="A03:2021 Injection",
            cwe="CWE-78",
            capec="CAPEC-248",
            references=(
                "OWASP OS Command Injection Defense Cheat Sheet",
                "OWASP Code Injection Prevention",
            ),
        ),
    ),
    (
        ("ssrf", "server side request forgery", "server-side request forgery"),
        RemediationEntry(
            name="Server-Side Request Forgery (SSRF)",
            steps=(
                "Terapkan allowlist tujuan untuk host, port, dan skema yang diizinkan.",
                "Blokir rentang alamat internal, loopback, dan metadata cloud pada lapisan jaringan.",
                "Validasi serta resolusi DNS dilakukan sekali untuk mencegah rebinding.",
                "Nonaktifkan redirect otomatis dan batasi protokol selain HTTP dan HTTPS.",
                "Jalankan permintaan keluar melalui proxy tersegmentasi dengan kebijakan keluar ketat.",
            ),
            owasp="A10:2021 Server-Side Request Forgery",
            cwe="CWE-918",
            capec="CAPEC-664",
            references=("OWASP Server Side Request Forgery Prevention Cheat Sheet",),
        ),
    ),
    (
        ("xxe", "xml external entity", "xml injection"),
        RemediationEntry(
            name="XML External Entity (XXE)",
            steps=(
                "Nonaktifkan pemrosesan external entity dan DTD pada seluruh parser XML.",
                "Gunakan parser dengan konfigurasi aman secara default dan perbarui ke versi terbaru.",
                "Validasi skema XML masukan dengan XSD yang ketat.",
                "Pertimbangkan format data yang lebih sederhana seperti JSON bila memungkinkan.",
                "Batasi ukuran dan kedalaman dokumen XML untuk mencegah penyalahgunaan entitas.",
            ),
            owasp="A05:2021 Security Misconfiguration",
            cwe="CWE-611",
            capec="CAPEC-201",
            references=("OWASP XML External Entity Prevention Cheat Sheet",),
        ),
    ),
    (
        ("csrf", "cross site request forgery", "cross-site request forgery"),
        RemediationEntry(
            name="Cross-Site Request Forgery (CSRF)",
            steps=(
                "Terapkan anti-CSRF token unik per sesi yang divalidasi pada setiap permintaan yang mengubah state.",
                "Set atribut SameSite pada cookie sesi ke nilai Lax atau Strict.",
                "Verifikasi header Origin dan Referer pada operasi sensitif.",
                "Wajibkan re-autentikasi untuk transaksi berdampak tinggi.",
                "Gunakan metode HTTP yang sesuai dan hindari perubahan state melalui permintaan GET.",
            ),
            owasp="A01:2021 Broken Access Control",
            cwe="CWE-352",
            capec="CAPEC-62",
            references=("OWASP Cross-Site Request Forgery Prevention Cheat Sheet",),
        ),
    ),
    (
        ("authentication bypass", "broken authentication", "weak password", "credential stuffing", "default credential", "default credentials"),
        RemediationEntry(
            name="Broken Authentication",
            steps=(
                "Ganti seluruh kredensial default dan terapkan kebijakan kata sandi yang kuat.",
                "Aktifkan autentikasi multifaktor untuk akun istimewa dan akses sensitif.",
                "Terapkan penguncian akun bertahap serta rate limiting terhadap brute force.",
                "Simpan kata sandi dengan algoritma hashing adaptif bersalt seperti bcrypt atau argon2.",
                "Kelola sesi dengan token acak yang aman, kedaluwarsa, dan diinvalidasi saat logout.",
            ),
            owasp="A07:2021 Identification and Authentication Failures",
            cwe="CWE-287",
            capec="CAPEC-115",
            references=(
                "OWASP Authentication Cheat Sheet",
                "OWASP Credential Stuffing Prevention Cheat Sheet",
            ),
        ),
    ),
    (
        ("insecure deserialization", "deserialization", "object injection"),
        RemediationEntry(
            name="Insecure Deserialization",
            steps=(
                "Hindari deserialisasi data tidak tepercaya dan utamakan format data tanpa eksekusi objek.",
                "Terapkan validasi integritas dengan tanda tangan digital pada payload terserialisasi.",
                "Gunakan allowlist tipe yang diizinkan selama deserialisasi.",
                "Jalankan proses deserialisasi dengan privilege minimum dan isolasi.",
                "Perbarui library serialisasi serta pantau pemanggilan gadget berbahaya.",
            ),
            owasp="A08:2021 Software and Data Integrity Failures",
            cwe="CWE-502",
            capec="CAPEC-586",
            references=("OWASP Deserialization Cheat Sheet",),
        ),
    ),
    (
        ("security misconfiguration", "misconfiguration", "directory listing", "default configuration", "verbose error"),
        RemediationEntry(
            name="Security Misconfiguration",
            steps=(
                "Terapkan baseline hardening dan nonaktifkan fitur, port, serta layanan yang tidak digunakan.",
                "Hapus akun, sampel, dan dokumentasi default dari lingkungan produksi.",
                "Matikan directory listing dan pesan error verbose kepada pengguna akhir.",
                "Terapkan header keamanan respons dan konfigurasi TLS yang kuat.",
                "Otomasikan pemeriksaan konfigurasi secara berkala di seluruh lingkungan.",
            ),
            owasp="A05:2021 Security Misconfiguration",
            cwe="CWE-16",
            capec="CAPEC-1",
            references=("OWASP Security Misconfiguration Guidance",),
        ),
    ),
    (
        ("information disclosure", "sensitive data exposure", "info leak", "phpinfo", "version disclosure", "verbose banner"),
        RemediationEntry(
            name="Information Disclosure",
            steps=(
                "Hapus endpoint diagnostik seperti phpinfo dan halaman status dari produksi.",
                "Sembunyikan banner versi pada server, framework, dan komponen pihak ketiga.",
                "Sanitasi pesan error dan stack trace agar tidak menampilkan detail internal.",
                "Terapkan kontrol akses pada berkas konfigurasi, backup, dan repositori.",
                "Lakukan inventarisasi komponen serta pantau CVE untuk versi yang terungkap.",
            ),
            owasp="A01:2021 Broken Access Control",
            cwe="CWE-200",
            capec="CAPEC-118",
            references=("OWASP Information Exposure Prevention Guidance",),
        ),
    ),
    (
        ("open redirect", "url redirect", "unvalidated redirect"),
        RemediationEntry(
            name="Open Redirect",
            steps=(
                "Gunakan allowlist tujuan redirect dan tolak URL absolut eksternal.",
                "Petakan tujuan redirect ke identifier internal alih-alih URL mentah dari pengguna.",
                "Validasi serta normalisasi parameter redirect sebelum digunakan.",
                "Tampilkan halaman antara untuk redirect ke domain eksternal.",
                "Catat upaya redirect mencurigakan untuk analisis lebih lanjut.",
            ),
            owasp="A01:2021 Broken Access Control",
            cwe="CWE-601",
            capec="CAPEC-194",
            references=("OWASP Unvalidated Redirects and Forwards Cheat Sheet",),
        ),
    ),
    (
        ("file upload", "unrestricted upload", "arbitrary file upload", "webshell"),
        RemediationEntry(
            name="Unrestricted File Upload",
            steps=(
                "Validasi tipe berkas dengan allowlist ekstensi dan verifikasi magic byte.",
                "Simpan berkas unggahan di luar webroot dan tanpa hak eksekusi.",
                "Ganti nama berkas secara acak serta batasi ukuran dan jumlah unggahan.",
                "Pindai berkas dengan antimalware sebelum disimpan atau diakses.",
                "Sajikan berkas melalui handler terkendali dengan header tipe konten yang benar.",
            ),
            owasp="A04:2021 Insecure Design",
            cwe="CWE-434",
            capec="CAPEC-650",
            references=("OWASP File Upload Cheat Sheet",),
        ),
    ),
    (
        ("ssl", "tls", "weak cipher", "expired certificate", "cryptographic failure", "weak encryption"),
        RemediationEntry(
            name="Cryptographic Failures",
            steps=(
                "Nonaktifkan protokol dan cipher suite lemah serta wajibkan TLS versi modern.",
                "Gunakan sertifikat valid dengan rantai tepercaya dan rotasi berkala.",
                "Terapkan HSTS dan enkripsi data sensitif saat transit maupun saat disimpan.",
                "Kelola kunci kriptografi secara aman dengan rotasi dan pemisahan peran.",
                "Hindari algoritma usang dan gunakan primitif kriptografi yang teruji.",
            ),
            owasp="A02:2021 Cryptographic Failures",
            cwe="CWE-327",
            capec="CAPEC-217",
            references=("OWASP Transport Layer Protection Cheat Sheet",),
        ),
    ),
)


_GENERIC_ENTRY = RemediationEntry(
    name="Rekomendasi Umum",
    steps=(
        "Validasi dan sanitasi seluruh input mengikuti prinsip allowlist.",
        "Terapkan kontrol akses deny by default pada seluruh fungsi dan sumber daya.",
        "Perbarui komponen serta dependensi ke versi yang telah dipatch.",
        "Aktifkan logging, monitoring, dan deteksi anomali pada perilaku aplikasi.",
        "Lakukan pengujian keamanan berkala dan tinjau ulang konfigurasi hardening.",
    ),
    owasp="OWASP Top 10 2021",
    cwe="CWE-693",
    capec="CAPEC-1000",
    references=("OWASP Application Security Verification Standard (ASVS)",),
)


def resolve(finding_name: str) -> RemediationMatch:
    normalized = finding_name.lower().strip()
    for keywords, entry in _KNOWLEDGE_BASE:
        for keyword in keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", normalized) or keyword in normalized:
                return RemediationMatch(entry=entry, matched_keyword=keyword)
    return RemediationMatch(entry=_GENERIC_ENTRY, matched_keyword="")


def catalog() -> tuple[str, ...]:
    return tuple(entry.name for _, entry in _KNOWLEDGE_BASE)
