"""
Implementação do repositório de persistência de projetos utilizando arquivos YAML.
Lida com a conversão entre o modelo de domínio do Projeto e o arquivo manifest.yaml.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from docbuilder.core.domain.entities import (
    Project,
    Volume,
    Part,
    Chapter,
    Document,
    Version,
)
from docbuilder.core.domain.interfaces import IProjectRepository


class ProjectRepository(IProjectRepository):
    """
    Implementação concreta de IProjectRepository para salvar e carregar
    projetos baseados no manifesto 'manifest.yaml'.
    """

    def save(self, project: Project, destination_path: Path) -> None:
        """
        Salva o projeto e serializa a hierarquia completa de volumes, partes,
        capítulos e documentos em manifest.yaml.
        """
        if not destination_path.exists():
            destination_path.mkdir(parents=True, exist_ok=True)

        manifest_file = destination_path / "manifest.yaml"

        # Converte a hierarquia de domínio em um dicionário serializável
        data = {
            "title": project.name,
            "version": str(project.version),
            "author": project.author,
            "language": project.language,
            "logo": project.logo_path,
            "template": project.template_name,
            "structure_mode": project.structure_mode,
            "changelog_history": project.changelog_history,
            "volumes": self._serialize_volumes(project.volumes),
        }

        with open(manifest_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def load(self, project_path: Path) -> Project:
        """
        Carrega e reconstrói o modelo de domínio do Projeto a partir do manifest.yaml.
        """
        manifest_file = project_path / "manifest.yaml"
        if not manifest_file.exists():
            raise FileNotFoundError(
                f"Arquivo de manifesto não encontrado em: {manifest_file}"
            )

        with open(manifest_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Erro de sintaxe no arquivo manifest.yaml: {e}")

        # Reconstrói a versão
        version_str = data.get("version", "1.0.0.1")
        version = Version.from_string(version_str)

        # Cria o projeto básico
        project = Project(
            name=data.get("title", ""),
            author=data.get("author", ""),
            language=data.get("language", "pt-BR"),
            version=version,
            logo_path=data.get("logo"),
            template_name=data.get("template", "Corporate"),
            structure_mode=data.get("structure_mode", "fluid"),
            changelog_history=data.get("changelog_history", []),
        )

        # Reconstrói a árvore hierárquica
        volumes_data = data.get("volumes", [])
        project.volumes = self._deserialize_volumes(volumes_data)

        return project

    def _serialize_volumes(self, volumes: List[Volume]) -> List[Dict[str, Any]]:
        serialized = []
        for vol in volumes:
            serialized_vol = {"title": vol.title, "parts": []}
            for part in vol.parts:
                serialized_part = {"title": part.title, "chapters": []}
                for cap in part.chapters:
                    serialized_cap = {"title": cap.title, "documents": []}
                    for doc in cap.documents:
                        serialized_doc = {
                            "title": doc.title,
                            "file_path": doc.file_path,
                            "format": doc.format,
                        }
                        serialized_cap["documents"].append(serialized_doc)
                    serialized_part["chapters"].append(serialized_cap)
                serialized_vol["parts"].append(serialized_part)
            serialized.append(serialized_vol)
        return serialized

    def _deserialize_volumes(self, volumes_data: List[Dict[str, Any]]) -> List[Volume]:
        volumes = []
        if not volumes_data:
            return volumes

        for vol_data in volumes_data:
            vol = Volume(title=vol_data.get("title", ""))

            parts_data = vol_data.get("parts", [])
            for part_data in parts_data:
                part = Part(title=part_data.get("title", ""))

                chapters_data = part_data.get("chapters", [])
                for cap_data in chapters_data:
                    cap = Chapter(title=cap_data.get("title", ""))

                    docs_data = cap_data.get("documents", [])
                    for doc_data in docs_data:
                        doc = Document(
                            title=doc_data.get("title", ""),
                            file_path=doc_data.get("file_path", ""),
                            format=doc_data.get("format", "markdown"),
                        )
                        cap.add_document(doc)
                    part.add_chapter(cap)
                vol.add_part(part)
            volumes.append(vol)
        return volumes
