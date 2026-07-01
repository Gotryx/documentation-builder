"""
Implementação do exportador de formato HTML5 limpo.
Processa a AST em JSON gerando tags HTML estruturadas e cria uma folha de estilo CSS externa desacoplada, baseada no template.
"""

from pathlib import Path
from xml.sax.saxutils import escape
from docbuilder.core.domain.entities import TemplateStyle
from docbuilder.core.domain.document_ast import (
    HeadingBlock, ParagraphBlock, ListBlock, TableBlock, ImageBlock,
    PageBreakBlock, SectionBreakBlock
)
from docbuilder.core.builders.document_builder import ASTSerializer
from docbuilder.core.domain.interfaces import IExporter


class HtmlExporter(IExporter):
    """
    Exportador encarregado de compilar a AST em uma estrutura de páginas web HTML5 limpas
    com folha de estilos CSS separada e sem estilização inline.
    """

    def get_supported_format(self) -> str:
        return "html"

    def export(self, source_document_path: Path, output_path: Path, template: TemplateStyle) -> None:
        # 1. Carrega a AST do arquivo temporário
        with open(source_document_path, "r", encoding="utf-8") as f:
            json_ast = f.read()
        blocks = ASTSerializer.deserialize_from_json(json_ast)

        # 2. Cria a folha de estilo externa CSS baseada no template do projeto
        css_filename = output_path.stem + ".css"
        css_path = output_path.parent / css_filename
        self._generate_css(css_path, template)

        # 3. Monta o corpo HTML
        html_lines = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append(f'<html lang="pt-BR">')
        html_lines.append("<head>")
        html_lines.append('    <meta charset="utf-8">')
        html_lines.append('    <meta name="viewport" content="width=device-width, initial-scale=device-width">')
        html_lines.append(f"    <title>{escape(template.header_text or 'Documentação GoTryx')}</title>")
        html_lines.append(f'    <link rel="stylesheet" href="{css_filename}">')
        html_lines.append("</head>")
        html_lines.append("<body>")
        html_lines.append('    <div class="document-container">')

        for block in blocks:
            if isinstance(block, SectionBreakBlock):
                html_lines.append(f'        <section class="document-section" data-title="{escape(block.title)}">')
            
            elif isinstance(block, HeadingBlock):
                level = min(max(block.level, 1), 6)
                html_lines.append(f"            <h{level}>{escape(block.text)}</h{level}>")
            
            elif isinstance(block, ParagraphBlock):
                runs_html = []
                for run in block.runs:
                    text_escaped = escape(run.text)
                    if run.bold:
                        text_escaped = f"<strong>{text_escaped}</strong>"
                    if run.italic:
                        text_escaped = f"<em>{text_escaped}</em>"
                    if run.underline:
                        text_escaped = f"<u>{text_escaped}</u>"
                    if run.link_url:
                        text_escaped = f'<a href="{escape(run.link_url)}">{text_escaped}</a>'
                    runs_html.append(text_escaped)
                html_lines.append(f"            <p>{''.join(runs_html)}</p>")
            
            elif isinstance(block, ListBlock):
                tag = "ol" if block.ordered else "ul"
                html_lines.append(f"            <{tag}>")
                for item in block.items:
                    item_runs_html = []
                    for run in item.runs:
                        text_escaped = escape(run.text)
                        if run.bold:
                            text_escaped = f"<strong>{text_escaped}</strong>"
                        if run.italic:
                            text_escaped = f"<em>{text_escaped}</em>"
                        if run.underline:
                            text_escaped = f"<u>{text_escaped}</u>"
                        if run.link_url:
                            text_escaped = f'<a href="{escape(run.link_url)}">{text_escaped}</a>'
                        item_runs_html.append(text_escaped)
                    html_lines.append(f"                <li>{''.join(item_runs_html)}</li>")
                html_lines.append(f"            </{tag}>")
            
            elif isinstance(block, TableBlock):
                html_lines.append("            <table>")
                
                # Headers
                if block.headers:
                    html_lines.append("                <thead>")
                    html_lines.append("                    <tr>")
                    for cell in block.headers:
                        cell_text = escape("".join(r.text for r in cell.runs))
                        html_lines.append(f"                        <th>{cell_text}</th>")
                    html_lines.append("                    </tr>")
                    html_lines.append("                </thead>")
                
                # Rows
                if block.rows:
                    html_lines.append("                <tbody>")
                    for row in block.rows:
                        html_lines.append("                    <tr>")
                        for cell in row:
                            cell_text = escape("".join(r.text for r in cell.runs))
                            html_lines.append(f"                        <td>{cell_text}</td>")
                        html_lines.append("                    </tr>")
                    html_lines.append("                </tbody>")
                
                html_lines.append("            </table>")
            
            elif isinstance(block, ImageBlock):
                # Mantém caminho da imagem, convertendo para caminhos web relativos (apenas nome se copiado para pasta dist)
                img_name = Path(block.image_path).name
                caption_text = escape(block.caption) if block.caption else ""
                html_lines.append("            <figure>")
                html_lines.append(f'                <img src="{escape(img_name)}" alt="{caption_text}">')
                if caption_text:
                    html_lines.append(f"                <figcaption>{caption_text}</figcaption>")
                html_lines.append("            </figure>")
            
            elif isinstance(block, PageBreakBlock):
                html_lines.append('            <div class="page-break"></div>')

        html_lines.append("    </div>")
        html_lines.append("</body>")
        html_lines.append("</html>")

        # Salva o arquivo final HTML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))

    def _generate_css(self, css_path: Path, template: TemplateStyle) -> None:
        """Gera um arquivo CSS externo aplicando as regras estilísticas do template."""
        # Convertemos fontes serifadas/monospace padrão caso não instaladas
        fallback_font = "sans-serif"
        if "serif" in template.font_family.lower() or "georgia" in template.font_family.lower():
            fallback_font = "serif"
        elif "mono" in template.font_family.lower():
            fallback_font = "monospace"

        css_content = f"""/* GoTryx Document template: {template.name} */

body {{
    font-family: "{template.font_family}", {fallback_font};
    font-size: {template.font_size}pt;
    line-height: 1.6;
    color: #1F2937;
    background-color: #FFFFFF;
    margin: 0;
    padding: 0;
}}

.document-container {{
    max-width: 800px;
    margin: 0 auto;
    padding: {template.margin_top}cm {template.margin_right}cm {template.margin_bottom}cm {template.margin_left}cm;
}}

h1, h2, h3, h4, h5, h6 {{
    color: {template.primary_color};
    font-weight: 700;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
}}

h1 {{
    font-size: 2.2em;
    border-bottom: 2px solid {template.secondary_color};
    padding-bottom: 0.3em;
}}

h2 {{
    font-size: 1.7em;
    margin-top: 1.2em;
}}

h3 {{
    font-size: 1.3em;
    color: {template.secondary_color};
}}

p {{
    margin-top: 0;
    margin-bottom: 1em;
    text-align: justify;
}}

a {{
    color: {template.secondary_color};
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

ul, ol {{
    margin-top: 0;
    margin-bottom: 1em;
    padding-left: 2em;
}}

li {{
    margin-bottom: 0.5em;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    page-break-inside: avoid;
}}

th, td {{
    border: 1px solid #E5E7EB;
    padding: 10px 12px;
    text-align: left;
}}

th {{
    background-color: {template.primary_color};
    color: #FFFFFF;
    font-weight: 600;
}}

tr:nth-child(even) {{
    background-color: #F9FAFB;
}}

figure {{
    display: block;
    text-align: center;
    margin: 1.5em 0;
    page-break-inside: avoid;
}}

img {{
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}}

figcaption {{
    font-size: 0.9em;
    color: #6B7280;
    margin-top: 0.5em;
    font-style: italic;
}}

.page-break {{
    page-break-before: always;
    margin-top: 3em;
    border-top: 1px dashed #D1D5DB;
}}

@media print {{
    body {{
        background-color: transparent;
        font-size: 11pt;
    }}
    .document-container {{
        max-width: 100%;
        padding: 0;
    }}
    .page-break {{
        page-break-before: always;
        border-top: none;
    }}
}}
"""
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css_content)
