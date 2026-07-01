"""
Servidor HTTP integrado para visualização da documentação compilada (Wiki Local).
Roda em segundo plano (thread separada) servindo os arquivos estáticos gerados em HTML/CSS.
"""

import socket
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional


class WikiHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handler customizado para silenciar logs excessivos no terminal e garantir tipos MIME corretos."""

    def log_message(self, format: str, *args) -> None:
        # Silencia logs no terminal para não sobrecarregar o console da UI
        pass


class WikiServer:
    """
    Servidor HTTP leve para hospedar localmente a documentação HTML da GoTryx.
    """

    def __init__(self) -> None:
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._directory: Optional[Path] = None
        self._port: int = 8080
        self._is_running: bool = False

    def start(self, directory: Path, port: int = 8080) -> bool:
        """Inicia o servidor HTTP em segundo plano se ele não estiver ativo."""
        if self._is_running:
            return True

        if not directory.exists():
            raise FileNotFoundError(
                f"Diretório de documentação não encontrado: {directory}"
            )

        self._directory = directory
        self._port = port

        # Procura uma porta livre caso a padrão de trabalho esteja ocupada
        self._port = self._find_free_port(self._port)

        # Configura o handler para servir a partir do diretório correto
        # No Python 3.7+, SimpleHTTPRequestHandler aceita o parâmetro directory
        class Handler(WikiHTTPRequestHandler):
            def __init__(self, request, client_address, server):
                super().__init__(
                    request, client_address, server, directory=str(directory)
                )

        try:
            self._server = HTTPServer(("127.0.0.1", self._port), Handler)
            self._is_running = True

            # Inicia o loop em uma thread
            self._thread = threading.Thread(target=self._run_server, daemon=True)
            self._thread.start()
            return True
        except Exception:
            self._is_running = False
            return False

    def stop(self) -> None:
        """Encerra o servidor de forma limpa."""
        if not self._is_running or not self._server:
            return

        # Para o loop do servidor
        self._server.shutdown()
        # Fecha o socket
        self._server.server_close()

        if self._thread:
            self._thread.join(timeout=2.0)

        self._is_running = False
        self._server = None
        self._thread = None

    def is_running(self) -> bool:
        return self._is_running

    def get_url(self) -> str:
        """Retorna o endereço local do servidor Wiki."""
        if self._is_running:
            return f"http://127.0.0.1:{self._port}"
        return ""

    def _run_server(self) -> None:
        if self._server:
            self._server.serve_forever()

    def _find_free_port(self, start_port: int) -> int:
        """Tenta ligar na porta especificada; se ocupada, incrementa até achar uma livre."""
        port = start_port
        while port < start_port + 100:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", port))
                    return port
                except socket.error:
                    port += 1
        return start_port


pre_push = True
