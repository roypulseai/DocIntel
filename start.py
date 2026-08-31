#!/usr/bin/env python3
"""
DocIntel self-managed launcher (cross-platform).

Power users who prefer running a single command can call:
    python start.py [start|stop]

This wraps the .bat / .command / .sh logic so every platform shares
one implementation.
"""
import os
import subprocess
import sys
import time
import webbrowser
import platform
import shutil

WEB_PORT = "8501"
URL = f"http://localhost:{WEB_PORT}"


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _python() -> str:
    return sys.executable


def ensure_python() -> bool:
    if not _run([_python(), "--version"]):
        print("[ERROR] Python 3 not found. See README for install instructions.")
        return False
    return True


def ensure_deps() -> bool:
    mods = ["streamlit", "langchain_groq", "langgraph", "spacy", "sklearn"]
    if all(_run([_python(), "-c", f"import {m}"]) for m in mods):
        print("[OK] Dependencies already installed.")
        return True
    print("Installing dependencies (first run may take a few minutes)...")
    if not _run([_python(), "-m", "pip", "install", "-r", "requirements.txt"]):
        print("[ERROR] Dependency install failed. Run: python -m pip install -r requirements.txt")
        return False
    return True


def ensure_spacy() -> bool:
    if _run([_python(), "-c", "import spacy; spacy.load('en_core_web_sm')"]):
        print("[OK] spaCy model ready.")
        return True
    print("Downloading spaCy NER model (one time, ~40 MB)...")
    if not _run([_python(), "-m", "spacy", "download", "en_core_web_sm"]):
        print("[ERROR] spaCy model download failed.")
        return False
    return True


def ensure_env() -> None:
    if os.environ.get("GROQ_API_KEY") or os.path.exists(".env"):
        return
    print("\nFirst-time setup: you need a free API key.")
    print("It takes 60 seconds at https://console.groq.com")
    key = input("  Paste your Groq API key (starts with gsk_): ").strip()
    if key:
        with open(".env", "w") as f:
            f.write(f"GROQ_API_KEY={key}\nGROQ_MODEL=llama-3.3-70b-versatile\n")
        print("[OK] Saved API key to .env")


def start() -> None:
    if not all([ensure_python(), ensure_deps(), ensure_spacy()]):
        input("Press Enter to exit...")
        sys.exit(1)
    ensure_env()

    env = dict(os.environ)
    if os.path.exists(".env"):
        for line in open(".env"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k, v)

    print("\nStarting DocIntel... opening browser in a moment. Press Ctrl+C to stop.\n")
    proc = subprocess.Popen(
        [_python(), "-m", "streamlit", "run", "app.py", "--server.port", WEB_PORT],
        env=env,
    )
    time.sleep(4)
    webbrowser.open(URL)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nDocIntel stopped.")


def stop() -> None:
    from docintel.tools.stop_server import stop_streamlit
    stop_streamlit()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "stop":
        stop()
    else:
        start()
