"""
Interface gráfica principal (GUI) da GoTryx Documentation Platform utilizando PySide6.
Lógica de controle da janela, gerenciamento do portfólio de projetos (Dashboard do Workspace),
árvore de manifesto reordenável por drag-and-drop, servidor Wiki integrado e sincronização remota Git.
Toda lógica de negócio é delegada para a camada de Serviços e Use Cases.
"""

import sys
import webbrowser
from pathlib import Path
from uuid import uuid4
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QTextBrowser,
    QFormLayout,
    QFrame,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QApplication,
)
from PySide6.QtGui import QIcon

# Importação da camada de Serviços, Repositórios e Domínio
from docbuilder.core.repositories.project_repository import ProjectRepository
from docbuilder.core.repositories.template_repository import TemplateRepository
from docbuilder.core.repositories.workspace_repository import WorkspaceRepository
from docbuilder.core.repositories.cloud.git_storage import GitStorage

from docbuilder.core.builders.document_builder import DocumentBuilder
from docbuilder.core.builders.wiki_server import WikiServer
from docbuilder.core.exporters.docx_exporter import DocxExporter
from docbuilder.core.exporters.pdf_exporter import PdfExporter
from docbuilder.core.exporters.html_exporter import HtmlExporter
from docbuilder.core.exporters.markdown_exporter import MarkdownExporter

from docbuilder.core.domain.workspace import Workspace
from docbuilder.core.services.dtos import (
    ProjectDTO,
    VolumeDTO,
    PartDTO,
    ChapterDTO,
    DocumentDTO,
)
from docbuilder.core.services.project_services import (
    CreateProjectUseCase,
    LoadProjectUseCase,
    SaveProjectUseCase,
    ImportDocumentUseCase,
    SyncFolderFilesUseCase,
)
from docbuilder.core.services.workspace_services import (
    LoadWorkspaceUseCase,
    SaveWorkspaceUseCase,
    RegisterProjectInWorkspaceUseCase,
)
from docbuilder.core.services.sync_services import SyncProjectUseCase
from docbuilder.core.services.build_services import (
    ValidateProjectUseCase,
    BuildProjectUseCase,
)
from docbuilder.ui.styles import get_stylesheet


class MainWindow(QMainWindow):
    """Janela principal da plataforma GoTryx."""

    def __init__(self, start_workspace_dir: Optional[Path] = None) -> None:
        super().__init__()
        self.setWindowTitle("GoTryx Documentation Platform")
        self.resize(1200, 800)
        self.setStyleSheet(get_stylesheet())

        # Definição do ícone da janela
        icon_path = Path(__file__).parent / "resources" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Instanciação dos Repositórios e Motores
        self._project_repo = ProjectRepository()
        self._template_repo = TemplateRepository()
        self._workspace_repo = WorkspaceRepository()
        self._wiki_server = WikiServer()

        # Definição do workspace ativo
        self.workspace_dir = start_workspace_dir or Path.cwd()
        self.workspace: Optional[Workspace] = None
        self.current_project_dir: Optional[Path] = None
        self.current_project: Optional[ProjectDTO] = None

        # Elementos estruturais de telas (Dashboard e Editor)
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self._init_dashboard_ui()
        self._init_editor_ui()

        # Carrega o Workspace inicial
        self._load_workspace()

    # ==========================================
    # INICIALIZAÇÃO VISUAL: TELA 1 - DASHBOARD
    # ==========================================

    def _init_dashboard_ui(self) -> None:
        """Cria a tela inicial contendo o portfólio de projetos cadastrados."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Cabeçalho do Dashboard
        header_layout = QHBoxLayout()
        lbl_platform = QLabel("GoTryx Documentation Platform")
        lbl_platform.setStyleSheet("font-size: 20px; font-weight: 800; color: #3B82F6;")
        header_layout.addWidget(lbl_platform)
        header_layout.addStretch()

        self.lbl_workspace_name = QLabel("Workspace: Carregando...")
        self.lbl_workspace_name.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_layout.addWidget(self.lbl_workspace_name)
        layout.addLayout(header_layout)

        # Grid/Lista de Projetos
        lbl_title = QLabel("Portfólio de Documentações da Empresa")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(lbl_title)

        # Tabela de Projetos
        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(4)
        self.table_projects.setHorizontalHeaderLabels(
            ["Nome da Documentação", "Versão", "Autor", "Caminho Local"]
        )
        self.table_projects.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_projects.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )
        self.table_projects.setStyleSheet(
            "background-color: #1E293B; border: 1px solid #334155; border-radius: 6px;"
        )
        self.table_projects.itemDoubleClicked.connect(
            self._on_project_table_double_click
        )
        layout.addWidget(self.table_projects)

        # Ações de Gerenciamento do Portfolio
        actions_layout = QHBoxLayout()
        btn_new_proj = QPushButton("Novo Projeto")
        btn_new_proj.setObjectName("accentButton")
        btn_new_proj.clicked.connect(self._on_new_project)

        btn_register_existing = QPushButton("Registrar Projeto Existente")
        btn_register_existing.clicked.connect(self._on_register_existing_project)

        btn_remove_from_ws = QPushButton("Desvincular do Portfolio")
        btn_remove_from_ws.setObjectName("dangerButton")
        btn_remove_from_ws.clicked.connect(self._on_remove_project_from_workspace)

        actions_layout.addWidget(btn_new_proj)
        actions_layout.addWidget(btn_register_existing)
        actions_layout.addWidget(btn_remove_from_ws)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        self.stacked_widget.addWidget(widget)

    # ==========================================
    # INICIALIZAÇÃO VISUAL: TELA 2 - EDITOR
    # ==========================================

    def _init_editor_ui(self) -> None:
        """Cria a tela de edição do projeto selecionado."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Barra Superior do Editor
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton("← Voltar ao Portfólio")
        self.btn_back.clicked.connect(self._on_back_to_dashboard)
        top_bar.addWidget(self.btn_back)

        self.btn_save = QPushButton("Salvar Alterações")
        self.btn_save.clicked.connect(self._on_save_project)
        top_bar.addWidget(self.btn_save)
        top_bar.addStretch()

        # Controles do Servidor Wiki
        server_control_layout = QHBoxLayout()
        self.btn_wiki_server = QPushButton("Iniciar Portal Wiki")
        self.btn_wiki_server.clicked.connect(self._on_toggle_wiki_server)
        self.btn_open_portal = QPushButton("Visualizar no Navegador")
        self.btn_open_portal.setEnabled(False)
        self.btn_open_portal.clicked.connect(self._on_open_portal_url)

        server_control_layout.addWidget(self.btn_wiki_server)
        server_control_layout.addWidget(self.btn_open_portal)
        top_bar.addLayout(server_control_layout)

        top_bar.addStretch()

        self.lbl_active_project = QLabel("Projeto: Nenhum")
        self.lbl_active_project.setStyleSheet(
            "font-weight: bold; color: #3B82F6; font-size: 14px;"
        )
        top_bar.addWidget(self.lbl_active_project)
        layout.addLayout(top_bar)

        # Divisor Horizontal Central
        h_splitter = QSplitter(Qt.Horizontal)

        # Painel Lateral Esquerdo: Árvore do Manifesto
        left_frame = QFrame()
        left_frame.setObjectName("sidebarFrame")
        left_layout = QVBoxLayout(left_frame)
        lbl_sidebar = QLabel("Estrutura do Manifesto")
        lbl_sidebar.setObjectName("panelTitle")
        left_layout.addWidget(lbl_sidebar)

        self.tree_manifest = QTreeWidget()
        self.tree_manifest.setHeaderLabel("Itens do Manifesto")
        self.tree_manifest.setDragEnabled(True)
        self.tree_manifest.setAcceptDrops(True)
        self.tree_manifest.setDragDropMode(QTreeWidget.InternalMove)
        self.tree_manifest.itemSelectionChanged.connect(self._on_item_selected)
        self.tree_manifest.model().rowsMoved.connect(self._on_structure_reordered)
        left_layout.addWidget(self.tree_manifest)

        # Botões da Árvore
        tree_buttons = QHBoxLayout()
        self.btn_add_vol = QPushButton("+ Vol")
        self.btn_add_vol.clicked.connect(self._on_add_volume)
        self.btn_add_part = QPushButton("+ Part")
        self.btn_add_part.clicked.connect(self._on_add_part)
        self.btn_add_cap = QPushButton("+ Cap")
        self.btn_add_cap.clicked.connect(self._on_add_chapter)

        tree_buttons.addWidget(self.btn_add_vol)
        tree_buttons.addWidget(self.btn_add_part)
        tree_buttons.addWidget(self.btn_add_cap)
        left_layout.addLayout(tree_buttons)

        tree_buttons_2 = QHBoxLayout()
        self.btn_import = QPushButton("Importar Doc")
        self.btn_import.clicked.connect(self._on_import_doc)
        self.btn_delete = QPushButton("Remover")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self._on_delete_item)

        tree_buttons_2.addWidget(self.btn_import)
        tree_buttons_2.addWidget(self.btn_delete)
        left_layout.addLayout(tree_buttons_2)

        tree_buttons_3 = QHBoxLayout()
        self.btn_sync_folder = QPushButton("Sincronizar Disco")
        self.btn_sync_folder.clicked.connect(self._on_sync_folder_files)
        tree_buttons_3.addWidget(self.btn_sync_folder)
        left_layout.addLayout(tree_buttons_3)

        h_splitter.addWidget(left_frame)

        # Painel Central: Abas (Visualizador / Pré-visualização)
        center_frame = QFrame()
        center_frame.setObjectName("editorFrame")
        center_layout = QVBoxLayout(center_frame)

        self.tab_editor = QTabWidget()
        self.web_preview = QTextBrowser()
        self.web_preview.setPlaceholderText(
            "Selecione um documento para pré-visualizar o conteúdo."
        )
        self.tab_editor.addTab(self.web_preview, "Pré-visualização do Documento")
        center_layout.addWidget(self.tab_editor)

        h_splitter.addWidget(center_frame)

        # Painel Direito: Formulário de Propriedades
        right_frame = QFrame()
        right_frame.setObjectName("propertiesFrame")
        self.right_layout = QVBoxLayout(right_frame)
        lbl_right = QLabel("Propriedades")
        lbl_right.setObjectName("panelTitle")
        self.right_layout.addWidget(lbl_right)

        self.properties_form = QFormLayout()
        self.right_layout.addLayout(self.properties_form)
        self.right_layout.addStretch()

        h_splitter.addWidget(right_frame)
        h_splitter.setSizes([250, 500, 250])
        layout.addWidget(h_splitter)

        # Rodapé: Painel de Build e Console de Logs
        bottom_layout = QHBoxLayout()

        # Opções de Compilação
        build_frame = QFrame()
        build_frame.setObjectName("sidebarFrame")
        build_layout = QVBoxLayout(build_frame)
        build_layout.addWidget(QLabel("Formatos de Publicação:"))

        self.chk_docx = QCheckBox("Documento Word (DOCX)")
        self.chk_docx.setChecked(True)
        self.chk_pdf = QCheckBox("LibreOffice PDF")
        self.chk_pdf.setChecked(True)
        self.chk_html = QCheckBox("HTML5 Limpo (Portal)")
        self.chk_html.setChecked(True)
        self.chk_markdown = QCheckBox("Markdown Unificado")

        build_layout.addWidget(self.chk_docx)
        build_layout.addWidget(self.chk_pdf)
        build_layout.addWidget(self.chk_html)
        build_layout.addWidget(self.chk_markdown)

        self.btn_validate = QPushButton("Validar Estrutura")
        self.btn_validate.clicked.connect(self._on_validate_project)
        self.btn_build = QPushButton("Publicar")
        self.btn_build.setObjectName("accentButton")
        self.btn_build.clicked.connect(self._on_build_project)

        build_layout.addWidget(self.btn_validate)
        build_layout.addWidget(self.btn_build)
        bottom_layout.addWidget(build_frame)

        # Console de Logs
        log_frame = QFrame()
        log_frame.setObjectName("logFrame")
        log_layout = QVBoxLayout(log_frame)
        log_layout.addWidget(QLabel("Log de Publicação e Compilação"))

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        bottom_layout.addWidget(log_frame)

        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.addWidget(build_frame)
        bottom_splitter.addWidget(log_frame)
        bottom_splitter.setSizes([250, 750])
        layout.addWidget(bottom_splitter)

        self.stacked_widget.addWidget(widget)

    def _set_editor_buttons_enabled(self, enabled: bool) -> None:
        """Habilita ou desabilita os botões do editor para evitar concorrência durante o build."""
        self.btn_back.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        self.btn_wiki_server.setEnabled(enabled)
        if enabled:
            self.btn_open_portal.setEnabled(self._wiki_server.is_running())
        else:
            self.btn_open_portal.setEnabled(False)

        self.btn_add_vol.setEnabled(enabled)
        self.btn_add_part.setEnabled(enabled)
        self.btn_add_cap.setEnabled(enabled)
        self.btn_import.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.btn_sync_folder.setEnabled(enabled)
        self.btn_validate.setEnabled(enabled)
        self.btn_build.setEnabled(enabled)
        self.tree_manifest.setEnabled(enabled)

    # ==========================================
    # LOGS E FLUXO DO PORTFÓLIO (TELA 1)
    # ==========================================

    def _log_info(self, text: str) -> None:
        self.txt_log.append(f"[INFO] {text}")

    def _log_warning(self, text: str) -> None:
        self.txt_log.append(f'<span style="color: #FBBF24;">[AVISO] {text}</span>')

    def _log_error(self, text: str) -> None:
        self.txt_log.append(f'<span style="color: #EF4444;">[ERRO] {text}</span>')

    def _load_workspace(self) -> None:
        """Carrega a lista de projetos do workspace.yaml."""
        load_use_case = LoadWorkspaceUseCase(self._workspace_repo)
        try:
            self.workspace = load_use_case.execute(self.workspace_dir)
            self.lbl_workspace_name.setText(f"Workspace: {self.workspace.name}")
            self._rebuild_projects_table()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Não foi possível carregar o portfólio:\n{e}"
            )

    def _rebuild_projects_table(self) -> None:
        """Popula a tabela do Dashboard com as informações de metadados de cada projeto."""
        self.table_projects.setRowCount(0)
        if not self.workspace:
            return

        # Escaneia os projetos locais válidos cadastrados no workspace
        valid_paths = []
        for path_str in self.workspace.project_paths:
            path = Path(path_str)
            manifest_file = path / "manifest.yaml"
            if not manifest_file.exists():
                # Removido ou indisponível
                continue

            valid_paths.append(path_str)

            try:
                # Carrega metadados rápidos do manifesto
                project_dto = LoadProjectUseCase(self._project_repo).execute(path)

                row = self.table_projects.rowCount()
                self.table_projects.insertRow(row)

                self.table_projects.setItem(row, 0, QTableWidgetItem(project_dto.name))
                self.table_projects.setItem(
                    row, 1, QTableWidgetItem(project_dto.version)
                )
                self.table_projects.setItem(
                    row, 2, QTableWidgetItem(project_dto.author)
                )

                path_item = QTableWidgetItem(str(path))
                path_item.setToolTip(str(path))
                self.table_projects.setItem(row, 3, QTableWidgetItem(path_item))
            except Exception:
                # Se corrompido, exibe informações parciais
                row = self.table_projects.rowCount()
                self.table_projects.insertRow(row)
                self.table_projects.setItem(
                    row, 0, QTableWidgetItem("Projeto Corrompido / Inválido")
                )
                self.table_projects.setItem(row, 1, QTableWidgetItem("-"))
                self.table_projects.setItem(row, 2, QTableWidgetItem("-"))
                self.table_projects.setItem(row, 3, QTableWidgetItem(str(path)))

        # Atualiza a lista caso projetos indisponíveis tenham sido ignorados
        if len(valid_paths) != len(self.workspace.project_paths):
            self.workspace.project_paths = valid_paths
            SaveWorkspaceUseCase(self._workspace_repo).execute(
                self.workspace, self.workspace_dir
            )

    def _on_project_table_double_click(self, item: QTableWidgetItem) -> None:
        """Ao clicar duas vezes em um projeto na tabela, abre o respectivo editor."""
        row = item.row()
        path_item = self.table_projects.item(row, 3)
        if path_item:
            project_path = Path(path_item.text())
            self._open_project_in_editor(project_path)

    def _open_project_in_editor(self, project_path: Path) -> None:
        """Carrega o projeto e transiciona a tela para o editor."""
        load_use_case = LoadProjectUseCase(self._project_repo)
        try:
            self.current_project = load_use_case.execute(project_path)
            self.current_project_dir = project_path

            # Atualiza labels do Editor
            self.lbl_active_project.setText(
                f"Projeto: {self.current_project.name} (v{self.current_project.version})"
            )
            self._rebuild_tree_widget()

            # Limpa logs e previews anteriores
            self.txt_log.clear()
            self.web_preview.setHtml("")

            # Se o servidor Wiki estiver rodando de outro projeto, encerra
            self._wiki_server.stop()
            self.btn_wiki_server.setText("Iniciar Portal Wiki")
            self.btn_open_portal.setEnabled(False)

            # Sobe a tela do editor
            self.stacked_widget.setCurrentIndex(1)
            self._log_info(f"Edição aberta: '{self.current_project.name}'")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao abrir",
                f"Não foi possível ler os arquivos do projeto:\n{e}",
            )

    def _on_back_to_dashboard(self) -> None:
        """Fecha o editor ativo, encerra o servidor web e retorna ao portfólio."""
        self._wiki_server.stop()
        self.current_project = None
        self.current_project_dir = None
        self._rebuild_projects_table()
        self.stacked_widget.setCurrentIndex(0)

    # ==========================================
    # EVENTOS DE GERENCIAMENTO DE PROJETOS
    # ==========================================

    def _on_new_project(self) -> None:
        """Cria e cadastra um novo projeto de documentação corporativa."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecione o diretório para criar o novo projeto"
        )
        if not folder:
            return

        folder_path = Path(folder)

        # Validação: se a pasta já contém um projeto (manifest.yaml), avisa e cancela
        manifest_file = folder_path / "manifest.yaml"
        if manifest_file.exists():
            QMessageBox.warning(
                self,
                "Projeto Existente",
                "O diretório selecionado já possui um controle de projeto ativo (manifest.yaml).\n\n"
                "Para utilizá-lo, use a opção 'Vincular Pasta Existente' no Dashboard principal.",
            )
            return

        create_use_case = CreateProjectUseCase(self._project_repo)
        try:
            self.current_project = create_use_case.execute(
                name="Manual Corporativo Gotryx",
                author="Administração GoTryx",
                language="pt-BR",
                template="Corporate",
                target_dir=folder_path,
            )
            self.current_project_dir = folder_path

            # Registra no Workspace e reconstrói tabela
            register_use_case = RegisterProjectInWorkspaceUseCase(self._workspace_repo)
            self.workspace = register_use_case.execute(folder_path, self.workspace_dir)
            self._rebuild_projects_table()

            # Abre no editor diretamente
            self._open_project_in_editor(folder_path)
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Não foi possível criar o projeto:\n{e}"
            )

    def _on_register_existing_project(self) -> None:
        """Registra uma pasta de documentação existente no Workspace."""
        folder = QFileDialog.getExistingDirectory(
            self, "Selecione a pasta do projeto contendo o manifest.yaml"
        )
        if not folder:
            return

        folder_path = Path(folder)
        manifest_file = folder_path / "manifest.yaml"
        if not manifest_file.exists():
            QMessageBox.critical(
                self,
                "Erro de Manifesto",
                "O diretório selecionado não é um projeto válido do GoTryx Builder.\n"
                "Certifique-se de que o arquivo 'manifest.yaml' existe na pasta.",
            )
            return

        try:
            register_use_case = RegisterProjectInWorkspaceUseCase(self._workspace_repo)
            self.workspace = register_use_case.execute(folder_path, self.workspace_dir)
            self._rebuild_projects_table()
            QMessageBox.information(
                self, "Sucesso", "Documentação vinculada com sucesso ao portfólio!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao registrar", f"Erro: {e}")

    def _on_remove_project_from_workspace(self) -> None:
        """Desvincula a pasta do projeto do workspace (sem apagar os arquivos físicos)."""
        selected_row = self.table_projects.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Alerta", "Selecione um projeto na tabela para desvincular."
            )
            return

        path_item = self.table_projects.item(selected_row, 3)
        if path_item and self.workspace:
            proj_path = Path(path_item.text())

            confirm = QMessageBox.question(
                self,
                "Desvincular Projeto",
                f"Tem certeza de que deseja desvincular o projeto '{self.table_projects.item(selected_row, 0).text()}' do portfólio?\n"
                "Os arquivos físicos da pasta não serão deletados.",
                QMessageBox.Yes | QMessageBox.No,
            )

            if confirm == QMessageBox.Yes:
                self.workspace.unregister_project(proj_path)
                SaveWorkspaceUseCase(self._workspace_repo).execute(
                    self.workspace, self.workspace_dir
                )
                self._rebuild_projects_table()

    # ==========================================
    # CONTROLE DO SERVIDOR WIKI E PORTAL
    # ==========================================

    def _on_toggle_wiki_server(self) -> None:
        """Liga ou desliga o servidor Wiki local para visualização interativa do HTML gerado."""
        if not self.current_project_dir:
            return

        dist_dir = self.current_project_dir / "dist"

        if self._wiki_server.is_running():
            self._wiki_server.stop()
            self.btn_wiki_server.setText("Iniciar Portal Wiki")
            self.btn_open_portal.setEnabled(False)
            self._log_info("Servidor do Portal Wiki Local encerrado.")
        else:
            if not dist_dir.exists() or not list(dist_dir.glob("*.html")):
                QMessageBox.warning(
                    self,
                    "Portal Wiki",
                    "Nenhuma compilação HTML encontrada no diretório 'dist/'.\n"
                    "Gere a documentação marcando o formato 'HTML5 Limpo' antes de abrir o Portal.",
                )
                return

            try:
                if self._wiki_server.start(dist_dir, port=8080):
                    self.btn_wiki_server.setText("Parar Portal Wiki")
                    self.btn_open_portal.setEnabled(True)
                    self._log_info(
                        f"Portal Wiki Local iniciado em: {self._wiki_server.get_url()}"
                    )
                    # Abre automaticamente na primeira vez
                    webbrowser.open(self._wiki_server.get_url())
                else:
                    self._log_error("Falha ao iniciar o servidor Wiki local.")
            except Exception as e:
                self._log_error(f"Erro ao ligar servidor Wiki: {e}")

    def _on_open_portal_url(self) -> None:
        if self._wiki_server.is_running():
            webbrowser.open(self._wiki_server.get_url())

    # ==========================================
    # MANIPULAÇÃO DA ESTRUTURA DO PROJETO (TELA 2)
    # ==========================================

    def _on_save_project(self) -> None:
        if not self.current_project or not self.current_project_dir:
            return

        self._synchronize_dto_from_tree()

        save_use_case = SaveProjectUseCase(self._project_repo)
        try:
            save_use_case.execute(self.current_project, self.current_project_dir)
            self._log_info("Alterações salvas com sucesso no manifesto do projeto.")
            self.lbl_active_project.setText(
                f"Projeto: {self.current_project.name} (v{self.current_project.version})"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro ao Salvar", f"Não foi possível salvar:\n{e}"
            )

    def _rebuild_tree_widget(self) -> None:
        self.tree_manifest.clear()
        if not self.current_project:
            return

        root_item = QTreeWidgetItem(self.tree_manifest)
        root_item.setText(0, self.current_project.name)
        root_item.setData(0, Qt.UserRole, "PROJECT")
        root_item.setData(1, Qt.UserRole, "root")
        self.tree_manifest.addTopLevelItem(root_item)

        for vol in self.current_project.volumes:
            vol_item = QTreeWidgetItem(root_item)
            vol_item.setText(0, vol.title)
            vol_item.setData(0, Qt.UserRole, "VOLUME")
            vol_item.setData(1, Qt.UserRole, vol.id)
            vol_item.setFlags(
                vol_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
            )

            for part in vol.parts:
                part_item = QTreeWidgetItem(vol_item)
                part_item.setText(0, part.title)
                part_item.setData(0, Qt.UserRole, "PART")
                part_item.setData(1, Qt.UserRole, part.id)
                part_item.setFlags(
                    part_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
                )

                for cap in part.chapters:
                    cap_item = QTreeWidgetItem(part_item)
                    cap_item.setText(0, cap.title)
                    cap_item.setData(0, Qt.UserRole, "CHAPTER")
                    cap_item.setData(1, Qt.UserRole, cap.id)
                    cap_item.setFlags(
                        cap_item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
                    )

                    for doc in cap.documents:
                        doc_item = QTreeWidgetItem(cap_item)
                        doc_item.setText(0, doc.title)
                        doc_item.setData(0, Qt.UserRole, "DOCUMENT")
                        doc_item.setData(1, Qt.UserRole, doc.id)
                        doc_item.setData(2, Qt.UserRole, doc.file_path)
                        doc_item.setData(3, Qt.UserRole, doc.format)
                        doc_item.setFlags(doc_item.flags() | Qt.ItemIsDragEnabled)

        self.tree_manifest.expandAll()

    def _synchronize_dto_from_tree(self) -> None:
        if not self.current_project:
            return

        root_item = self.tree_manifest.topLevelItem(0)
        new_volumes = []
        for i in range(root_item.childCount()):
            vol_item = root_item.child(i)
            if vol_item.data(0, Qt.UserRole) != "VOLUME":
                continue
            vol_dto = VolumeDTO(
                id=vol_item.data(1, Qt.UserRole), title=vol_item.text(0), parts=[]
            )
            for j in range(vol_item.childCount()):
                part_item = vol_item.child(j)
                if part_item.data(0, Qt.UserRole) != "PART":
                    continue
                part_dto = PartDTO(
                    id=part_item.data(1, Qt.UserRole),
                    title=part_item.text(0),
                    chapters=[],
                )
                for k in range(part_item.childCount()):
                    cap_item = part_item.child(k)
                    if cap_item.data(0, Qt.UserRole) != "CHAPTER":
                        continue
                    cap_dto = ChapterDTO(
                        id=cap_item.data(1, Qt.UserRole),
                        title=cap_item.text(0),
                        documents=[],
                    )
                    for idx_doc in range(cap_item.childCount()):
                        doc_item = cap_item.child(idx_doc)
                        if doc_item.data(0, Qt.UserRole) != "DOCUMENT":
                            continue
                        doc_dto = DocumentDTO(
                            id=doc_item.data(1, Qt.UserRole),
                            title=doc_item.text(0),
                            file_path=doc_item.data(2, Qt.UserRole),
                            format=doc_item.data(3, Qt.UserRole) or "markdown",
                        )
                        cap_dto.documents.append(doc_dto)
                    part_dto.chapters.append(cap_dto)
                vol_dto.parts.append(part_dto)
            new_volumes.append(vol_dto)

        self.current_project.volumes = new_volumes

    def _on_item_selected(self) -> None:
        while self.properties_form.count():
            item = self.properties_form.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        selected = self.tree_manifest.currentItem()
        if not selected:
            return

        item_type = selected.data(0, Qt.UserRole)

        if item_type == "PROJECT":
            self._show_project_properties()
        elif item_type in ["VOLUME", "PART", "CHAPTER"]:
            self._show_structural_properties(selected)
        elif item_type == "DOCUMENT":
            self._show_document_properties(selected)

    def _show_project_properties(self) -> None:
        if not self.current_project:
            return

        self.properties_form.addRow(QLabel("<b>Metadados do Projeto</b>"))

        txt_name = QLineEdit(self.current_project.name)
        txt_name.textChanged.connect(self._update_project_name_live)
        self.properties_form.addRow("Nome:", txt_name)

        txt_author = QLineEdit(self.current_project.author)
        txt_author.textChanged.connect(
            lambda t: setattr(self.current_project, "author", t)
        )
        self.properties_form.addRow("Autor:", txt_author)

        txt_version = QLineEdit(self.current_project.version)
        txt_version.textChanged.connect(
            lambda t: setattr(self.current_project, "version", t)
        )
        self.properties_form.addRow("Versão:", txt_version)

        txt_lang = QLineEdit(self.current_project.language)
        txt_lang.textChanged.connect(
            lambda t: setattr(self.current_project, "language", t)
        )
        self.properties_form.addRow("Idioma:", txt_lang)

        cmb_template = QComboBox()
        cmb_template.addItems(self._template_repo.list_available_templates())
        cmb_template.setCurrentText(self.current_project.template_name)
        cmb_template.currentTextChanged.connect(
            lambda t: setattr(self.current_project, "template_name", t)
        )
        self.properties_form.addRow("Estilo de Template:", cmb_template)

        cmb_structure = QComboBox()
        cmb_structure.addItem("Fluido (Linear)", "fluid")
        cmb_structure.addItem("Estruturado (Por Pastas)", "folders")
        current_mode = getattr(self.current_project, "structure_mode", "fluid")
        idx = cmb_structure.findData(current_mode)
        if idx >= 0:
            cmb_structure.setCurrentIndex(idx)
        cmb_structure.currentIndexChanged.connect(
            lambda i: setattr(
                self.current_project, "structure_mode", cmb_structure.itemData(i)
            )
        )
        self.properties_form.addRow("Organização do Disco:", cmb_structure)

        # Sincronização Git Cloud
        self.properties_form.addRow(
            QLabel("<b>Publicação e Controle de Versão (Git)</b>")
        )

        # Recupera URL remota configurada (se houver)
        remote_url_str = (
            self.current_project.global_settings.get("remote_url", "")
            if hasattr(self.current_project, "global_settings")
            else ""
        )
        self.txt_remote_url = QLineEdit(remote_url_str)
        self.txt_remote_url.setPlaceholderText("https://github.com/empresa/repo.git")
        self.txt_remote_url.textChanged.connect(self._validate_git_sync_state)
        self.properties_form.addRow("Repos. Remoto:", self.txt_remote_url)

        self.btn_sync = QPushButton("Sincronizar Cloud (Git Push)")
        self.btn_sync.clicked.connect(self._on_sync_git)
        self.properties_form.addRow(self.btn_sync)

        # Valida o estado inicial do botão de sincronização
        self._validate_git_sync_state()

    def _validate_git_sync_state(self) -> None:
        """Habilita o botão de sincronização Git apenas se houver repositório remoto informado e repositório Git local válido."""
        try:
            if not hasattr(self, "btn_sync") or not hasattr(self, "txt_remote_url"):
                return
            # Verifica se os widgets do C++ não foram deletados da tela
            self.btn_sync.parent()
            self.txt_remote_url.parent()
        except RuntimeError:
            return

        remote_url = self.txt_remote_url.text().strip()

        # 1. Campo não pode estar vazio
        if not remote_url:
            self.btn_sync.setEnabled(False)
            self.btn_sync.setToolTip(
                "Insira a URL do repositório remoto para habilitar a sincronização."
            )
            return

        # 2. O diretório do projeto deve possuir um repositório Git inicializado (.git existe)
        is_git_repo = False
        if self.current_project_dir:
            is_git_repo = (self.current_project_dir / ".git").exists()

        if not is_git_repo:
            self.btn_sync.setEnabled(False)
            self.btn_sync.setToolTip(
                "O diretório ativo do projeto não possui um repositório Git inicializado (.git)."
            )
            return

        # 3. Validação de prefixo básico da URL
        valid_prefixes = ("http://", "https://", "git@", "ssh://")
        is_valid_url = any(remote_url.startswith(p) for p in valid_prefixes)

        if not is_valid_url:
            self.btn_sync.setEnabled(False)
            self.btn_sync.setToolTip(
                "URL remota inválida. Use formatos HTTPS (https://) ou SSH (git@)."
            )
            return

        # Passou em todas as validações, ativa o botão
        self.btn_sync.setEnabled(True)
        self.btn_sync.setToolTip(
            "Clique para sincronizar suas alterações com o repositório remoto (Git Push)."
        )

    def _update_project_name_live(self, text: str) -> None:
        if self.current_project:
            self.current_project.name = text
            self.tree_manifest.topLevelItem(0).setText(0, text)

    def _on_sync_git(self) -> None:
        """Caso de uso de sincronização automática com repositório Git."""
        if not self.current_project_dir or not self.current_project:
            return

        # Sincroniza primeiro o DTO local e salva no manifest
        self._on_save_project()

        self._log_info("Iniciando publicação automática no Git...")

        # Armazena a URL no DTO
        if not hasattr(self.current_project, "global_settings"):
            self.current_project.global_settings = {}

        remote_url = self.txt_remote_url.text().strip()
        self.current_project.global_settings["remote_url"] = remote_url

        # Salva o manifest atualizado com a URL
        SaveProjectUseCase(self._project_repo).execute(
            self.current_project, self.current_project_dir
        )

        # Instancia e roda a sincronização
        git_prov = GitStorage()
        sync_use_case = SyncProjectUseCase(git_prov)

        credentials = {"remote_url": remote_url} if remote_url else {}

        success = sync_use_case.execute(self.current_project_dir, credentials)
        if success:
            self._log_info(
                "Documentação publicada e tag de release criada com sucesso no repositório local/remoto!"
            )
            QMessageBox.information(
                self,
                "Sincronização",
                "Repositório sincronizado e tag de release criada!",
            )
        else:
            self._log_error(
                "Falha ao sincronizar projeto com o controle de versão Git."
            )
            QMessageBox.critical(
                self, "Sincronização", "Ocorreu um erro ao rodar a sincronização Git."
            )

    def _show_structural_properties(self, item: QTreeWidgetItem) -> None:
        self.properties_form.addRow(
            QLabel(f"<b>Metadados do {item.data(0, Qt.UserRole).title()}</b>")
        )
        txt_title = QLineEdit(item.text(0))
        txt_title.textChanged.connect(item.setText)
        self.properties_form.addRow("Título:", txt_title)

    def _show_document_properties(self, item: QTreeWidgetItem) -> None:
        self.properties_form.addRow(QLabel("<b>Metadados do Documento</b>"))
        txt_title = QLineEdit(item.text(0))
        txt_title.textChanged.connect(item.setText)
        self.properties_form.addRow("Título:", txt_title)

        txt_file = QLineEdit(item.data(2, Qt.UserRole) or "")
        txt_file.setReadOnly(True)
        self.properties_form.addRow("Arquivo:", txt_file)

        # Visualização
        if self.current_project_dir:
            rel_path = item.data(2, Qt.UserRole)
            if rel_path:
                full_path = self.current_project_dir / rel_path
                self._load_document_preview(full_path, item.data(3, Qt.UserRole))

    def _load_document_preview(self, file_path: Path, doc_format: str) -> None:
        if not file_path.exists():
            self.web_preview.setHtml(
                "<span style='color: red;'>Erro: Arquivo físico ausente.</span>"
            )
            return
        try:
            # Pré-visualização nativa para arquivos DOCX
            if doc_format == "docx":
                import docx

                doc = docx.Document(file_path)
                html_parts = []
                for p in doc.paragraphs:
                    text = p.text.strip()
                    if text:
                        if p.style.name.startswith("Heading"):
                            html_parts.append(f"<h3>{text}</h3>")
                        else:
                            html_parts.append(f"<p>{text}</p>")
                if not html_parts:
                    self.web_preview.setHtml(
                        "<p><i>[Documento DOCX vazio ou sem parágrafos de texto]</i></p>"
                    )
                else:
                    self.web_preview.setHtml("".join(html_parts))
                return

            # Pré-visualização para formatos de texto plano
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    text = f.read()

            if doc_format in ["markdown", "md"]:
                import markdown

                html = markdown.markdown(text, extensions=["tables", "fenced_code"])
                self.web_preview.setHtml(html)
            elif doc_format in ["html", "txt"]:
                self.web_preview.setHtml(text)
            else:
                self.web_preview.setHtml(
                    f"<i>Sem preview disponível para {doc_format.upper()}.</i>"
                )
        except Exception as e:
            self.web_preview.setHtml(
                f"<span style='color: red;'>Erro de leitura: {e}</span>"
            )

    # ==========================================
    # ADIÇÃO E REMOÇÃO DE SEÇÕES (TELA 2)
    # ==========================================

    def _on_add_volume(self) -> None:
        root = self.tree_manifest.topLevelItem(0)
        vol_id = str(uuid4())
        item = QTreeWidgetItem(root)
        item.setText(0, "Novo Volume")
        item.setData(0, Qt.UserRole, "VOLUME")
        item.setData(1, Qt.UserRole, vol_id)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.tree_manifest.expandItem(root)

    def _on_add_part(self) -> None:
        selected = self.tree_manifest.currentItem()
        if not selected or selected.data(0, Qt.UserRole) != "VOLUME":
            QMessageBox.warning(self, "Alerta", "Selecione um Volume antes.")
            return
        part_id = str(uuid4())
        item = QTreeWidgetItem(selected)
        item.setText(0, "Nova Parte")
        item.setData(0, Qt.UserRole, "PART")
        item.setData(1, Qt.UserRole, part_id)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.tree_manifest.expandItem(selected)

    def _on_add_chapter(self) -> None:
        selected = self.tree_manifest.currentItem()
        if not selected or selected.data(0, Qt.UserRole) != "PART":
            QMessageBox.warning(self, "Alerta", "Selecione uma Parte antes.")
            return
        cap_id = str(uuid4())
        item = QTreeWidgetItem(selected)
        item.setText(0, "Novo Capítulo")
        item.setData(0, Qt.UserRole, "CHAPTER")
        item.setData(1, Qt.UserRole, cap_id)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.tree_manifest.expandItem(selected)

    def _on_import_doc(self) -> None:
        if not self.current_project_dir:
            return
        selected = self.tree_manifest.currentItem()
        if not selected or selected.data(0, Qt.UserRole) != "CHAPTER":
            QMessageBox.warning(
                self, "Alerta", "Selecione um Capítulo na árvore antes."
            )
            return

        file_filter = "Arquivos Suportados (*.md *.markdown *.docx *.odt *.txt *.html)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Documento", "", file_filter
        )
        if not file_path:
            return

        import_use_case = ImportDocumentUseCase()
        try:
            doc_dto = import_use_case.execute(Path(file_path), self.current_project_dir)
            doc_id = str(uuid4())
            item = QTreeWidgetItem(selected)
            item.setText(0, doc_dto.title)
            item.setData(0, Qt.UserRole, "DOCUMENT")
            item.setData(1, Qt.UserRole, doc_id)
            item.setData(2, Qt.UserRole, doc_dto.file_path)
            item.setData(3, Qt.UserRole, doc_dto.format)
            item.setFlags(item.flags() | Qt.ItemIsDragEnabled)
            self.tree_manifest.expandItem(selected)
            self._log_info(f"Documento '{doc_dto.title}' importado com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _on_sync_folder_files(self) -> None:
        """Sincroniza a árvore do manifesto com novos arquivos adicionados fisicamente ao disco."""
        if not self.current_project or not self.current_project_dir:
            return

        # Sincroniza primeiro o estado atual da árvore visual da UI para o DTO
        self._synchronize_dto_from_tree()

        self._log_info("Buscando novos arquivos físicos no disco...")

        # Converte o DTO para Entidade para processar no caso de uso
        from docbuilder.core.services.project_services import ProjectMappingHelper

        project_entity = ProjectMappingHelper.dto_to_entity(self.current_project)

        use_case = SyncFolderFilesUseCase(self._project_repo)
        try:
            added_titles = use_case.execute(project_entity, self.current_project_dir)

            if added_titles:
                self._log_info(
                    f"Sincronização concluída. Adicionados {len(added_titles)} documentos: {', '.join(added_titles)}"
                )
                # Atualiza o DTO local
                self.current_project = ProjectMappingHelper.entity_to_dto(
                    project_entity
                )
                # Reconstrói a árvore gráfica
                self._rebuild_tree_widget()
                QMessageBox.information(
                    self,
                    "Sincronização de Disco",
                    f"Sincronização concluída com sucesso!\n\nForam encontrados e adicionados {len(added_titles)} novos documentos no manifesto:\n"
                    + "\n".join(f"- {title}" for title in added_titles),
                )
            else:
                self._log_info(
                    "Sincronização concluída. Nenhum novo documento físico encontrado."
                )
                QMessageBox.information(
                    self,
                    "Sincronização de Disco",
                    "Sincronização concluída!\nNenhum arquivo novo foi encontrado no diretório do projeto.",
                )
        except Exception as e:
            self._log_error(f"Erro ao sincronizar pasta física: {e}")
            QMessageBox.critical(
                self, "Erro na Sincronização", f"Não foi possível sincronizar:\n{e}"
            )

    def _on_delete_item(self) -> None:
        selected = self.tree_manifest.currentItem()
        if not selected or selected.data(0, Qt.UserRole) == "PROJECT":
            return
        parent = selected.parent()
        if parent:
            parent.removeChild(selected)
            self._log_info("Item removido. Salve as alterações para gravar.")

    def _on_structure_reordered(self, *args) -> None:
        self._log_info(
            "Estrutura reordenada por Drag & Drop. Salve as alterações para gravar."
        )

    # ==========================================
    # PIPELINE DE BUILD E VALIDAÇÃO (TELA 2)
    # ==========================================

    def _on_validate_project(self) -> None:
        if not self.current_project or not self.current_project_dir:
            return
        self._synchronize_dto_from_tree()
        self.txt_log.clear()
        self._log_info("Validando documentação...")
        result = ValidateProjectUseCase(self._template_repo).execute(
            self.current_project, self.current_project_dir
        )

        if result.is_valid:
            self._log_info("Validação concluída: Projeto consistente!")
            QMessageBox.information(
                self, "Validação", "Estrutura do projeto está consistente!"
            )
        else:
            self._log_error("Validação concluída: Erros impeditivos encontrados!")
            QMessageBox.warning(
                self, "Validação", "Erros estruturais encontrados. Verifique o console."
            )

        for warn in result.warnings:
            self._log_warning(warn)
        for err in result.errors:
            self._log_error(err)

    def _on_build_project(self) -> None:
        if not self.current_project or not self.current_project_dir:
            return

        # Desabilita todos os botões e interações do editor durante o build
        self._set_editor_buttons_enabled(False)
        QApplication.processEvents()  # Força o Qt a processar e pintar as alterações da UI na tela imediatamente

        try:
            self._synchronize_dto_from_tree()
            self.txt_log.clear()

            formats = []
            if self.chk_docx.isChecked():
                formats.append("docx")
            if self.chk_pdf.isChecked():
                formats.append("pdf")
            if self.chk_html.isChecked():
                formats.append("html")
            if self.chk_markdown.isChecked():
                formats.append("md")

            if not formats:
                QMessageBox.warning(
                    self, "Alerta", "Selecione ao menos um formato de saída."
                )
                return

            # Validação automática
            self._log_info("Validando antes de publicar...")
            val_result = ValidateProjectUseCase(self._template_repo).execute(
                self.current_project, self.current_project_dir
            )
            if not val_result.is_valid:
                self._log_error("Cancelado devido a inconsistências:")
                for err in val_result.errors:
                    self._log_error(err)
                return

            # Executa Build
            docx_exp = DocxExporter()
            pdf_exp = PdfExporter(docx_exp)
            html_exp = HtmlExporter()
            md_exp = MarkdownExporter()

            use_case = BuildProjectUseCase(
                self._template_repo,
                DocumentBuilder(),
                [docx_exp, pdf_exp, html_exp, md_exp],
            )
            self._log_info("Iniciando compilação de publicação...")
            result = use_case.execute(
                self.current_project, self.current_project_dir, formats
            )

            for log in result.logs:
                if "ERRO" in log or "Erro" in log:
                    self._log_error(log)
                elif "Aviso" in log or "AVISO" in log:
                    self._log_warning(log)
                else:
                    self._log_info(log)

            if result.success:
                self._log_info("Publicação concluída com sucesso!")
                QMessageBox.information(
                    self, "Sucesso", "Documentação gerada com sucesso na pasta dist/!"
                )
                # Se o servidor Wiki estiver rodando, reinicia-o silenciosamente para atualizar o conteúdo
                if self._wiki_server.is_running():
                    self._wiki_server.stop()
                    self._wiki_server.start(
                        self.current_project_dir / "dist", port=8080
                    )
            else:
                QMessageBox.critical(self, "Falha de Publicação", result.message)
        finally:
            # Garante reabilitar todos os botões e a árvore ao final da publicação
            self._set_editor_buttons_enabled(True)

    def closeEvent(self, event) -> None:
        """Garante fechar o servidor Wiki ao fechar a janela principal."""
        self._wiki_server.stop()
        event.accept()


def run_app(workspace_dir: Optional[Path] = None) -> None:
    app = QApplication(sys.argv)
    window = MainWindow(workspace_dir)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
Pre_push = True
