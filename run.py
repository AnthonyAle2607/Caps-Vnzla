"""Application entry point for CAPS VNZLA."""

import socket
from threading import Timer
import webbrowser

from app import create_app

app = create_app()


def available_port(start: int = 5000, stop: int = 5100) -> int:
    for port in range(start, stop):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
            if probe_socket.connect_ex(("127.0.0.1", port)) == 0:
                continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            try:
                server_socket.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No hay puertos disponibles entre 5000 y 5099.")


if __name__ == "__main__":
    port = available_port()
    Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(debug=False, host="127.0.0.1", port=port)

