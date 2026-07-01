"""
Casos de Uso (Use Cases) e Serviços de Gerenciamento do Workspace (Portfólio de Projetos).
Permite listar, alternar e registrar novos projetos no painel do Workspace.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from docbuilder.core.domain.workspace import Workspace
from docbuilder.core.domain.interfaces import IWorkspaceRepository


class LoadWorkspaceUseCase:
    """Caso de uso para carregar o Workspace contendo o portfólio de projetos."""

    def __init__(self, repository: IWorkspaceRepository) -> None:
        self._repository = repository

    def execute(self, workspace_dir: Path) -> Workspace:
        return self._repository.load(workspace_dir)


class SaveWorkspaceUseCase:
    """Caso de uso para salvar o Workspace."""

    def __init__(self, repository: IWorkspaceRepository) -> None:
        self._repository = repository

    def execute(self, workspace: Workspace, workspace_dir: Path) -> None:
        errors = workspace.validate()
        if errors:
            raise ValueError(f"O workspace possui inconsistências impeditivas: {', '.join(errors)}")
        self._repository.save(workspace, workspace_dir)


class RegisterProjectInWorkspaceUseCase:
    """Caso de uso para registrar um novo projeto ou existente no Workspace."""

    def __init__(self, repository: IWorkspaceRepository) -> None:
        self._repository = repository

    def execute(self, project_dir: Path, workspace_dir: Path) -> Workspace:
        workspace = self._repository.load(workspace_dir)
        workspace.register_project(project_dir)
        self._repository.save(workspace, workspace_dir)
        return workspace
