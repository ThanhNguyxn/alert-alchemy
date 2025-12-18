"""GUI launcher for Alert Alchemy using pywebview.

Opens the web game in a native window without needing a browser.
"""

import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path


def find_web_folder() -> Path:
    """Find the web folder with game assets."""
    # Try relative to this file (dev mode)
    module_dir = Path(__file__).parent
    
    # Check for bundled assets (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)  # type: ignore
        web_path = base_path / 'web'
        if web_path.exists():
            return web_path
    
    # Dev mode - look for web folder
    candidates = [
        module_dir.parent.parent / 'web',  # src/alert_alchemy/../../web
        Path.cwd() / 'web',
    ]
    
    for path in candidates:
        if (path / 'index.html').exists():
            return path
    
    raise FileNotFoundError("Could not find web folder with game assets")


def start_server(web_folder: Path, port: int) -> socketserver.TCPServer:
    """Start a local HTTP server serving the web folder."""
    os.chdir(web_folder)
    
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # Suppress logs
    
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    return server


def find_free_port() -> int:
    """Find a free port to bind the server."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def main():
    """Launch the Alert Alchemy GUI."""
    try:
        import webview
    except ImportError:
        print("Error: pywebview is not installed.")
        print("Install it with: pip install pywebview")
        print("Or use the browser version at: https://thanhnguyxn.github.io/alert-alchemy/")
        sys.exit(1)
    
    try:
        web_folder = find_web_folder()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run from the project root or ensure web assets are bundled.")
        sys.exit(1)
    
    # Ensure incidents.json exists
    incidents_file = web_folder / 'data' / 'incidents.json'
    if not incidents_file.exists():
        print("Warning: incidents.json not found. Running export script...")
        try:
            import subprocess
            subprocess.run([sys.executable, 'scripts/export_web_data.py'], check=True)
        except Exception:
            pass  # Continue anyway, game may show empty
    
    # Start local server
    port = find_free_port()
    server = start_server(web_folder, port)
    
    try:
        # Create window
        window = webview.create_window(
            title='🧪 Alert Alchemy',
            url=f'http://127.0.0.1:{port}/index.html',
            width=1280,
            height=720,
            resizable=True,
            min_size=(800, 600),
        )
        
        # Start webview (blocking)
        webview.start()
        
    finally:
        server.shutdown()


if __name__ == '__main__':
    main()
