"""
Entidades de domínio do Workspace (Portfólio de Documentação) do GoTryx.
Permite o gerenciamento de múltiplos projetos de documentação a partir de um único contexto de trabalho.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class Workspace:
    """
    Entidade de domínio que representa o portfólio de documentação corporativa da empresa.
    Mantém uma lista de caminhos de projetos registrados e configurações globais de sincronização.
    """

    name: str = "GoTryx Documentation Platform"
    project_paths: List[str] = field(
        default_factory=list
    )  # caminhos de pastas locais de projetos
    global_settings: Dict[str, Any] = field(default_factory=dict)

    def register_project(self, project_dir: Path) -> None:
        """Cadastra um projeto no catálogo se ele ainda não estiver presente."""
        proj_path_str = str(project_dir.resolve())
        if proj_path_str not in self.project_paths:
            self.project_paths.append(proj_path_str)

    def unregister_project(self, project_dir: Path) -> bool:
        """Remove um projeto do catálogo do workspace."""
        proj_path_str = str(project_dir.resolve())
        if proj_path_str in self.project_paths:
            self.project_paths.remove(proj_path_str)
            return True
        return False

    def validate(self) -> List[str]:
        """Realiza validações lógicas de consistência do workspace."""
        errors = []
        if not self.name.strip():
            errors.append("O nome do workspace não pode estar vazio.")
        return errors
