"""
Árvore de Sintaxe Abstrata (AST) de Documentação.
Representação intermediária unificada de blocos de texto e estrutura para desacoplar formatos de entrada de formatos de saída.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TextRun:
    """Uma sequência de texto com formatação uniforme."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    link_url: Optional[str] = None


@dataclass
class Block:
    """Classe base para todos os blocos de conteúdo da documentação."""
    pass


@dataclass
class HeadingBlock(Block):
    """Representa um título/cabeçalho de nível H1 a H6."""
    text: str
    level: int  # 1 para título principal, 2 para seção, etc.


@dataclass
class ParagraphBlock(Block):
    """Representa um parágrafo contendo múltiplos fragmentos de texto formatados."""
    runs: List[TextRun] = field(default_factory=list)


@dataclass
class ListItem:
    """Item individual de uma lista, contendo runs de texto."""
    runs: List[TextRun] = field(default_factory=list)


@dataclass
class ListBlock(Block):
    """Representa uma lista ordenada ou não ordenada."""
    items: List[ListItem] = field(default_factory=list)
    ordered: bool = False


@dataclass
class TableCell:
    """Célula de uma tabela contendo runs de texto."""
    runs: List[TextRun] = field(default_factory=list)


@dataclass
class TableBlock(Block):
    """Representa uma tabela de dados estruturada."""
    headers: List[TableCell] = field(default_factory=list)
    rows: List[List[TableCell]] = field(default_factory=list)


@dataclass
class ImageBlock(Block):
    """Representa uma imagem inserida no documento."""
    image_path: str
    caption: Optional[str] = None


@dataclass
class PageBreakBlock(Block):
    """Representa uma quebra de página manual."""
    pass


@dataclass
class SectionBreakBlock(Block):
    """Representa uma quebra de seção (geralmente inserida ao mudar de Volume ou Parte)."""
    title: str
