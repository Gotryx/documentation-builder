"""
Interface de Linha de Comando (CLI) para o GoTryx Documentation Platform.
Permite automação headless total e integração com scripts externos.
Toda saída do processo é formatada em JSON no stdout para facilitar o parsing automático.
"""

import argparse
import json
import sys
from pathlib import Path
from docbuilder.core.repositories.project_repository import ProjectRepository
from docbuilder.core.repositories.template_repository import TemplateRepository
from docbuilder.core.repositories.workspace_repository import WorkspaceRepository
from docbuilder.core.repositories.cloud.git_storage import GitStorage
from docbuilder.core.builders.document_builder import DocumentBuilder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI oficial da GoTryx Documentation Platform para automação headless."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcomandos disponíveis")

    # Comando 'create'
    create_parser = subparsers.add_parser("create", help="Cria um novo projeto de documentação.")
    create_parser.add_argument("--name", required=True, help="Nome do projeto.")
    create_parser.add_argument("--author", required=True, help="Autor da documentação.")
    create_parser.add_argument("--language", default="pt-BR", help="Idioma principal.")
    create_parser.add_argument("--template", default="Corporate", help="Nome do template inicial.")
    create_parser.add_argument("--dir", required=True, help="Diretório onde o projeto será criado.")

    # Comando 'validate'
    validate_parser = subparsers.add_parser("validate", help="Valida a integridade do projeto e links.")
    validate_parser.add_argument("--project", required=True, help="Caminho raiz do projeto.")

    # Comando 'build'
    build_parser = subparsers.add_parser("build", help="Compila e exporta a documentação.")
    build_parser.add_argument("--project", required=True, help="Caminho raiz do projeto.")
    build_parser.add_argument("--formats", default="docx,pdf,html,md", help="Formatos de saída separados por vírgula.")

    # Comando 'import'
    import_parser = subparsers.add_parser("import", help="Importa um arquivo externo para o diretório do projeto.")
    import_parser.add_argument("--file", required=True, help="Caminho do arquivo externo a ser importado.")
    import_parser.add_argument("--project", required=True, help="Caminho raiz do projeto.")

    # Comando 'workspace-list'
    ws_list_parser = subparsers.add_parser("workspace-list", help="Lista todos os projetos cadastrados no Workspace.")
    ws_list_parser.add_argument("--dir", required=True, help="Caminho raiz do workspace.")

    # Comando 'workspace-register'
    ws_reg_parser = subparsers.add_parser("workspace-register", help="Cadastra um projeto existente no Workspace.")
    ws_reg_parser.add_argument("--project", required=True, help="Caminho do projeto.")
    ws_reg_parser.add_argument("--dir", required=True, help="Caminho raiz do workspace.")

    # Comando 'sync'
    sync_parser = subparsers.add_parser("sync", help="Sincroniza o projeto com o controle de versão Git.")
    sync_parser.add_argument("--project", required=True, help="Caminho do projeto.")
    sync_parser.add_argument("--remote", default="", help="URL opcional do repositório Git remoto.")

    args = parser.parse_args()

    repo = ProjectRepository()
    temp_repo = TemplateRepository()
    ws_repo = WorkspaceRepository()

    if args.command == "create":
        from docbuilder.core.services.project_services import CreateProjectUseCase
        use_case = CreateProjectUseCase(repo)
        try:
            dto = use_case.execute(
                name=args.name,
                author=args.author,
                language=args.language,
                template=args.template,
                target_dir=Path(args.dir)
            )
            print(json.dumps({"success": True, "project": dto.__dict__}, ensure_ascii=False, default=str))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "validate":
        from docbuilder.core.services.build_services import ValidateProjectUseCase
        use_case = ValidateProjectUseCase(temp_repo)
        try:
            project_path = Path(args.project)
            from docbuilder.core.services.project_services import LoadProjectUseCase
            load_use_case = LoadProjectUseCase(repo)
            project_dto = load_use_case.execute(project_path)
            
            result = use_case.execute(project_dto, project_path)
            print(json.dumps({
                "success": True,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings
            }, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "build":
        from docbuilder.core.exporters.docx_exporter import DocxExporter
        from docbuilder.core.exporters.pdf_exporter import PdfExporter
        from docbuilder.core.exporters.html_exporter import HtmlExporter
        from docbuilder.core.exporters.markdown_exporter import MarkdownExporter
        from docbuilder.core.services.build_services import BuildProjectUseCase
        from docbuilder.core.services.project_services import LoadProjectUseCase

        docx_exp = DocxExporter()
        pdf_exp = PdfExporter(docx_exp)
        html_exp = HtmlExporter()
        md_exp = MarkdownExporter()

        exporters_list = [docx_exp, pdf_exp, html_exp, md_exp]
        builder = DocumentBuilder()

        use_case = BuildProjectUseCase(temp_repo, builder, exporters_list)
        try:
            project_path = Path(args.project)
            load_use_case = LoadProjectUseCase(repo)
            project_dto = load_use_case.execute(project_path)

            formats = [f.strip().lower() for f in args.formats.split(",")]
            result = use_case.execute(project_dto, project_path, formats)
            
            print(json.dumps({
                "success": result.success,
                "message": result.message,
                "output_files": result.output_files,
                "logs": result.logs
            }, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "import":
        from docbuilder.core.services.project_services import ImportDocumentUseCase
        use_case = ImportDocumentUseCase()
        try:
            file_path = Path(args.file)
            project_path = Path(args.project)
            dto = use_case.execute(file_path, project_path)
            print(json.dumps({"success": True, "imported_document": dto.__dict__}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "workspace-list":
        from docbuilder.core.services.workspace_services import LoadWorkspaceUseCase
        use_case = LoadWorkspaceUseCase(ws_repo)
        try:
            workspace_path = Path(args.dir)
            ws = use_case.execute(workspace_path)
            print(json.dumps({
                "success": True,
                "workspace_name": ws.name,
                "project_paths": ws.project_paths,
                "global_settings": ws.global_settings
            }, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "workspace-register":
        from docbuilder.core.services.workspace_services import RegisterProjectInWorkspaceUseCase
        use_case = RegisterProjectInWorkspaceUseCase(ws_repo)
        try:
            project_path = Path(args.project)
            workspace_path = Path(args.dir)
            ws = use_case.execute(project_path, workspace_path)
            print(json.dumps({
                "success": True,
                "workspace_name": ws.name,
                "project_paths": ws.project_paths
            }, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)

    elif args.command == "sync":
        from docbuilder.core.services.sync_services import SyncProjectUseCase
        git_prov = GitStorage()
        use_case = SyncProjectUseCase(git_prov)
        try:
            project_path = Path(args.project)
            remote_url = args.remote
            
            # Executa a validação rápida da presença do git
            if not git_prov.connect({"remote_url": remote_url} if remote_url else {}):
                raise RuntimeError("Git executável não encontrado no PATH.")

            success = use_case.execute(project_path, {"remote_url": remote_url} if remote_url else {})
            print(json.dumps({
                "success": success,
                "message": "Sincronização concluída com sucesso e tag criada." if success else "Sincronização falhou."
            }, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)


if __name__ == "__main__":
    main()
