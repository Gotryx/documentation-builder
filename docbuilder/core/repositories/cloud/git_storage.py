"""
Implementação concreta de armazenamento e sincronização baseada no Git CLI.
Permite o controle de versão e publicação remota de projetos do GoTryx.
"""

import subprocess
from pathlib import Path
from typing import Optional
from docbuilder.core.domain.interfaces import ICloudStorage


class GitStorage(ICloudStorage):
    """
    Provedor de controle de versão que utiliza a CLI do Git local.
    Automatiza os commits, tags e pushes das releases de documentação.
    """

    def __init__(self, remote_url: Optional[str] = None) -> None:
        self._remote_url = remote_url
        self._connected = False

    def connect(self, credentials: dict) -> bool:
        """
        No Git, a conexão valida se o executável do git está no PATH
        e se o repositório remoto responde.
        """
        try:
            subprocess.run(
                ["git", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            self._connected = True

            # Se fornecido nas credenciais, atualiza a url do remoto
            if "remote_url" in credentials:
                self._remote_url = credentials["remote_url"]

            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            self._connected = False
            return False

    def sync_project(self, project_path: Path) -> bool:
        """
        Inicializa o git, commita todas as mudanças e adiciona uma tag com a versão.
        """
        if not self._connected:
            raise RuntimeError(
                "Provedor Git não inicializado. Chame 'connect' primeiro."
            )

        try:
            # 1. Verifica se já existe um repo git local. Se não, inicializa
            git_dir = project_path / ".git"
            if not git_dir.exists():
                self._run_git(project_path, ["init"])

            # 2. Configura o remoto se necessário e se configurado
            if self._remote_url:
                # Remove remote antigo se existir para evitar colisão
                self._run_git(project_path, ["remote", "remove", "origin"], check=False)
                self._run_git(
                    project_path, ["remote", "add", "origin", self._remote_url]
                )

            # 3. Adiciona arquivos do projeto (manifesto e subpastas de conteúdo)
            self._run_git(
                project_path, ["add", "manifest.yaml", "documents/", "resources/"]
            )

            # 4. Verifica se há modificações para commitar
            status_res = self._run_git(project_path, ["status", "--porcelain"])
            if status_res.strip():
                # Carrega o manifesto temporariamente para pegar a versão
                import yaml

                manifest_file = project_path / "manifest.yaml"
                version_str = "1.0.0.1"
                if manifest_file.exists():
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        m_data = yaml.safe_load(f) or {}
                        version_str = m_data.get("version", "1.0.0.1")

                # Commita
                msg = f"Release v{version_str} - GoTryx Documentation Platform"
                self._run_git(project_path, ["commit", "-m", msg])

                # Cria tag de versão local
                # Apaga tag antiga de mesmo nome se houver (overwrite local)
                tag_name = f"v{version_str}"
                self._run_git(project_path, ["tag", "-d", tag_name], check=False)
                self._run_git(
                    project_path, ["tag", "-a", tag_name, "-m", f"Versão {version_str}"]
                )

                # 5. Se houver remoto, envia
                if self._remote_url:
                    # Envia ramificação atual (normalmente master ou main)
                    # Descobre ramificação atual
                    branch = self._run_git(
                        project_path, ["rev-parse", "--abbrev-ref", "HEAD"]
                    ).strip()
                    self._run_git(
                        project_path, ["push", "-u", "origin", branch], check=False
                    )
                    self._run_git(
                        project_path, ["push", "origin", "--tags"], check=False
                    )

            return True
        except Exception:
            return False

    def get_provider_name(self) -> str:
        return "git"

    def _run_git(self, cwd: Path, args: list, check: bool = True) -> str:
        cmd = ["git"] + args
        res = subprocess.run(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if check and res.returncode != 0:
            raise RuntimeError(
                f"Comando Git falhou: {' '.join(cmd)}\nErro: {res.stderr.strip()}"
            )
        return res.stdout
