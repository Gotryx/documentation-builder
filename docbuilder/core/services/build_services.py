"""
Casos de uso para validação e orquestração do processo de Build e Exportação da documentação.
Executa verificações profundas pré-compilação e coordena os exportadores.
"""

import re
from pathlib import Path
from typing import List, Tuple
from docbuilder.core.domain.interfaces import (
    ITemplateRepository,
    IDocumentBuilder,
    IExporter,
)
from docbuilder.core.services.dtos import (
    ProjectDTO,
    ValidationResultDTO,
    BuildResultDTO,
)
from docbuilder.core.services.project_services import ProjectMappingHelper


class ValidateProjectUseCase:
    """
    Caso de Uso responsável por realizar todas as validações pré-compilação
    no projeto e nos seus documentos.
    """

    def __init__(self, template_repository: ITemplateRepository) -> None:
        self._template_repo = template_repository

    def execute(
        self, project_dto: ProjectDTO, project_dir: Path
    ) -> ValidationResultDTO:
        errors: List[str] = []
        warnings: List[str] = []

        project = ProjectMappingHelper.dto_to_entity(project_dto)

        # 1. Validações básicas de Domínio
        domain_errors = project.validate()
        errors.extend(domain_errors)

        # 2. Validar existência do template
        templates_available = self._template_repo.list_available_templates()
        if project.template_name not in templates_available:
            errors.append(
                f"O template '{project.template_name}' configurado no projeto não existe."
            )

        # 3. Validar arquivo de logo (se habilitado)
        if project.logo_path:
            logo_absolute = project_dir / project.logo_path
            if not logo_absolute.exists():
                errors.append(
                    f"O arquivo de logo '{project.logo_path}' não foi encontrado no disco."
                )

        # 4. Validar arquivos inexistentes e links quebrados na estrutura
        documents_collected: List[Tuple[str, Path]] = []

        for vol in project.volumes:
            for part in vol.parts:
                for cap in part.chapters:
                    for doc in cap.documents:
                        doc_path = project_dir / doc.file_path
                        documents_collected.append((doc.title, doc_path))

                        # Validar existência do arquivo físico
                        if not doc_path.exists():
                            errors.append(
                                f"Arquivo inexistente no disco: '{doc.file_path}' "
                                f"(Volume: '{vol.title}' -> Capítulo: '{cap.title}' -> Doc: '{doc.title}')"
                            )
                        else:
                            # Executar validação de conteúdo (links/imagens)
                            doc_errors, doc_warnings = self._validate_document_content(
                                doc_path, project_dir
                            )
                            errors.extend(
                                [f"[{doc.title}] {err}" for err in doc_errors]
                            )
                            warnings.extend(
                                [f"[{doc.title}] {warn}" for warn in doc_warnings]
                            )

        # 5. Validar duplicidade de arquivos importados
        filepaths = [str(path) for _, path in documents_collected]
        duplicates = set([fp for fp in filepaths if filepaths.count(fp) > 1])
        for dup in duplicates:
            warnings.append(
                f"O arquivo '{Path(dup).name}' está sendo reutilizado em múltiplos capítulos."
            )

        is_valid = len(errors) == 0
        return ValidationResultDTO(is_valid=is_valid, errors=errors, warnings=warnings)

    def _validate_document_content(
        self, file_path: Path, project_dir: Path
    ) -> Tuple[List[str], List[str]]:
        """Analisa o conteúdo do arquivo para identificar links locais quebrados ou imagens faltantes."""
        errors: List[str] = []
        warnings: List[str] = []

        if file_path.suffix.lower() not in [".md", ".markdown", ".html", ".htm"]:
            # Não fazemos análise de links profundos em binários como DOCX por limitação de parsing direto rápido
            return errors, warnings

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"Falha ao ler conteúdo para validação: {e}")
            return errors, warnings

        # Expressão regular para encontrar links Markdown: [texto](link)
        # Ignora links externos iniciados com http://, https://, mailto:, etc.
        md_links = re.findall(r"\[.*?\]\((.*?)\)", content)
        # Expressão regular para tags HTML de links e imagens
        html_hrefs = re.findall(r'href=["\'](.*?)["\']', content)
        html_srcs = re.findall(r'src=["\'](.*?)["\']', content)

        all_links = md_links + html_hrefs
        all_sources = html_srcs  # Imagens, mídias

        # Validar Links locais
        for link in all_links:
            # Limpa âncoras internas (#secao)
            link_clean = link.split("#")[0]
            if not link_clean:
                continue

            # Ignora links externos e esquemas de rede
            if link_clean.startswith(
                ("http://", "https://", "mailto:", "ftp:", "tel:")
            ):
                continue

            # Resolve o caminho do link relativo ao diretório do arquivo atual ou à raiz do projeto
            link_path_relative_to_file = file_path.parent / link_clean
            link_path_relative_to_project = project_dir / link_clean

            if (
                not link_path_relative_to_file.exists()
                and not link_path_relative_to_project.exists()
            ):
                warnings.append(f"Link local suspeito de estar quebrado: '{link}'")

        # Validar Imagens locais
        # Encontra imagens no padrão Markdown: ![alt](caminho_imagem)
        md_images = re.findall(r"\!\[.*?\]\((.*?)\)", content)
        for img in md_images + all_sources:
            if img.startswith(("http://", "https://", "data:")):
                continue

            img_path_relative_to_file = file_path.parent / img
            img_path_relative_to_project = project_dir / img

            if (
                not img_path_relative_to_file.exists()
                and not img_path_relative_to_project.exists()
            ):
                errors.append(
                    f"Imagem local inexistente referenciada no texto: '{img}'"
                )

        return errors, warnings


class BuildProjectUseCase:
    """
    Caso de Uso principal que coordena a compilação e consolidação
    do projeto completo para gerar a documentação final.
    """

    def __init__(
        self,
        template_repository: ITemplateRepository,
        document_builder: IDocumentBuilder,
        exporters: List[IExporter],
    ) -> None:
        self._template_repo = template_repository
        self._builder = document_builder
        self._exporters = {exp.get_supported_format(): exp for exp in exporters}
        self._logs: List[str] = []

    def execute(
        self, project_dto: ProjectDTO, project_dir: Path, output_formats: List[str]
    ) -> BuildResultDTO:
        self._logs = []
        self._log("Iniciando build do projeto...")

        project = ProjectMappingHelper.dto_to_entity(project_dto)

        # 1. Carrega as especificações do template
        template_style = self._template_repo.get_template_style(project.template_name)
        self._log(f"Carregado template de estilo: {template_style.name}")

        # 2. Executa a compilação do conteúdo (Builder)
        try:
            self._log("Consolidando estrutura hierárquica e gerando sumários...")
            compiled_doc_path = self._builder.build(
                project, project_dir, template_style
            )
            self._log(
                f"Estrutura montada com sucesso em arquivo temporário: {compiled_doc_path.name}"
            )
        except Exception as e:
            self._log(f"ERRO CRÍTICO NO BUILDER: {e}")
            return BuildResultDTO(
                success=False, message=f"Erro de compilação: {e}", logs=self._logs
            )

        # 3. Exporta para cada formato solicitado
        output_files: List[str] = []
        output_dir = project_dir / "dist"
        output_dir.mkdir(exist_ok=True)

        for fmt in output_formats:
            exporter = self._exporters.get(fmt)
            if not exporter:
                self._log(
                    f"Aviso: Nenhum exportador disponível para o formato '{fmt}'. Ignorado."
                )
                continue

            # Nome do arquivo final gerado
            clean_project_name = "".join(
                c for c in project.name if c.isalnum() or c in (" ", "_", "-")
            ).rstrip()
            clean_project_name = clean_project_name.replace(" ", "_")
            out_filename = f"{clean_project_name}_v{project.version}.{fmt}"
            out_path = output_dir / out_filename

            try:
                self._log(f"Exportando para formato '{fmt.upper()}'...")
                exporter.export(compiled_doc_path, out_path, template_style)
                output_files.append(str(out_path))
                self._log(f"Exportado com sucesso: {out_filename}")
            except Exception as e:
                self._log(f"Erro ao exportar formato {fmt.upper()}: {e}")

        # Remove o arquivo temporário de build intermediário se necessário
        if compiled_doc_path.exists():
            try:
                compiled_doc_path.unlink()
            except OSError:
                pass

        success = len(output_files) > 0
        message = (
            "Build finalizado com sucesso!"
            if success
            else "O build finalizou mas nenhuma exportação pôde ser gerada."
        )
        return BuildResultDTO(
            success=success, message=message, output_files=output_files, logs=self._logs
        )

    def _log(self, message: str) -> None:
        self._logs.append(message)
