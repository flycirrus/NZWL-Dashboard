#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NZWL Payment Planning Dashboard – Setup- und Systempruefungs-Skript
===================================================================

Dieses Skript bereitet einen Windows- oder Linux-Server fuer die
Installation des NZWL Streamlit-Dashboards vor.

Funktionen:
  1. Systemcheck (OS, Python-Version, RAM, Disk, wichtige Ports)
  2. Anlegen einer virtuellen Umgebung (./venv)
  3. Installation aller Python-Module aus requirements.txt
  4. Optionaler Verbindungstest zu MariaDB

Ausfuehrung:
  python setup_nzwl.py                 -> Systemcheck + venv + Pakete
  python setup_nzwl.py --check-only    -> Nur Systemcheck
  python setup_nzwl.py --no-install    -> venv anlegen, keine Pakete
  python setup_nzwl.py --db-test       -> Zusaetzlich DB-Verbindung pruefen

Getestet mit Python 3.10, 3.11, 3.12.
Standardbibliothek only – keine externen Abhaengigkeiten noetig.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

MIN_PYTHON = (3, 10)
MIN_RAM_GB = 4
MIN_DISK_GB = 10
REQUIRED_PORTS = [8501]            # Streamlit-Standardport
OPTIONAL_PORTS = [3306, 80, 443]   # MariaDB, HTTP, HTTPS
VENV_DIR = Path(__file__).resolve().parent / "venv"
PROJECT_DIR = Path(__file__).resolve().parent
REQUIREMENTS = PROJECT_DIR / "requirements.txt"

# ANSI-Farben (werden auf Windows automatisch deaktiviert, falls nicht unterstuetzt)
class C:
    OK = "\033[92m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    INFO = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if platform.system() == "Windows":
        # Windows 10+ Terminals unterstuetzen ANSI in der Regel
        return os.environ.get("WT_SESSION") is not None or os.environ.get("TERM") is not None
    return sys.stdout.isatty()


if not _supports_color():
    for attr in ("OK", "WARN", "ERR", "INFO", "BOLD", "END"):
        setattr(C, attr, "")


def log_ok(msg: str) -> None:
    print(f"{C.OK}[OK]{C.END}   {msg}")


def log_warn(msg: str) -> None:
    print(f"{C.WARN}[WARN]{C.END} {msg}")


def log_err(msg: str) -> None:
    print(f"{C.ERR}[FAIL]{C.END} {msg}")


def log_info(msg: str) -> None:
    print(f"{C.INFO}[INFO]{C.END} {msg}")


def section(title: str) -> None:
    line = "=" * 70
    print(f"\n{C.BOLD}{line}\n {title}\n{line}{C.END}")


# ---------------------------------------------------------------------------
# Systemchecks
# ---------------------------------------------------------------------------

def check_os() -> dict:
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }
    log_ok(f"OS: {info['system']} {info['release']} ({info['machine']})")
    if info["system"] not in ("Windows", "Linux", "Darwin"):
        log_warn(f"Nicht offiziell unterstuetzt: {info['system']}")
    return info


def check_python() -> bool:
    v = sys.version_info
    log_info(f"Python-Interpreter: {sys.executable}")
    if (v.major, v.minor) < MIN_PYTHON:
        log_err(
            f"Python {v.major}.{v.minor}.{v.micro} gefunden – "
            f"benoetigt wird {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+"
        )
        return False
    log_ok(f"Python {v.major}.{v.minor}.{v.micro}")
    return True


def check_pip() -> bool:
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "--version"],
            stderr=subprocess.STDOUT, text=True,
        )
        log_ok(f"pip verfuegbar: {out.strip()}")
        return True
    except Exception as exc:
        log_err(f"pip nicht verfuegbar: {exc}")
        return False


def check_venv_module() -> bool:
    try:
        subprocess.check_output(
            [sys.executable, "-m", "venv", "--help"],
            stderr=subprocess.STDOUT,
        )
        log_ok("venv-Modul verfuegbar")
        return True
    except Exception:
        log_err(
            "venv-Modul fehlt. Linux: 'sudo apt install python3-venv' ausfuehren."
        )
        return False


def check_disk() -> bool:
    total, used, free = shutil.disk_usage(PROJECT_DIR)
    free_gb = free / (1024 ** 3)
    total_gb = total / (1024 ** 3)
    msg = f"Disk: {free_gb:.1f} GB frei / {total_gb:.1f} GB gesamt"
    if free_gb < MIN_DISK_GB:
        log_err(f"{msg} – weniger als {MIN_DISK_GB} GB frei")
        return False
    log_ok(msg)
    return True


def check_ram() -> bool:
    ram_gb = None
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo", "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_gb = kb / (1024 ** 2)
                        break
        elif platform.system() == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_gb = stat.ullTotalPhys / (1024 ** 3)
        elif platform.system() == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
            ram_gb = int(out.strip()) / (1024 ** 3)
    except Exception as exc:
        log_warn(f"RAM konnte nicht ermittelt werden: {exc}")
        return True  # nicht blockierend

    if ram_gb is None:
        log_warn("RAM-Groesse unbekannt")
        return True
    if ram_gb < MIN_RAM_GB:
        log_warn(f"RAM: nur {ram_gb:.1f} GB (empfohlen: {MIN_RAM_GB} GB+)")
        return True
    log_ok(f"RAM: {ram_gb:.1f} GB")
    return True


def _port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) != 0


def check_ports() -> bool:
    all_ok = True
    for port in REQUIRED_PORTS:
        if _port_free(port):
            log_ok(f"Port {port} ist frei")
        else:
            log_err(f"Port {port} ist belegt – Streamlit wird nicht starten koennen")
            all_ok = False
    for port in OPTIONAL_PORTS:
        if _port_free(port):
            log_info(f"Optionaler Port {port} ist frei")
        else:
            log_info(f"Optionaler Port {port} ist belegt (ggf. bereits genutzt)")
    return all_ok


def check_external_tools() -> None:
    """Sucht nach wichtigen externen Tools (nicht blockierend)."""
    for tool in ("git", "nginx", "mysql", "mariadb"):
        path = shutil.which(tool)
        if path:
            log_ok(f"Gefunden: {tool} -> {path}")
        else:
            log_info(f"Nicht installiert: {tool} (optional)")


def run_system_check() -> bool:
    section("1) Systemcheck")
    results = [
        check_python(),
        check_pip(),
        check_venv_module(),
        check_disk(),
        check_ram(),
        check_ports(),
    ]
    check_os()
    check_external_tools()
    ok = all(results)
    print()
    if ok:
        log_ok("Systemcheck bestanden.")
    else:
        log_err("Systemcheck fehlgeschlagen – bitte Punkte oben beheben.")
    return ok


# ---------------------------------------------------------------------------
# Virtuelle Umgebung & Pakete
# ---------------------------------------------------------------------------

def venv_python(venv_path: Path) -> Path:
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def create_venv() -> bool:
    section("2) Virtuelle Umgebung")
    if VENV_DIR.exists():
        log_info(f"venv existiert bereits: {VENV_DIR}")
        return True
    log_info(f"Lege venv an: {VENV_DIR}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        log_ok("venv erstellt")
        return True
    except subprocess.CalledProcessError as exc:
        log_err(f"venv-Erstellung fehlgeschlagen: {exc}")
        return False


def install_requirements() -> bool:
    section("3) Python-Module installieren")
    if not REQUIREMENTS.exists():
        log_err(f"requirements.txt nicht gefunden: {REQUIREMENTS}")
        return False
    py = venv_python(VENV_DIR)
    if not py.exists():
        log_err(f"Python der venv nicht gefunden: {py}")
        return False

    try:
        log_info("pip aktualisieren ...")
        subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip"])
        log_info(f"Installiere aus {REQUIREMENTS.name} ...")
        subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        log_ok("Alle Pakete installiert")
        return True
    except subprocess.CalledProcessError as exc:
        log_err(f"Installation fehlgeschlagen: {exc}")
        return False


# ---------------------------------------------------------------------------
# Optional: MariaDB-Verbindungstest
# ---------------------------------------------------------------------------

def db_test() -> bool:
    section("4) MariaDB-Verbindungstest")
    host = os.environ.get("NZWL_DB_HOST", "127.0.0.1")
    port = int(os.environ.get("NZWL_DB_PORT", "3306"))
    try:
        with socket.create_connection((host, port), timeout=3):
            log_ok(f"MariaDB erreichbar unter {host}:{port}")
            return True
    except OSError as exc:
        log_warn(f"MariaDB nicht erreichbar ({host}:{port}): {exc}")
        return False


# ---------------------------------------------------------------------------
# Zusammenfassung / Next steps
# ---------------------------------------------------------------------------

def print_next_steps() -> None:
    section("Naechste Schritte")
    activate = (
        r"venv\Scripts\activate"
        if platform.system() == "Windows"
        else "source venv/bin/activate"
    )
   # print(f"  1. venv aktivieren:        {activate}")
    #print(f"  2. Dashboard starten:      streamlit run dashboard/app.py")
    #print(f"  3. Im Browser oeffnen:     http://<server-ip>:8501")
    print()
    log_info("Bei Fragen an den Installateur wenden.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="NZWL Setup- und Pruefskript")
    parser.add_argument("--check-only", action="store_true",
                        help="Nur Systemcheck, keine Installation")
    parser.add_argument("--no-install", action="store_true",
                        help="venv anlegen, aber Pakete nicht installieren")
    parser.add_argument("--db-test", action="store_true",
                        help="Zusaetzlich MariaDB-Verbindung testen")
    args = parser.parse_args()

    section(f"NZWL Payment Planning Dashboard – Server-Setup")
    log_info(f"Projektverzeichnis: {PROJECT_DIR}")

    sys_ok = run_system_check()

    if args.check_only:
        return 0 if sys_ok else 1

    if not sys_ok:
        log_err("Abbruch wegen fehlgeschlagenem Systemcheck.")
        return 1

    if not create_venv():
        return 2

    if not args.no_install:
        if not install_requirements():
            return 3

    if args.db_test:
        db_test()

    print_next_steps()
    log_ok("Setup abgeschlossen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
