"""
Casos de Uso (Use Cases) e Serviços de Gerenciamento do Ciclo de Vida do Projeto.
Lida com criação, carregamento, salvamento, importação de documentos e reordenação.
"""

import shutil
from pathlib import Path
from uuid import UUID
from typing import List
from docbuilder.core.domain.entities import (
    Project,
    Volume,
    Part,
    Chapter,
    Document,
    Version,
)
from docbuilder.core.domain.interfaces import IProjectRepository
from docbuilder.core.services.dtos import (
    ProjectDTO,
    VolumeDTO,
    PartDTO,
    ChapterDTO,
    DocumentDTO,
)


class ProjectMappingHelper:
    """Classe auxiliar para conversão entre Entidades de Domínio e DTOs."""

    @staticmethod
    def entity_to_dto(project: Project) -> ProjectDTO:
        volumes_dto = []
        for vol in project.volumes:
            parts_dto = []
            for part in vol.parts:
                chapters_dto = []
                for cap in part.chapters:
                    docs_dto = []
                    for doc in cap.documents:
                        docs_dto.append(
                            DocumentDTO(
                                id=str(doc.id),
                                title=doc.title,
                                file_path=doc.file_path,
                                format=doc.format,
                            )
                        )
                    chapters_dto.append(
                        ChapterDTO(id=str(cap.id), title=cap.title, documents=docs_dto)
                    )
                parts_dto.append(
                    PartDTO(id=str(part.id), title=part.title, chapters=chapters_dto)
                )
            volumes_dto.append(
                VolumeDTO(id=str(vol.id), title=vol.title, parts=parts_dto)
            )

        return ProjectDTO(
            name=project.name,
            author=project.author,
            language=project.language,
            version=str(project.version),
            logo_path=project.logo_path,
            template_name=project.template_name,
            structure_mode=project.structure_mode,
            volumes=volumes_dto,
            changelog_history=project.changelog_history,
        )

    @staticmethod
    def dto_to_entity(dto: ProjectDTO) -> Project:
        project = Project(
            name=dto.name,
            author=dto.author,
            language=dto.language,
            version=Version.from_string(dto.version),
            logo_path=dto.logo_path,
            template_name=dto.template_name,
            structure_mode=dto.structure_mode,
            changelog_history=dto.changelog_history,
        )

        for vol_dto in dto.volumes:
            vol = Volume(id=UUID(vol_dto.id), title=vol_dto.title)
            for part_dto in vol_dto.parts:
                part = Part(id=UUID(part_dto.id), title=part_dto.title)
                for cap_dto in part_dto.chapters:
                    cap = Chapter(id=UUID(cap_dto.id), title=cap_dto.title)
                    for doc_dto in cap_dto.documents:
                        doc = Document(
                            id=UUID(doc_dto.id),
                            title=doc_dto.title,
                            file_path=doc_dto.file_path,
                            format=doc_dto.format,
                        )
                        cap.add_document(doc)
                    part.add_chapter(cap)
                vol.add_part(part)
            project.add_volume(vol)

        return project


class CreateProjectUseCase:
    """Caso de uso para criar um novo projeto de documentação."""

    def __init__(self, repository: IProjectRepository) -> None:
        self._repository = repository

    def execute(
        self,
        name: str,
        author: str,
        language: str,
        template: str,
        target_dir: Path,
        structure_mode: str = "fluid",
    ) -> ProjectDTO:
        # Garante a criação física do diretório
        target_dir.mkdir(parents=True, exist_ok=True)

        # Garante a criação da pasta resources para logos/assets
        (target_dir / "resources").mkdir(exist_ok=True)

        project = Project(
            name=name,
            author=author,
            language=language,
            version=Version(1, 0, 0, 1),
            template_name=template,
            structure_mode=structure_mode,
            changelog_history=[
                "1.0.0.1 - Inicialização do projeto de documentação GoTryx."
            ],
        )

        # 1. Varre o diretório em busca de documentos suportados já existentes
        supported_extensions = {
            ".md",
            ".markdown",
            ".docx",
            ".odt",
            ".txt",
            ".html",
            ".htm",
        }
        found_files: List[Path] = []

        # Escaneamento recursivo (limite de profundidade de 3 níveis para evitar loops)
        self._scan_directory(
            target_dir,
            target_dir,
            supported_extensions,
            found_files,
            depth=0,
            max_depth=3,
        )

        if found_files:
            # Ordena os arquivos para consistência alfanumérica/numérica
            sorted_files = sorted(found_files, key=lambda p: str(p))

            if structure_mode == "fluid":
                # Modo Fluido (Linear / Flat)
                vol = Volume(title="Volume I - Documentação")
                part = Part(title="Parte I - Conteúdo Geral")
                vol.add_part(part)
                project.add_volume(vol)

                for idx, file_path in enumerate(sorted_files):
                    relative_path = file_path.relative_to(target_dir)

                    parts_list = list(relative_path.parent.parts)
                    parts_list.append(relative_path.stem)
                    clean_parts = [
                        p.replace("_", " ").replace("-", " ").title()
                        for p in parts_list
                        if p and p != "."
                    ]
                    chapter_title = f"Capítulo {idx + 1:02d} - " + " - ".join(
                        clean_parts
                    )

                    ext = file_path.suffix.lower().replace(".", "")
                    fmt = "markdown" if ext in ["md", "markdown"] else ext

                    doc = Document(
                        title=file_path.stem.replace("_", " ")
                        .replace("-", " ")
                        .title(),
                        file_path=str(relative_path),
                        format=fmt,
                    )

                    chapter = Chapter(title=chapter_title)
                    chapter.add_document(doc)
                    part.add_chapter(chapter)
            else:
                # Modo por Pastas (folders) - Hierárquico e estruturado pelas pastas
                vol = Volume(title="Volume I - Documentação")
                project.add_volume(vol)

                # Parte principal padrão para arquivos na raiz
                default_part = Part(title="Parte I - Conteúdo Geral")
                vol.add_part(default_part)

                parts_map = {}
                chapters_map = {}

                for file_path in sorted_files:
                    relative_path = file_path.relative_to(target_dir)
                    parts_list = list(relative_path.parent.parts)

                    ext = file_path.suffix.lower().replace(".", "")
                    fmt = "markdown" if ext in ["md", "markdown"] else ext

                    doc = Document(
                        title=file_path.stem.replace("_", " ")
                        .replace("-", " ")
                        .title(),
                        file_path=str(relative_path),
                        format=fmt,
                    )

                    if not parts_list or str(relative_path.parent) == ".":
                        # Arquivo solto na raiz
                        chapter_title = f"Capítulo {len(default_part.chapters) + 1:02d} - {doc.title}"
                        chapter = Chapter(title=chapter_title)
                        chapter.add_document(doc)
                        default_part.add_chapter(chapter)
                    else:
                        # Arquivo em subpastas
                        part_key = parts_list[0]
                        if part_key not in parts_map:
                            part_num = len(vol.parts) + 1
                            part_title = f"Parte {part_num:02d} - {part_key.replace('_', ' ').replace('-', ' ').title()}"
                            new_part = Part(title=part_title)
                            vol.add_part(new_part)
                            parts_map[part_key] = new_part

                        target_part = parts_map[part_key]

                        # O capítulo será baseado nas pastas subsequentes mais o nome do arquivo
                        if len(parts_list) > 1:
                            cap_subfolders = [
                                p.replace("_", " ").replace("-", " ").title()
                                for p in parts_list[1:]
                            ]
                            cap_key = " - ".join(cap_subfolders)
                        else:
                            cap_key = doc.title

                        cap_map_key = (target_part.id, cap_key)
                        if cap_map_key not in chapters_map:
                            cap_num = len(target_part.chapters) + 1
                            chapter_title = f"Capítulo {cap_num:02d} - {cap_key}"
                            new_chapter = Chapter(title=chapter_title)
                            target_part.add_chapter(new_chapter)
                            chapters_map[cap_map_key] = new_chapter

                        target_chapter = chapters_map[cap_map_key]
                        target_chapter.add_document(doc)

                # Remove a Parte Geral se ela ficou sem capítulos
                if not default_part.chapters:
                    vol.parts.remove(default_part)
                    # Reordena a numeração das outras partes
                    for p_idx, p in enumerate(vol.parts):
                        title_clean = p.title.split(" - ", 1)[-1]
                        p.title = f"Parte {p_idx + 1:02d} - {title_clean}"
        else:
            # 2. Pasta vazia: cria estrutura de exemplo padrão com introducao.md
            (target_dir / "documents").mkdir(exist_ok=True)

            vol_exemplo = Volume(title="Volume I - Guia")
            part_exemplo = Part(title="Parte I - Fundamentos")
            cap_exemplo = Chapter(title="Capítulo 01 - Introdução")

            doc_path = target_dir / "documents" / "introducao.md"
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(
                    "# Introdução ao Projeto\n\nEste é o documento inicial do seu novo projeto de documentação GoTryx.\nEdite-o ou importe novos arquivos."
                )

            doc_exemplo = Document(
                title="Visão Geral",
                file_path="documents/introducao.md",
                format="markdown",
            )
            cap_exemplo.add_document(doc_exemplo)
            part_exemplo.add_chapter(cap_exemplo)
            vol_exemplo.add_part(part_exemplo)
            project.add_volume(vol_exemplo)

        # Salva o projeto
        self._repository.save(project, target_dir)

        return ProjectMappingHelper.entity_to_dto(project)

    def _scan_directory(
        self,
        base_dir: Path,
        current_dir: Path,
        extensions: set,
        file_list: list,
        depth: int,
        max_depth: int,
    ) -> None:
        if depth > max_depth:
            return

        try:
            for item in current_dir.iterdir():
                # Ignora arquivos/pastas ocultas, diretórios de build, recursos, pastas de exemplo geradas e ambientes virtuais
                if item.name.startswith(".") or item.name in [
                    "dist",
                    "resources",
                    "documents",
                    "__pycache__",
                    "node_modules",
                    "ambiente",
                    "venv",
                    ".venv",
                ]:
                    continue

                if item.is_file() and item.suffix.lower() in extensions:
                    file_list.append(item)
                elif item.is_dir():
                    self._scan_directory(
                        base_dir, item, extensions, file_list, depth + 1, max_depth
                    )
        except PermissionError:
            pass


class SyncFolderFilesUseCase:
    """Caso de uso para escanear a pasta do projeto em busca de novos documentos físicos no disco."""

    def __init__(self, repository: IProjectRepository) -> None:
        self._repository = repository

    def execute(self, project: Project, project_dir: Path) -> List[str]:
        # 1. Obtém os caminhos relativos dos documentos que já estão no manifesto
        existing_paths = set()
        for vol in project.volumes:
            for part in vol.parts:
                for cap in part.chapters:
                    for doc in cap.documents:
                        existing_paths.add(doc.file_path)

        # 2. Varre o diretório em busca de documentos no disco
        supported_extensions = {
            ".md",
            ".markdown",
            ".docx",
            ".odt",
            ".txt",
            ".html",
            ".htm",
        }
        found_files: List[Path] = []
        self._scan_directory(
            project_dir,
            project_dir,
            supported_extensions,
            found_files,
            depth=0,
            max_depth=3,
        )

        # 3. Filtra os arquivos que não estão no manifesto
        new_files = []
        for file_path in sorted(found_files, key=lambda p: str(p)):
            relative_path = file_path.relative_to(project_dir)
            if str(relative_path) not in existing_paths:
                new_files.append(file_path)

        if not new_files:
            return []

        # 4. Adiciona os novos arquivos respeitando o structure_mode do projeto
        if not project.volumes:
            vol = Volume(title="Volume I - Documentação")
            project.add_volume(vol)
        else:
            vol = project.volumes[0]

        added_titles = []

        if project.structure_mode == "fluid":
            # Modo Fluido (Linear / Flat)
            if not vol.parts:
                part = Part(title="Parte I - Conteúdo Geral")
                vol.add_part(part)
            else:
                part = vol.parts[0]

            start_idx = len(part.chapters) + 1

            for idx, file_path in enumerate(new_files):
                relative_path = file_path.relative_to(project_dir)

                # Formata o título do capítulo
                parts_list = list(relative_path.parent.parts)
                parts_list.append(relative_path.stem)
                clean_parts = [
                    p.replace("_", " ").replace("-", " ").title()
                    for p in parts_list
                    if p and p != "."
                ]
                chapter_title = f"Capítulo {start_idx + idx:02d} - " + " - ".join(
                    clean_parts
                )

                ext = file_path.suffix.lower().replace(".", "")
                fmt = "markdown" if ext in ["md", "markdown"] else ext

                from docbuilder.core.domain.entities import Document, Chapter

                doc = Document(
                    title=file_path.stem.replace("_", " ").replace("-", " ").title(),
                    file_path=str(relative_path),
                    format=fmt,
                )

                chapter = Chapter(title=chapter_title)
                chapter.add_document(doc)
                part.add_chapter(chapter)
                added_titles.append(doc.title)
        else:
            # Modo por Pastas (folders) - Hierárquico
            from docbuilder.core.domain.entities import (
                Document,
                Chapter,
                Part as DomainPart,
            )

            for file_path in new_files:
                relative_path = file_path.relative_to(project_dir)
                parts_list = list(relative_path.parent.parts)

                ext = file_path.suffix.lower().replace(".", "")
                fmt = "markdown" if ext in ["md", "markdown"] else ext

                doc = Document(
                    title=file_path.stem.replace("_", " ").replace("-", " ").title(),
                    file_path=str(relative_path),
                    format=fmt,
                )

                if not parts_list or str(relative_path.parent) == ".":
                    # Arquivo solto na raiz: vai para a primeira parte
                    if not vol.parts:
                        target_part = DomainPart(title="Parte I - Conteúdo Geral")
                        vol.add_part(target_part)
                    else:
                        target_part = vol.parts[0]

                    chapter_title = (
                        f"Capítulo {len(target_part.chapters) + 1:02d} - {doc.title}"
                    )
                    chapter = Chapter(title=chapter_title)
                    chapter.add_document(doc)
                    target_part.add_chapter(chapter)
                    added_titles.append(doc.title)
                else:
                    # Arquivo dentro de subpastas
                    part_title_base = (
                        parts_list[0].replace("_", " ").replace("-", " ").title()
                    )

                    # Procura por uma parte correspondente existente
                    target_part = None
                    for existing_part in vol.parts:
                        if part_title_base.lower() in existing_part.title.lower():
                            target_part = existing_part
                            break

                    if not target_part:
                        part_num = len(vol.parts) + 1
                        part_title = f"Parte {part_num:02d} - {part_title_base}"
                        target_part = DomainPart(title=part_title)
                        vol.add_part(target_part)

                    # Define o título do capítulo com base nas pastas de nível 2+ e arquivo
                    if len(parts_list) > 1:
                        cap_subfolders = [
                            p.replace("_", " ").replace("-", " ").title()
                            for p in parts_list[1:]
                        ]
                        cap_key = " - ".join(cap_subfolders)
                    else:
                        cap_key = doc.title

                    # Procura por um capítulo correspondente existente na parte
                    target_chapter = None
                    for existing_cap in target_part.chapters:
                        if cap_key.lower() in existing_cap.title.lower():
                            target_chapter = existing_cap
                            break

                    if not target_chapter:
                        cap_num = len(target_part.chapters) + 1
                        chapter_title = f"Capítulo {cap_num:02d} - {cap_key}"
                        target_chapter = Chapter(title=chapter_title)
                        target_part.add_chapter(target_chapter)

                    target_chapter.add_document(doc)
                    added_titles.append(doc.title)

        # 5. Salva o manifesto com a nova estrutura adicionada
        self._repository.save(project, project_dir)
        return added_titles

    def _scan_directory(
        self,
        base_dir: Path,
        current_dir: Path,
        extensions: set,
        file_list: list,
        depth: int,
        max_depth: int,
    ) -> None:
        if depth > max_depth:
            return

        try:
            for item in current_dir.iterdir():
                # Ignora arquivos/pastas ocultas, diretórios de build, recursos, pastas de exemplo geradas e ambientes virtuais
                if item.name.startswith(".") or item.name in [
                    "dist",
                    "resources",
                    "documents",
                    "__pycache__",
                    "node_modules",
                    "ambiente",
                    "venv",
                    ".venv",
                ]:
                    continue

                if item.is_file() and item.suffix.lower() in extensions:
                    file_list.append(item)
                elif item.is_dir():
                    self._scan_directory(
                        base_dir, item, extensions, file_list, depth + 1, max_depth
                    )
        except PermissionError:
            pass


class LoadProjectUseCase:
    """Caso de uso para carregar um projeto existente do disco."""

    def __init__(self, repository: IProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_dir: Path) -> ProjectDTO:
        project = self._repository.load(project_dir)
        return ProjectMappingHelper.entity_to_dto(project)


class SaveProjectUseCase:
    """Caso de uso para salvar o estado modificado de um projeto."""

    def __init__(self, repository: IProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_dto: ProjectDTO, project_dir: Path) -> None:
        project = ProjectMappingHelper.dto_to_entity(project_dto)
        # Validação de regras de negócio antes de persistir
        errors = project.validate()
        if errors:
            raise ValueError(
                f"O projeto possui inconsistências impeditivas para salvar: {', '.join(errors)}"
            )

        self._repository.save(project, project_dir)


class ImportDocumentUseCase:
    """Caso de uso para importar de forma segura um arquivo externo para o projeto."""

    def execute(self, external_file_path: Path, project_dir: Path) -> DocumentDTO:
        if not external_file_path.exists():
            raise FileNotFoundError(
                f"O arquivo externo {external_file_path} não existe."
            )

        # Determina o formato com base na extensão
        ext = external_file_path.suffix.lower().replace(".", "")
        if ext not in ["md", "markdown", "docx", "odt", "txt", "html"]:
            raise ValueError(
                f"Extensão de arquivo não suportada para importação: {ext}"
            )

        format_name = "markdown" if ext in ["md", "markdown"] else ext

        # Cria a pasta documents dentro do projeto, caso não exista
        docs_dir = project_dir / "documents"
        docs_dir.mkdir(exist_ok=True)

        # Evita colisões de nomes no diretório copiando com um sufixo
        dest_filename = external_file_path.name
        dest_file_path = docs_dir / dest_filename
        counter = 1
        while dest_file_path.exists():
            stem = external_file_path.stem
            dest_filename = f"{stem}_{counter}.{ext}"
            dest_file_path = docs_dir / dest_filename
            counter += 1

        # Copia o arquivo físico de forma assíncrona/segura
        shutil.copy2(external_file_path, dest_file_path)

        # Retorna o DTO com o caminho relativo interno do projeto
        relative_path = f"documents/{dest_filename}"
        return DocumentDTO(
            id=str(
                UUID(int=0)
            ),  # ID provisório, será atribuído no domínio ao integrar na árvore
            title=external_file_path.stem,
            file_path=relative_path,
            format=format_name,
        )
