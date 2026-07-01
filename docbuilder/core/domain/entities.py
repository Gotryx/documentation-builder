"""
Entidades de domínio do GoTryx Documentation Builder.
Define a estrutura hierárquica e os metadados do projeto de documentação.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4, UUID


@dataclass
class Version:
    """
    Objeto de Valor que representa a versão do projeto (Major.Minor.Patch.Build).
    """

    major: int = 1
    minor: int = 0
    patch: int = 0
    build: int = 1

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}.{self.build}"

    def increment_major(self) -> None:
        self.major += 1
        self.minor = 0
        self.patch = 0
        self.build += 1

    def increment_minor(self) -> None:
        self.minor += 1
        self.patch = 0
        self.build += 1

    def increment_patch(self) -> None:
        self.patch += 1
        self.build += 1

    def increment_build(self) -> None:
        self.build += 1

    @classmethod
    def from_string(cls, version_str: str) -> "Version":
        """Cria uma instância de Version a partir de uma string."""
        try:
            parts = version_str.strip().split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            build = int(parts[3]) if len(parts) > 3 else 1
            return cls(major, minor, patch, build)
        except (ValueError, IndexError):
            return cls()


@dataclass
class TemplateStyle:
    """
    Objeto de Valor que define os estilos e especificações visuais de um template.
    """

    name: str  # Corporate, Technical, Book, Manual
    font_family: str
    font_size: int
    margin_top: float  # em cm
    margin_bottom: float  # em cm
    margin_left: float  # em cm
    margin_right: float  # em cm
    header_text: str
    footer_text: str
    primary_color: str  # Hexadecimal
    secondary_color: str  # Hexadecimal
    numbering_style: str  # Arabic, Roman, etc.
    logo_enabled: bool = True


@dataclass
class Document:
    """
    Entidade que representa um arquivo de documentação individual de entrada.
    """

    title: str
    file_path: str  # Caminho relativo ao projeto
    id: UUID = field(default_factory=uuid4)
    format: str = "markdown"  # markdown, docx, odt, txt, html

    def validate(self) -> List[str]:
        """Realiza validações específicas da entidade documento."""
        errors = []
        if not self.title.strip():
            errors.append("O título do documento não pode estar vazio.")
        if not self.file_path.strip():
            errors.append("O caminho do arquivo do documento não pode estar vazio.")
        return errors


@dataclass
class Chapter:
    """
    Entidade que representa um Capítulo, contendo uma lista de documentos.
    """

    title: str
    id: UUID = field(default_factory=uuid4)
    documents: List[Document] = field(default_factory=list)

    def add_document(self, document: Document) -> None:
        self.documents.append(document)

    def remove_document(self, document_id: UUID) -> bool:
        for idx, doc in enumerate(self.documents):
            if doc.id == document_id:
                self.documents.pop(idx)
                return True
        return False


@dataclass
class Part:
    """
    Entidade que representa uma Parte da documentação, contendo capítulos.
    """

    title: str
    id: UUID = field(default_factory=uuid4)
    chapters: List[Chapter] = field(default_factory=list)

    def add_chapter(self, chapter: Chapter) -> None:
        self.chapters.append(chapter)

    def remove_chapter(self, chapter_id: UUID) -> bool:
        for idx, cap in enumerate(self.chapters):
            if cap.id == chapter_id:
                self.chapters.pop(idx)
                return True
        return False


@dataclass
class Volume:
    """
    Entidade que representa um Volume da documentação, contendo partes.
    """

    title: str
    id: UUID = field(default_factory=uuid4)
    parts: List[Part] = field(default_factory=list)

    def add_part(self, part: Part) -> None:
        self.parts.append(part)

    def remove_part(self, part_id: UUID) -> bool:
        for idx, part in enumerate(self.parts):
            if part.id == part_id:
                self.parts.pop(idx)
                return True
        return False


@dataclass
class Project:
    """
    Agregado Raiz que representa uma documentação completa do GoTryx.
    """

    name: str
    author: str
    language: str
    version: Version = field(default_factory=Version)
    logo_path: Optional[str] = None
    template_name: str = "Corporate"
    id: UUID = field(default_factory=uuid4)
    volumes: List[Volume] = field(default_factory=list)
    changelog_history: List[str] = field(default_factory=list)

    def add_volume(self, volume: Volume) -> None:
        self.volumes.append(volume)

    def remove_volume(self, volume_id: UUID) -> bool:
        for idx, vol in enumerate(self.volumes):
            if vol.id == volume_id:
                self.volumes.pop(idx)
                return True
        return False

    def validate(self) -> List[str]:
        """
        Valida a integridade lógica do projeto (ex: campos vazios, duplicidade).
        """
        errors = []
        if not self.name.strip():
            errors.append("O nome do projeto não pode estar vazio.")
        if not self.author.strip():
            errors.append("O autor do projeto não pode estar vazio.")
        if not self.language.strip():
            errors.append("O idioma do projeto não pode estar vazio.")

        # Verificar duplicidades de títulos nos volumes
        vol_titles = [v.title.lower() for v in self.volumes]
        if len(vol_titles) != len(set(vol_titles)):
            errors.append("Existem volumes com títulos duplicados no projeto.")

        return errors
