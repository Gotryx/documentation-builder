"""
Implementação do repositório de gerenciamento de templates.
Define e fornece as configurações dos templates pré-definidos: Corporativo, Técnico, Livro e Manual.
"""

from typing import List, Dict
from docbuilder.core.domain.entities import TemplateStyle
from docbuilder.core.domain.interfaces import ITemplateRepository


class TemplateRepository(ITemplateRepository):
    """
    Repositório encarregado de gerenciar e fornecer as configurações visuais dos templates da GoTryx.
    """

    def __init__(self) -> None:
        # Templates pré-definidos conforme requisitos do sistema
        self._templates: Dict[str, TemplateStyle] = {
            "Corporate": TemplateStyle(
                name="Corporate",
                font_family="Inter",
                font_size=11,
                margin_top=2.5,
                margin_bottom=2.5,
                margin_left=3.0,
                margin_right=2.0,
                header_text="GoTryx Corporation - Confidencial",
                footer_text="Pág. #PAGE# de #TOTAL#",
                primary_color="#1E3A8A",  # Azul Escuro Corporativo
                secondary_color="#3B82F6",  # Azul Claro Acentuado
                numbering_style="Arabic",
                logo_enabled=True,
            ),
            "Technical": TemplateStyle(
                name="Technical",
                font_family="JetBrains Mono",
                font_size=10,
                margin_top=2.0,
                margin_bottom=2.0,
                margin_left=2.5,
                margin_right=2.0,
                header_text="GoTryx Technical Documentation",
                footer_text="Manual do Engenheiro | #PAGE#",
                primary_color="#0F172A",  # Slate Escuro
                secondary_color="#10B981",  # Verde Técnico (Emerald)
                numbering_style="Arabic",
                logo_enabled=True,
            ),
            "Book": TemplateStyle(
                name="Book",
                font_family="Georgia",
                font_size=12,
                margin_top=3.0,
                margin_bottom=3.0,
                margin_left=3.0,
                margin_right=3.0,
                header_text="#SECTION_TITLE#",
                footer_text="#PAGE#",
                primary_color="#111827",  # Quase Preto
                secondary_color="#9CA3AF",  # Cinza Elegante
                numbering_style="Roman",
                logo_enabled=False,
            ),
            "Manual": TemplateStyle(
                name="Manual",
                font_family="Arial",
                font_size=11,
                margin_top=2.5,
                margin_bottom=2.0,
                margin_left=2.5,
                margin_right=2.5,
                header_text="GoTryx Manual de Operação e Processos",
                footer_text="Revisão #VERSION# | Página #PAGE#",
                primary_color="#B91C1C",  # Vermelho Escuro de Alerta
                secondary_color="#4B5563",  # Cinza Escuro
                numbering_style="Arabic",
                logo_enabled=True,
            ),
        }

    def get_template_style(self, template_name: str) -> TemplateStyle:
        """
        Retorna as configurações do template. Se o nome não existir,
        retorna o template padrão 'Corporate'.
        """
        return self._templates.get(template_name, self._templates["Corporate"])

    def list_available_templates(self) -> List[str]:
        """
        Retorna a lista de nomes dos templates disponíveis.
        """
        return list(self._templates.keys())
