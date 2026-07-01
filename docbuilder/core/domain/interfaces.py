"""
Interfaces e portas de domínio para desacoplamento de infraestrutura e serviços externos.
Segue o princípio de inversão de dependência (D do SOLID) da Clean Architecture.
"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from docbuilder.core.domain.entities import Project, TemplateStyle
from docbuilder.core.domain.workspace import Workspace


class IProjectRepository(ABC):
    """
    Interface para persistência de projetos de documentação (Carregar/Salvar).
    """

    @abstractmethod
    def save(self, project: Project, destination_path: Path) -> None:
        """Salva o projeto e seu manifesto manifest.yaml no diretório de destino."""
        pass

    @abstractmethod
    def load(self, project_path: Path) -> Project:
        """Carrega o projeto a partir do seu manifesto manifest.yaml."""
        pass


class IWorkspaceRepository(ABC):
    """
    Interface para persistência do portfólio de documentação (Workspace).
    """

    @abstractmethod
    def save(self, workspace: Workspace, destination_path: Path) -> None:
        """Salva a estrutura do workspace e a lista de caminhos em workspace.yaml."""
        pass

    @abstractmethod
    def load(self, destination_path: Path) -> Workspace:
        """Carrega o workspace a partir do workspace.yaml."""
        pass


class ITemplateRepository(ABC):
    """
    Interface para carregamento e gerenciamento de estilos de templates.
    """

    @abstractmethod
    def get_template_style(self, template_name: str) -> TemplateStyle:
        """Retorna as configurações visuais de um template específico pelo nome."""
        pass

    @abstractmethod
    def list_available_templates(self) -> List[str]:
        """Lista os nomes de todos os templates disponíveis no sistema."""
        pass


class IDocumentBuilder(ABC):
    """
    Interface responsável por compilar a estrutura hierárquica e unificar os arquivos de entrada.
    """

    @abstractmethod
    def build(self, project: Project, base_path: Path, template: TemplateStyle) -> Path:
        """
        Orquestra a leitura, ordenação, montagem de cabeçalhos/rodapés e numeração.
        Retorna o caminho de um arquivo intermediário consolidado (HTML/Markdown ou estrutura em memória).
        """
        pass


class IExporter(ABC):
    """
    Interface para os exportadores específicos de formato.
    """

    @abstractmethod
    def export(
        self, source_document_path: Path, output_path: Path, template: TemplateStyle
    ) -> None:
        """
        Converte o documento compilado unificado para o formato de destino específico.
        """
        pass

    @abstractmethod
    def get_supported_format(self) -> str:
        """Retorna a extensão ou nome do formato suportado (ex: 'docx', 'pdf', 'html', 'md')."""
        pass


class IPlugin(ABC):
    """
    Interface básica para o sistema de plugins do GoTryx Documentation Builder.
    Permite adicionar novos exportadores sem alterar o core da aplicação.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Retorna o nome único do plugin."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Retorna a descrição das funcionalidades providas pelo plugin."""
        pass

    @abstractmethod
    def initialize(self, app_context) -> None:
        """Inicializa o plugin injetando dependências ou registrando exportadores."""
        pass


class ICloudStorage(ABC):
    """
    Interface abstrata para armazenamento em nuvem e controle de versão (Git/OneDrive/Google Drive).
    Preparação da arquitetura para a fase futura do roadmap.
    """

    @abstractmethod
    def connect(self, credentials: dict) -> bool:
        """Estabelece conexão com o serviço na nuvem."""
        pass

    @abstractmethod
    def sync_project(self, project_path: Path) -> bool:
        """Sincroniza o diretório do projeto com o serviço na nuvem."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna o nome do provedor (ex: 'git', 'onedrive', 'googledrive')."""
        pass
