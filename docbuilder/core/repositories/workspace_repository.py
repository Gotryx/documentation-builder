"""
Implementação de persistência para o Workspace (Portfólio de Projetos) utilizando arquivos YAML.
Lida com a conversão de modelos de domínio de Workspace para o arquivo workspace.yaml.
"""

import yaml
from pathlib import Path
from docbuilder.core.domain.workspace import Workspace
from docbuilder.core.domain.interfaces import IWorkspaceRepository


class WorkspaceRepository(IWorkspaceRepository):
    """
    Implementação concreta do IWorkspaceRepository para gerenciar o catálogo
    de projetos utilizando o arquivo workspace.yaml.
    """

    def save(self, workspace: Workspace, destination_path: Path) -> None:
        """Salva a lista de projetos do workspace no arquivo workspace.yaml."""
        if not destination_path.exists():
            destination_path.mkdir(parents=True, exist_ok=True)

        workspace_file = destination_path / "workspace.yaml"
        
        data = {
            "name": workspace.name,
            "project_paths": workspace.project_paths,
            "global_settings": workspace.global_settings
        }

        with open(workspace_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def load(self, destination_path: Path) -> Workspace:
        """Carrega e reconstrói o Workspace a partir do workspace.yaml."""
        workspace_file = destination_path / "workspace.yaml"
        
        # Se não existir, retorna um workspace padrão em branco
        if not workspace_file.exists():
            return Workspace()

        with open(workspace_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Erro de sintaxe no arquivo workspace.yaml: {e}")

        return Workspace(
            name=data.get("name", "GoTryx Documentation Platform"),
            project_paths=data.get("project_paths", []),
            global_settings=data.get("global_settings", {})
        )
