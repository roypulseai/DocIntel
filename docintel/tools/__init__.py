"""Cross-platform helper to stop a running DocIntel/Streamlit server."""
import signal
import subprocess
import sys
import os
import platform

PORT = "8501"


def _find_pids_by_port(port: str):
    """Return a list of PIDs listening on *port*."""
    sysname = platform.system()
    pids = []
    if sysname == "Windows":
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        ).stdout
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pids.append(line.split()[-1])
    else:
        # lsof works on macOS and most Linux
        try:
            out = subprocess.run(
                ["lsof", "-t", f"-i:{port}"], capture_output=True, text=True
            ).stdout
            pids = [p for p in out.split() if p.strip()]
        except FileNotFoundError:
            # Fallback: use fuser
            try:
                out = subprocess.run(
                    ["fuser", f"{port}/tcp"], capture_output=True, text=True
                ).stdout
                pids = [p for p in out.split() if p.strip()]
            except FileNotFoundError:
                pass
    return pids


def stop_streamlit() -> None:
    sysname = platform.system()
    pids = _find_pids_by_port(PORT)
    if not pids:
        print("DocIntel is not running (no process found on port 8501).")
        return

    for pid in pids:
        try:
            if sysname == "Windows":
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               capture_output=True)
            else:
                os.kill(int(pid), signal.SIGTERM)
            print(f"Stopped process {pid}")
        except Exception as e:
            print(f"Could not stop {pid}: {e}")
    print("DocIntel stopped.")


if __name__ == "__main__":
    stop_streamlit()
