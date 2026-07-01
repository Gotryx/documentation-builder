"""
Testes unitários e de integração para o Workspace (Portfólio de Projetos).
"""

import tempfile
from pathlib import Path
from docbuilder.core.domain.workspace import Workspace
from docbuilder.core.repositories.workspace_repository import WorkspaceRepository
from docbuilder.core.services.workspace_services import (
    LoadWorkspaceUseCase, SaveWorkspaceUseCase, RegisterProjectInWorkspaceUseCase
)


def test_workspace_domain_registration() -> None:
    ws = Workspace(name="GoTryx Docs")
    assert len(ws.project_paths) == 0

    proj_dir = Path("/mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/projeto_a")
    ws.register_project(proj_dir)
    assert len(ws.project_paths) == 1
    assert ws.project_paths[0] == str(proj_dir.resolve())

    # Cadastra duplicado (deve ignorar)
    ws.register_project(proj_dir)
    assert len(ws.project_paths) == 1

    # Desvincula
    ws.unregister_project(proj_dir)
    assert len(ws.project_paths) == 0


def test_workspace_persistence_and_use_cases() -> None:
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        repo = WorkspaceRepository()

        # Caso de Uso: Save e Load
        ws = Workspace(name="Portfolio Gotryx Testing")
        ws.register_project(temp_dir / "projeto_1")
        ws.register_project(temp_dir / "projeto_2")

        save_use_case = SaveWorkspaceUseCase(repo)
        save_use_case.execute(ws, temp_dir)

        assert (temp_dir / "workspace.yaml").exists()

        load_use_case = LoadWorkspaceUseCase(repo)
        loaded_ws = load_use_case.execute(temp_dir)

        assert loaded_ws.name == "Portfolio Gotryx Testing"
        assert len(loaded_ws.project_paths) == 2
        assert str((temp_dir / "projeto_1").resolve()) in loaded_ws.project_paths

        # Caso de Uso: Registrar novo projeto
        register_use_case = RegisterProjectInWorkspaceUseCase(repo)
        updated_ws = register_use_case.execute(temp_dir / "projeto_3", temp_dir)
        assert len(updated_ws.project_paths) == 3
        assert str((temp_dir / "projeto_3").resolve()) in updated_ws.project_paths
