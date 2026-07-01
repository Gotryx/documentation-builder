"""
Caso de uso para Sincronização Cloud e Controle de Versão (Git/Nuvem).
Gerencia a conexão com provedores e envia as atualizações de documentação.
"""

from pathlib import Path
from docbuilder.core.domain.interfaces import ICloudStorage


class SyncProjectUseCase:
    """
    Caso de Uso encarregado de conectar e sincronizar fisicamente o repositório
    de documentação com servidores remotos ou repositórios locais do Git.
    """

    def __init__(self, cloud_provider: ICloudStorage) -> None:
        self._provider = cloud_provider

    def execute(self, project_path: Path, credentials: dict) -> bool:
        """ Conecta e executa a sincronização do projeto com o Git/Nuvem."""
        if not self._provider.connect(credentials):
            return False
        
        return self._provider.sync_project(project_path)
