"""
Objetos de Transferência de Dados (DTOs) para comunicação entre a UI e a Camada de Serviços.
Garante o desacoplamento das entidades de domínio ricas e evita contaminação da UI.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DocumentDTO:
    """DTO para transporte de informações de documentos individuais."""

    id: str
    title: str
    file_path: str
    format: str


@dataclass
class ChapterDTO:
    """DTO para transporte de informações de capítulos."""

    id: str
    title: str
    documents: List[DocumentDTO] = field(default_factory=list)


@dataclass
class PartDTO:
    """DTO para transporte de informações de partes."""

    id: str
    title: str
    chapters: List[ChapterDTO] = field(default_factory=list)


@dataclass
class VolumeDTO:
    """DTO para transporte de informações de volumes."""

    id: str
    title: str
    parts: List[PartDTO] = field(default_factory=list)


@dataclass
class ProjectDTO:
    """DTO para transporte de informações completas do projeto."""

    name: str
    author: str
    language: str
    version: str
    logo_path: Optional[str] = None
    template_name: str = "Corporate"
    volumes: List[VolumeDTO] = field(default_factory=list)
    changelog_history: List[str] = field(default_factory=list)


@dataclass
class ValidationResultDTO:
    """DTO contendo informações das validações pré-build."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BuildResultDTO:
    """DTO que contém o resultado do processo de compilação."""

    success: bool
    message: str
    output_files: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
