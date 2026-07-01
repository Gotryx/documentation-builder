"""
Implementação do exportador de formato Markdown (.md).
Processa a AST em JSON e gera um único arquivo Markdown unificado e limpo seguindo o padrão GFM.
"""

from pathlib import Path
from docbuilder.core.domain.entities import TemplateStyle
from docbuilder.core.domain.document_ast import (
    HeadingBlock,
    ParagraphBlock,
    ListBlock,
    TableBlock,
    ImageBlock,
    PageBreakBlock,
    SectionBreakBlock,
)
from docbuilder.core.builders.document_builder import ASTSerializer
from docbuilder.core.domain.interfaces import IExporter


class MarkdownExporter(IExporter):
    """
    Exportador encarregado de consolidar a AST em um único arquivo Markdown (.md)
    preservando formatações, links, listas, imagens e tabelas padrão GFM.
    """

    def get_supported_format(self) -> str:
        return "md"

    def export(
        self, source_document_path: Path, output_path: Path, template: TemplateStyle
    ) -> None:
        # 1. Carrega a AST do arquivo temporário
        with open(source_document_path, "r", encoding="utf-8") as f:
            json_ast = f.read()
        blocks = ASTSerializer.deserialize_from_json(json_ast)

        md_lines = []

        # 2. Processa cada bloco AST para compor o Markdown unificado
        for idx, block in enumerate(blocks):
            if isinstance(block, SectionBreakBlock):
                md_lines.append(f"\n<!-- SECTION: {block.title} -->\n")
                md_lines.append("---")

            elif isinstance(block, HeadingBlock):
                # Limita nível entre 1 e 6
                level = min(max(block.level, 1), 6)
                hashes = "#" * level
                md_lines.append(f"\n{hashes} {block.text}\n")

            elif isinstance(block, ParagraphBlock):
                runs_md = []
                for run in block.runs:
                    text_run = run.text
                    if run.bold:
                        text_run = f"**{text_run}**"
                    if run.italic:
                        text_run = f"*{text_run}*"
                    if run.underline:
                        text_run = f"<u>{text_run}</u>"
                    if run.link_url:
                        text_run = f"[{text_run}]({run.link_url})"
                    runs_md.append(text_run)
                md_lines.append(f"{''.join(runs_md)}\n")

            elif isinstance(block, ListBlock):
                for item_idx, item in enumerate(block.items):
                    runs_item = []
                    for run in item.runs:
                        text_run = run.text
                        if run.bold:
                            text_run = f"**{text_run}**"
                        if run.italic:
                            text_run = f"*{text_run}*"
                        if run.underline:
                            text_run = f"<u>{text_run}</u>"
                        if run.link_url:
                            text_run = f"[{text_run}]({run.link_url})"
                        runs_item.append(text_run)

                    prefix = f"{item_idx + 1}." if block.ordered else "-"
                    md_lines.append(f"{prefix} {''.join(runs_item)}")
                md_lines.append("")  # Linha em branco após a lista

            elif isinstance(block, TableBlock):
                md_lines.append("")  # Espaço antes da tabela

                # Headers
                header_cols = []
                separator_cols = []
                for cell in block.headers:
                    cell_text = "".join(r.text for r in cell.runs)
                    header_cols.append(cell_text)
                    separator_cols.append("---")

                md_lines.append("| " + " | ".join(header_cols) + " |")
                md_lines.append("| " + " | ".join(separator_cols) + " |")

                # Rows
                for row in block.rows:
                    row_cols = []
                    for cell in row:
                        cell_text = "".join(r.text for r in cell.runs)
                        row_cols.append(cell_text)
                    md_lines.append("| " + " | ".join(row_cols) + " |")

                md_lines.append("")  # Espaço após a tabela

            elif isinstance(block, ImageBlock):
                # Mantém caminho da imagem, convertendo para caminhos relativos de nome do arquivo
                img_name = Path(block.image_path).name
                caption_text = block.caption if block.caption else "Imagem"
                md_lines.append(f"\n![{caption_text}]({img_name})\n")

            elif isinstance(block, PageBreakBlock):
                md_lines.append("\n<!-- PAGE BREAK -->\n")

        # Salva o arquivo final Markdown
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))


pre_push = True
