"""
Testes de integração para o pipeline de build, validação e exportação.
Valida o comportamento dos Use Cases integrados com arquivos no disco.
"""

import tempfile
from pathlib import Path
from docbuilder.core.repositories.project_repository import ProjectRepository
from docbuilder.core.repositories.template_repository import TemplateRepository
from docbuilder.core.builders.document_builder import DocumentBuilder
from docbuilder.core.exporters.markdown_exporter import MarkdownExporter
from docbuilder.core.exporters.html_exporter import HtmlExporter
from docbuilder.core.services.project_services import CreateProjectUseCase
from docbuilder.core.services.build_services import (
    ValidateProjectUseCase,
    BuildProjectUseCase,
)


def test_full_build_pipeline() -> None:
    # 1. Cria diretório de testes temporário
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Repositórios
        proj_repo = ProjectRepository()
        temp_repo = TemplateRepository()

        # 2. Executa caso de uso para criar o projeto
        create_use_case = CreateProjectUseCase(proj_repo)
        project_dto = create_use_case.execute(
            name="Manual de Engenharia GoTryx",
            author="Equipe GoTryx",
            language="pt-BR",
            template="Corporate",
            target_dir=temp_dir,
        )

        assert (temp_dir / "manifest.yaml").exists()
        assert (temp_dir / "documents" / "introducao.md").exists()

        # 3. Adiciona um arquivo Markdown extra para testar o validador de links locais
        doc2_path = temp_dir / "documents" / "arquitetura.md"
        with open(doc2_path, "w", encoding="utf-8") as f:
            # Insere um link correto e um link quebrado para validação
            f.write(
                "# Arquitetura\n\nLink correto para [Introdução](introducao.md) e link quebrado [Inexistente](invalido.md)."
            )

        # Atualiza o DTO manualmente simulando ação na árvore do usuário
        # Para isso, adiciona o novo documento no Capítulo 1
        cap_dto = project_dto.volumes[0].parts[0].chapters[0]
        from uuid import uuid4
        from docbuilder.core.services.dtos import DocumentDTO

        cap_dto.documents.append(
            DocumentDTO(
                id=str(uuid4()),
                title="Arquitetura do Core",
                file_path="documents/arquitetura.md",
                format="markdown",
            )
        )

        # 4. Executa validação e espera encontrar 1 aviso de link quebrado
        val_use_case = ValidateProjectUseCase(temp_repo)
        val_result = val_use_case.execute(project_dto, temp_dir)

        # Deve estar válido (is_valid=True) pois links locais quebrados geram warnings, não erros impeditivos
        assert val_result.is_valid is True
        assert len(val_result.warnings) >= 1
        assert any("invalido.md" in w for w in val_result.warnings)

        # 5. Executa o build completo para Markdown e HTML
        md_exporter = MarkdownExporter()
        html_exporter = HtmlExporter()
        builder = DocumentBuilder()

        build_use_case = BuildProjectUseCase(
            temp_repo, builder, [md_exporter, html_exporter]
        )
        build_result = build_use_case.execute(project_dto, temp_dir, ["md", "html"])

        # O build deve ser bem-sucedido
        assert build_result.success is True
        assert len(build_result.output_files) == 2

        # Garante que os arquivos físicos de saída foram criados na pasta dist
        dist_dir = temp_dir / "dist"
        assert dist_dir.exists()

        generated_files = [Path(fp).name for fp in build_result.output_files]
        assert any(
            "Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".md")
            for fn in generated_files
        )
        assert any(
            "Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".html")
            for fn in generated_files
        )
        assert any(
            "Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".css")
            for fn in [f.name for f in dist_dir.glob("*.css")]
        )


def test_project_folder_structure_mode() -> None:
    # Testa a criação de projeto e a sincronização no modo "folders" (por pastas)
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        # Cria a árvore física de pastas e arquivos no disco
        (temp_dir / "01-planejamento").mkdir()
        (temp_dir / "02-execucao").mkdir()

        with open(temp_dir / "readme.md", "w", encoding="utf-8") as f:
            f.write("# Raiz\n\nDocumento raiz.")

        with open(
            temp_dir / "01-planejamento" / "requisitos.md", "w", encoding="utf-8"
        ) as f:
            f.write("# Requisitos\n\nRequisitos de software.")

        with open(temp_dir / "02-execucao" / "testes.md", "w", encoding="utf-8") as f:
            f.write("# Testes\n\nCódigo de testes.")

        proj_repo = ProjectRepository()

        # 1. Cria o projeto no modo folders
        create_use_case = CreateProjectUseCase(proj_repo)
        project_dto = create_use_case.execute(
            name="Projeto Estruturado",
            author="Gotryx Dev",
            language="pt-BR",
            template="Corporate",
            target_dir=temp_dir,
            structure_mode="folders",
        )

        assert project_dto.structure_mode == "folders"

        # O projeto deve conter o volume e as partes correspondentes
        assert len(project_dto.volumes) == 1
        vol = project_dto.volumes[0]

        # Partes criadas: "Parte I - Conteúdo Geral" (readme.md na raiz), "Parte 02 - 01 Planejamento" e "Parte 03 - 02 Execucao"
        assert len(vol.parts) == 3

        parts_titles = [p.title for p in vol.parts]
        assert "Parte I - Conteúdo Geral" in parts_titles
        assert "Parte 02 - 01 Planejamento" in parts_titles
        assert "Parte 03 - 02 Execucao" in parts_titles

        # 2. Testa o Sincronizador de Pasta no modo folders
        from docbuilder.core.services.project_services import (
            ProjectMappingHelper,
            SyncFolderFilesUseCase,
        )

        # Adiciona um novo arquivo em subpasta profunda (nível 2)
        (temp_dir / "01-planejamento" / "detalhes").mkdir()
        with open(
            temp_dir / "01-planejamento" / "detalhes" / "design.md",
            "w",
            encoding="utf-8",
        ) as f:
            f.write("# Design\n\nDetalhes de design.")

        # Converte DTO para Entidade
        project_entity = ProjectMappingHelper.dto_to_entity(project_dto)

        # Roda a sincronização
        sync_use_case = SyncFolderFilesUseCase(proj_repo)
        added_titles = sync_use_case.execute(project_entity, temp_dir)

        # O design.md deve ter sido catalogado
        assert "Design" in added_titles

        # Converte de volta para DTO para analisar a árvore atualizada
        updated_dto = ProjectMappingHelper.entity_to_dto(project_entity)

        # Procura a parte do Planejamento
        part_planejamento = next(
            p for p in updated_dto.volumes[0].parts if "01 Planejamento" in p.title
        )

        # O novo capítulo deve ser "Detalhes"
        chapter_titles = [c.title for c in part_planejamento.chapters]
        assert any("Detalhes" in t for t in chapter_titles)

        # O documento dentro de Detalhes deve ser "Design"
        cap_detalhes = next(
            c for c in part_planejamento.chapters if "Detalhes" in c.title
        )
        assert len(cap_detalhes.documents) == 1
        assert cap_detalhes.documents[0].title == "Design"
