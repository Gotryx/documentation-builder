"""
Casos de Uso (Use Cases) e Serviços de Gerenciamento do Ciclo de Vida do Projeto.
Lida com criação, carregamento, salvamento, importação de documentos e reordenação.
"""

import shutil
from pathlib import Path
from uuid import UUID
from typing import List, Optional
from docbuilder.core.domain.entities import Project, Volume, Part, Chapter, Document, Version
from docbuilder.core.domain.interfaces import IProjectRepository
from docbuilder.core.services.dtos import ProjectDTO, VolumeDTO, PartDTO, ChapterDTO, DocumentDTO


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
                        docs_dto.append(DocumentDTO(
                            id=str(doc.id),
                            title=doc.title,
                            file_path=doc.file_path,
                            format=doc.format
                        ))
                    chapters_dto.append(ChapterDTO(
                        id=str(cap.id),
                        title=cap.title,
                        documents=docs_dto
                    ))
                parts_dto.append(PartDTO(
                    id=str(part.id),
                    title=part.title,
                    chapters=chapters_dto
                ))
            volumes_dto.append(VolumeDTO(
                id=str(vol.id),
                title=vol.title,
                parts=parts_dto
            ))

        return ProjectDTO(
            name=project.name,
            author=project.author,
            language=project.language,
            version=str(project.version),
            logo_path=project.logo_path,
            template_name=project.template_name,
            volumes=volumes_dto,
            changelog_history=project.changelog_history
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
            changelog_history=dto.changelog_history
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
                            format=doc_dto.format
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

    def execute(self, name: str, author: str, language: str, template: str, target_dir: Path) -> ProjectDTO:
        # Garante a criação física do diretório
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Cria a pasta de documentos importados do projeto para garantir portabilidade
        (target_dir / "documents").mkdir(exist_ok=True)
        (target_dir / "resources").mkdir(exist_ok=True)

        project = Project(
            name=name,
            author=author,
            language=language,
            version=Version(1, 0, 0, 1),
            template_name=template,
            changelog_history=["1.0.0.1 - Inicialização do projeto de documentação GoTryx."]
        )

        # Cria uma estrutura inicial de exemplo
        vol_exemplo = Volume(title="Volume I - Guia")
        part_exemplo = Part(title="Parte I - Fundamentos")
        cap_exemplo = Chapter(title="Capítulo 01 - Introdução")
        
        # Cria um arquivo markdown físico inicial de boas-vindas
        doc_path = target_dir / "documents" / "introducao.md"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("# Introdução ao Projeto\n\nEste é o documento inicial do seu novo projeto de documentação GoTryx.\nEdite-o ou importe novos arquivos.")

        doc_exemplo = Document(
            title="Visão Geral",
            file_path="documents/introducao.md",
            format="markdown"
        )
        cap_exemplo.add_document(doc_exemplo)
        part_exemplo.add_chapter(cap_exemplo)
        vol_exemplo.add_part(part_exemplo)
        project.add_volume(vol_exemplo)

        # Salva o projeto inicial
        self._repository.save(project, target_dir)

        return ProjectMappingHelper.entity_to_dto(project)


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
            raise ValueError(f"O projeto possui inconsistências impeditivas para salvar: {', '.join(errors)}")
        
        self._repository.save(project, project_dir)


class ImportDocumentUseCase:
    """Caso de uso para importar de forma segura um arquivo externo para o projeto."""

    def execute(self, external_file_path: Path, project_dir: Path) -> DocumentDTO:
        if not external_file_path.exists():
            raise FileNotFoundError(f"O arquivo externo {external_file_path} não existe.")

        # Determina o formato com base na extensão
        ext = external_file_path.suffix.lower().replace(".", "")
        if ext not in ["md", "markdown", "docx", "odt", "txt", "html"]:
            raise ValueError(f"Extensão de arquivo não suportada para importação: {ext}")
        
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
            id=str(UUID(int=0)),  # ID provisório, será atribuído no domínio ao integrar na árvore
            title=external_file_path.stem,
            file_path=relative_path,
            format=format_name
        )
