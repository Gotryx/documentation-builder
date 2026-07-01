"""
Estilos e definições visuais da interface gráfica (PySide6) do GoTryx Documentation Builder.
Utiliza uma folha de estilos QSS premium focada em uma experiência de uso refinada (Dark mode).
"""


def get_stylesheet() -> str:
    """Retorna o QSS correspondente ao tema Dark Premium da GoTryx."""
    return """
    /* Paleta de Cores GoTryx:
       Background Principal: #0F172A
       Background Secundário: #1E293B
       Bordas: #334155
       Texto Principal: #F8FAFC
       Texto Secundário: #94A3B8
       Azul Accent: #3B82F6
       Azul Hover: #2563EB
       Danger/Alerta: #EF4444
       Sucesso/Concluído: #10B981
    */

    QMainWindow {
        background-color: #0F172A;
    }

    QWidget {
        color: #F8FAFC;
        font-family: "Segoe UI", "Inter", "Helvetica", sans-serif;
        font-size: 13px;
    }

    /* Painel Lateral e Containers */
    QFrame#sidebarFrame, QFrame#propertiesFrame, QFrame#logFrame, QFrame#editorFrame {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
    }

    /* Menu Lateral / Árvore de Projeto */
    QTreeView {
        background-color: #1E293B;
        border: none;
        color: #E2E8F0;
        show-decoration-selected: 1;
        outline: 0;
        padding: 5px;
    }

    QTreeView::item {
        padding: 6px;
        border-radius: 4px;
        margin-bottom: 2px;
    }

    QTreeView::item:hover {
        background-color: #334155;
        color: #F8FAFC;
    }

    QTreeView::item:selected {
        background-color: #3B82F6;
        color: #FFFFFF;
        font-weight: bold;
    }

    QTreeView::branch {
        background: transparent;
    }

    /* Cabeçalhos de Seção / Títulos */
    QLabel#panelTitle {
        font-size: 15px;
        font-weight: 700;
        color: #3B82F6;
        padding-bottom: 6px;
        border-bottom: 1px solid #334155;
        margin-bottom: 8px;
    }

    /* Campos de Entrada e ComboBoxes */
    QLineEdit, QComboBox, QSpinBox {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 4px;
        padding: 6px 10px;
        color: #F8FAFC;
    }

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border: 1px solid #3B82F6;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    /* Botões Premium */
    QPushButton {
        background-color: #334155;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        color: #F8FAFC;
    }

    QPushButton:hover {
        background-color: #475569;
        border-color: #64748B;
    }

    QPushButton:pressed {
        background-color: #1E293B;
    }

    QPushButton#accentButton {
        background-color: #3B82F6;
        border: 1px solid #2563EB;
        color: #FFFFFF;
    }

    QPushButton#accentButton:hover {
        background-color: #2563EB;
    }

    QPushButton#dangerButton {
        background-color: #EF4444;
        border: 1px solid #DC2626;
        color: #FFFFFF;
    }

    QPushButton#dangerButton:hover {
        background-color: #DC2626;
    }

    /* Estado Desabilitado (Disabled) - Cores Apagadas e Foscas */
    QPushButton:disabled, QPushButton#accentButton:disabled, QPushButton#dangerButton:disabled {
        background-color: #0F172A;
        border: 1px dashed #334155;
        color: #64748B;
    }

    /* Console de Logs / Editor de texto */
    QTextEdit {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #F1F5F9;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
        padding: 8px;
    }

    /* Abas do Editor (QTabWidget) */
    QTabWidget::pane {
        border: 1px solid #334155;
        background-color: #1E293B;
        border-radius: 6px;
        top: -1px;
    }

    QTabBar::tab {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-bottom-color: transparent;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 16px;
        margin-right: 2px;
        color: #94A3B8;
    }

    QTabBar::tab:hover {
        background-color: #334155;
        color: #F8FAFC;
    }

    QTabBar::tab:selected {
        background-color: #1E293B;
        color: #3B82F6;
        border-bottom-color: #1E293B;
        font-weight: 600;
    }

    /* Scrollbars Modernas */
    QScrollBar:vertical {
        border: none;
        background: #0F172A;
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: #475569;
        min-height: 20px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical:hover {
        background: #64748B;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }

    /* Estilização explícita de QMessageBox e Diálogos para evitar texto invisível (branco no claro) */
    QMessageBox {
        background-color: #1E293B;
        border: 1px solid #334155;
    }

    QMessageBox QLabel {
        color: #F8FAFC;
        background-color: transparent;
        font-size: 13px;
        min-width: 250px;
    }

    QMessageBox QPushButton {
        background-color: #334155;
        border: 1px solid #475569;
        border-radius: 4px;
        color: #F8FAFC;
        padding: 6px 14px;
        min-width: 70px;
    }

    QMessageBox QPushButton:hover {
        background-color: #475569;
    }

    QFileDialog {
        background-color: #1E293B;
        color: #F8FAFC;
    }

    QFileDialog QLabel {
        color: #F8FAFC;
    }

    QFileDialog QListView, QFileDialog QTreeView {
        background-color: #0F172A;
        color: #E2E8F0;
        border: 1px solid #334155;
    }

    QFileDialog QLineEdit {
        background-color: #0F172A;
        color: #F8FAFC;
        border: 1px solid #334155;
        padding: 4px;
    }

    QFileDialog QPushButton {
        background-color: #334155;
        color: #F8FAFC;
        border: 1px solid #475569;
        padding: 6px 12px;
        border-radius: 4px;
    }

    /* Aba de Resumo Estatístico do Projeto */
    QLabel#summaryTitle {
        font-size: 18px;
        font-weight: bold;
        color: #3B82F6;
        margin-bottom: 2px;
    }

    QLabel#summaryDesc {
        font-size: 13px;
        color: #94A3B8;
        margin-bottom: 10px;
    }

    QFrame#summaryCard {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
    }

    QFrame#summaryCard:hover {
        border-color: #3B82F6;
    }

    QLabel#cardValue {
        font-size: 18px;
        font-weight: bold;
        color: #F8FAFC;
    }

    QLabel#cardTitle {
        font-size: 12px;
        color: #94A3B8;
    }
    """
