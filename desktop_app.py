# desktop_app.py — minimal wrapper to run Streamlit app in a desktop window
import subprocess, sys, time, os, socket, webbrowser

APP_TITLE = "Aircraft & Multirotor Calculator"
SCRIPT_BASENAME = "drone_app.py"

def resource_path(rel_path: str) -> str:
    # when frozen by PyInstaller, files are unpacked to _MEIPASS
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)

def script_path() -> str:
    # prefer external file next to the EXE (easy to update without rebuild)
    here = os.path.dirname(os.path.abspath(getattr(sys, "_MEIPASS", sys.argv[0])))
    external = os.path.join(here, SCRIPT_BASENAME)
    return external if os.path.exists(external) else resource_path(SCRIPT_BASENAME)

def find_free_port(start=8501, end=8999) -> int:
    for p in range(start, end + 1):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("No free port found")

def run_streamlit(app_path: str, port: int) -> subprocess.Popen:
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless=true", f"--server.port={port}",
        "--server.fileWatcherType=none", "--browser.gatherUsageStats=false",
    ]
    return subprocess.Popen(cmd, env=env)

def wait_until_up(port: int, timeout: float = 60.0) -> bool:
    import http.client
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            conn.request("GET", "/")
            if conn.getresponse().status in (200, 302, 403, 404):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

def main():
    app = script_path()
    port = find_free_port()
    proc = run_streamlit(app, port)

    if not wait_until_up(port):
        try: proc.terminate()
        except Exception: pass
        raise SystemExit("Streamlit server did not start. Check app/logs.")

    url = f"http://127.0.0.1:{port}"
    # Try native webview if WebView2 exists; otherwise open default browser.
    try:
        import webview  # optional
        window = webview.create_window(APP_TITLE, url, width=1200, height=800)
        webview.start()
    except Exception:
        webbrowser.open(url)
        proc.wait()  # keep process alive while browser is open

    try: proc.terminate()
    except Exception: pass

if __name__ == "__main__":
    main()
