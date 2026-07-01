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
from docbuilder.core.services.build_services import ValidateProjectUseCase, BuildProjectUseCase


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
            target_dir=temp_dir
        )

        assert (temp_dir / "manifest.yaml").exists()
        assert (temp_dir / "documents" / "introducao.md").exists()

        # 3. Adiciona um arquivo Markdown extra para testar o validador de links locais
        doc2_path = temp_dir / "documents" / "arquitetura.md"
        with open(doc2_path, "w", encoding="utf-8") as f:
            # Insere um link correto e um link quebrado para validação
            f.write("# Arquitetura\n\nLink correto para [Introdução](introducao.md) e link quebrado [Inexistente](invalido.md).")

        # Atualiza o DTO manualmente simulando ação na árvore do usuário
        # Para isso, adiciona o novo documento no Capítulo 1
        cap_dto = project_dto.volumes[0].parts[0].chapters[0]
        cap_dto.documents.append(
            from_doc_dto := HtmlExporter().get_supported_format()  # apenas pegando uma string de referência, mas vamos definir diretamente
        )
        # Vamos remover o placeholder inserido incorretamente e colocar o DTO estruturado correto
        cap_dto.documents.pop()
        from uuid import uuid4
        from docbuilder.core.services.dtos import DocumentDTO
        cap_dto.documents.append(DocumentDTO(
            id=str(uuid4()),
            title="Arquitetura do Core",
            file_path="documents/arquitetura.md",
            format="markdown"
        ))

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

        build_use_case = BuildProjectUseCase(temp_repo, builder, [md_exporter, html_exporter])
        build_result = build_use_case.execute(project_dto, temp_dir, ["md", "html"])

        # O build deve ser bem-sucedido
        assert build_result.success is True
        assert len(build_result.output_files) == 2
        
        # Garante que os arquivos físicos de saída foram criados na pasta dist
        dist_dir = temp_dir / "dist"
        assert dist_dir.exists()
        
        generated_files = [Path(fp).name for fp in build_result.output_files]
        assert any("Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".md") for fn in generated_files)
        assert any("Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".html") for fn in generated_files)
        assert any("Manual_de_Engenharia_GoTryx" in fn and fn.endswith(".css") for fn in [f.name for f in dist_dir.glob("*.css")])
