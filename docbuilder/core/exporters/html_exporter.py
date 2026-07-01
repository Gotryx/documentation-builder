"""
Implementação do exportador de formato HTML5 Wiki profissional.
Processa a AST gerando um portal wiki interativo com sidebar de navegação,
pesquisa em tempo real, suporte a modo escuro e controle de leitura.
"""

from pathlib import Path
from xml.sax.saxutils import escape
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


class HtmlExporter(IExporter):
    """
    Exportador encarregado de compilar a AST em um Portal Wiki corporativo completo,
    responsivo, esteticamente premium, com busca dinâmica e suporte a tema escuro.
    """

    def get_supported_format(self) -> str:
        return "html"

    def export(
        self, source_document_path: Path, output_path: Path, template: TemplateStyle
    ) -> None:
        # 1. Carrega a AST do arquivo temporário
        with open(source_document_path, "r", encoding="utf-8") as f:
            json_ast = f.read()
        blocks = ASTSerializer.deserialize_from_json(json_ast)

        # 2. Divide os blocos da AST em páginas com base nos SectionBreakBlock
        pages = []
        current_page_blocks = []
        current_page_title = "Visão Geral"

        for block in blocks:
            if isinstance(block, SectionBreakBlock):
                if current_page_blocks:
                    pages.append((current_page_title, current_page_blocks))
                current_page_title = block.title or f"Tópico {len(pages) + 1}"
                current_page_blocks = []
            else:
                current_page_blocks.append(block)

        if current_page_blocks or not pages:
            pages.append((current_page_title, current_page_blocks))

        # 3. Cria a folha de estilo externa CSS baseada no template do projeto
        css_filename = output_path.stem + ".css"
        css_path = output_path.parent / css_filename
        self._generate_css(css_path, template)

        # 4. Monta o portal HTML
        html_lines = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append('<html lang="pt-BR">')
        html_lines.append("<head>")
        html_lines.append('    <meta charset="utf-8">')
        html_lines.append(
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
        html_lines.append(
            f"    <title>{escape(template.header_text or 'Wiki Corporativa GoTryx')}</title>"
        )
        html_lines.append(
            '    <link rel="preconnect" href="https://fonts.googleapis.com">'
        )
        html_lines.append(
            '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        )
        html_lines.append(
            '    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">'
        )
        html_lines.append(f'    <link rel="stylesheet" href="{css_filename}">')
        html_lines.append("</head>")
        html_lines.append("<body>")

        # Estrutura do Wiki Wrapper
        html_lines.append('    <div class="wiki-wrapper">')

        # Sidebar Esquerda
        html_lines.append('        <aside class="wiki-sidebar">')
        html_lines.append('            <div class="sidebar-header">')
        html_lines.append('                <div class="logo-area">')
        html_lines.append(
            f"                    <h3>{escape(template.header_text or 'Manual GoTryx')}</h3>"
        )
        html_lines.append("                </div>")
        html_lines.append('                <div class="sidebar-meta">')
        html_lines.append(
            f'                    <span class="version-tag">v{escape(template.footer_text or "1.0")}</span>'
        )
        html_lines.append("                </div>")
        html_lines.append("            </div>")

        html_lines.append('            <div class="search-box">')
        html_lines.append(
            '                <input type="text" id="wiki-search" placeholder="Pesquisar..." autocomplete="off">'
        )
        html_lines.append("            </div>")

        html_lines.append('            <nav class="sidebar-nav">')
        html_lines.append('                <ul class="nav-list">')
        for idx, (title, _) in enumerate(pages):
            html_lines.append(
                f'                    <li><a href="#page-{idx}" class="nav-link" data-index="{idx}"><span class="link-bullet"></span><span class="link-text">{escape(title)}</span></a></li>'
            )
        html_lines.append("                </ul>")
        html_lines.append("            </nav>")

        html_lines.append('            <div class="sidebar-footer">')
        html_lines.append("                <span>Corporativo GoTryx</span>")
        html_lines.append("            </div>")
        html_lines.append("        </aside>")

        # Conteúdo Principal Direito
        html_lines.append('        <main class="wiki-content">')
        html_lines.append('            <header class="content-header">')
        html_lines.append(
            '                <button class="mobile-toggle" id="mobile-toggle">'
        )
        html_lines.append("                    <span></span><span></span><span></span>")
        html_lines.append("                </button>")
        html_lines.append('                <div class="breadcrumbs" id="breadcrumbs">')
        html_lines.append(
            '                    <span>Documentação</span> <span class="separator">/</span> <span class="current">Visão Geral</span>'
        )
        html_lines.append("                </div>")
        html_lines.append('                <div class="theme-switcher">')
        html_lines.append(
            '                    <button id="dark-mode-toggle" title="Alternar Modo Escuro">🌙</button>'
        )
        html_lines.append("                </div>")
        html_lines.append("            </header>")

        html_lines.append('            <div class="content-body">')

        # Renderiza os blocos dentro de cada seção
        for idx, (title, page_blocks) in enumerate(pages):
            html_lines.append(
                f'                <section class="wiki-page" id="page-{idx}" style="display: none;">'
            )
            html_lines.append(
                f'                    <h1 class="page-title">{escape(title)}</h1>'
            )

            for block in page_blocks:
                if isinstance(block, HeadingBlock):
                    level = min(max(block.level, 1), 6)
                    # Força títulos internos a começarem em h2 para manter hierarquia limpa
                    h_level = min(level + 1, 6)
                    html_lines.append(
                        f"                    <h{h_level}>{escape(block.text)}</h{h_level}>"
                    )

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
                            text_escaped = (
                                f'<a href="{escape(run.link_url)}">{text_escaped}</a>'
                            )
                        runs_html.append(text_escaped)
                    html_lines.append(
                        f"                    <p>{''.join(runs_html)}</p>"
                    )

                elif isinstance(block, ListBlock):
                    tag = "ol" if block.ordered else "ul"
                    html_lines.append(f"                    <{tag}>")
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
                        html_lines.append(
                            f"                        <li>{''.join(item_runs_html)}</li>"
                        )
                    html_lines.append(f"                    </{tag}>")

                elif isinstance(block, TableBlock):
                    html_lines.append("                    <table>")
                    if block.headers:
                        html_lines.append("                        <thead>")
                        html_lines.append("                            <tr>")
                        for cell in block.headers:
                            cell_text = escape("".join(r.text for r in cell.runs))
                            html_lines.append(
                                f"                                <th>{cell_text}</th>"
                            )
                        html_lines.append("                            </tr>")
                        html_lines.append("                        </thead>")
                    if block.rows:
                        html_lines.append("                        <tbody>")
                        for row in block.rows:
                            html_lines.append("                            <tr>")
                            for cell in row:
                                cell_text = escape("".join(r.text for r in cell.runs))
                                html_lines.append(
                                    f"                                <td>{cell_text}</td>"
                                )
                            html_lines.append("                            </tr>")
                        html_lines.append("                        </tbody>")
                    html_lines.append("                    </table>")

                elif isinstance(block, ImageBlock):
                    img_name = Path(block.image_path).name
                    caption_text = escape(block.caption) if block.caption else ""
                    html_lines.append("                    <figure>")
                    html_lines.append(
                        f'                        <img src="{escape(img_name)}" alt="{caption_text}">'
                    )
                    if caption_text:
                        html_lines.append(
                            f"                        <figcaption>{caption_text}</figcaption>"
                        )
                    html_lines.append("                    </figure>")

                elif isinstance(block, PageBreakBlock):
                    html_lines.append(
                        '                    <hr class="section-divider">'
                    )

            html_lines.append("                </section>")

        html_lines.append("            </div>")

        # Navegação no Rodapé
        html_lines.append('            <footer class="content-footer">')
        html_lines.append('                <div class="page-navigation">')
        html_lines.append(
            '                    <button id="btn-prev-page" class="nav-button">← Anterior</button>'
        )
        html_lines.append(
            '                    <button id="btn-next-page" class="nav-button">Próximo →</button>'
        )
        html_lines.append("                </div>")
        html_lines.append("            </footer>")

        html_lines.append("        </main>")
        html_lines.append("    </div>")

        # Script JS dinâmico da Wiki
        html_lines.append("    <script>")
        html_lines.append(
            "        document.addEventListener('DOMContentLoaded', () => {"
        )
        html_lines.append(
            "            const pages = document.querySelectorAll('.wiki-page');"
        )
        html_lines.append(
            "            const navLinks = document.querySelectorAll('.nav-link');"
        )
        html_lines.append(
            "            const breadcrumbs = document.getElementById('breadcrumbs');"
        )
        html_lines.append(
            "            const prevBtn = document.getElementById('btn-prev-page');"
        )
        html_lines.append(
            "            const nextBtn = document.getElementById('btn-next-page');"
        )
        html_lines.append(
            "            const searchInput = document.getElementById('wiki-search');"
        )
        html_lines.append(
            "            const mobileToggle = document.getElementById('mobile-toggle');"
        )
        html_lines.append(
            "            const sidebar = document.querySelector('.wiki-sidebar');"
        )
        html_lines.append(
            "            const darkToggle = document.getElementById('dark-mode-toggle');"
        )
        html_lines.append("            let currentPageIdx = 0;")
        html_lines.append(
            "            if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {"
        )
        html_lines.append("                document.body.classList.add('dark-theme');")
        html_lines.append("                darkToggle.textContent = '☀️';")
        html_lines.append("            }")
        html_lines.append("            darkToggle.addEventListener('click', () => {")
        html_lines.append(
            "                document.body.classList.toggle('dark-theme');"
        )
        html_lines.append(
            "                const isDark = document.body.classList.contains('dark-theme');"
        )
        html_lines.append(
            "                darkToggle.textContent = isDark ? '☀️' : '🌙';"
        )
        html_lines.append(
            "                localStorage.setItem('theme', isDark ? 'dark' : 'light');"
        )
        html_lines.append("            });")
        html_lines.append("            mobileToggle.addEventListener('click', () => {")
        html_lines.append("                sidebar.classList.toggle('open');")
        html_lines.append("                mobileToggle.classList.toggle('active');")
        html_lines.append("            });")
        html_lines.append("            function showPage(idx) {")
        html_lines.append("                if (idx < 0 || idx >= pages.length) return;")
        html_lines.append("                pages.forEach((page, i) => {")
        html_lines.append(
            "                    page.style.display = i === idx ? 'block' : 'none';"
        )
        html_lines.append(
            "                    if (i === idx) page.classList.add('active');"
        )
        html_lines.append("                    else page.classList.remove('active');")
        html_lines.append("                });")
        html_lines.append("                navLinks.forEach((link, i) => {")
        html_lines.append(
            "                    if (i === idx) link.classList.add('active');"
        )
        html_lines.append("                    else link.classList.remove('active');")
        html_lines.append("                });")
        html_lines.append("                currentPageIdx = idx;")
        html_lines.append("                const activeLink = navLinks[idx];")
        html_lines.append(
            "                const pageTitle = activeLink ? activeLink.querySelector('.link-text').textContent : 'Início';"
        )
        html_lines.append(
            '                breadcrumbs.innerHTML = `<span>Documentação</span> <span class="separator">/</span> <span class="current">${pageTitle}</span>`;'
        )
        html_lines.append("                prevBtn.disabled = idx === 0;")
        html_lines.append(
            "                nextBtn.disabled = idx === pages.length - 1;"
        )
        html_lines.append("                sidebar.classList.remove('open');")
        html_lines.append("                mobileToggle.classList.remove('active');")
        html_lines.append(
            "                window.scrollTo({ top: 0, behavior: 'smooth' });"
        )
        html_lines.append("                window.location.hash = `page-${idx}`;")
        html_lines.append("            }")
        html_lines.append("            navLinks.forEach((link, i) => {")
        html_lines.append("                link.addEventListener('click', (e) => {")
        html_lines.append("                    e.preventDefault();")
        html_lines.append("                    showPage(i);")
        html_lines.append("                });")
        html_lines.append("            });")
        html_lines.append("            prevBtn.addEventListener('click', () => {")
        html_lines.append(
            "                if (currentPageIdx > 0) showPage(currentPageIdx - 1);"
        )
        html_lines.append("            });")
        html_lines.append("            nextBtn.addEventListener('click', () => {")
        html_lines.append(
            "                if (currentPageIdx < pages.length - 1) showPage(currentPageIdx + 1);"
        )
        html_lines.append("            });")
        html_lines.append("            searchInput.addEventListener('input', (e) => {")
        html_lines.append(
            "                const query = e.target.value.toLowerCase().trim();"
        )
        html_lines.append("                navLinks.forEach((link, i) => {")
        html_lines.append("                    const page = pages[i];")
        html_lines.append(
            "                    const textContent = page.textContent.toLowerCase();"
        )
        html_lines.append(
            "                    const titleText = link.querySelector('.link-text').textContent.toLowerCase();"
        )
        html_lines.append(
            "                    if (query === '' || textContent.includes(query) || titleText.includes(query)) {"
        )
        html_lines.append("                        link.style.display = 'flex';")
        html_lines.append("                    } else {")
        html_lines.append("                        link.style.display = 'none';")
        html_lines.append("                    }")
        html_lines.append("                });")
        html_lines.append("            });")
        html_lines.append("            const hash = window.location.hash;")
        html_lines.append("            if (hash && hash.startsWith('#page-')) {")
        html_lines.append(
            "                const idx = parseInt(hash.replace('#page-', ''), 10);"
        )
        html_lines.append(
            "                if (!isNaN(idx) && idx >= 0 && idx < pages.length) {"
        )
        html_lines.append("                    showPage(idx);")
        html_lines.append("                    return;")
        html_lines.append("                }")
        html_lines.append("            }")
        html_lines.append("            showPage(0);")
        html_lines.append("        });")
        html_lines.append("    </script>")

        html_lines.append("</body>")
        html_lines.append("</html>")

        # Salva o arquivo final HTML
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))

    def _generate_css(self, css_path: Path, template: TemplateStyle) -> None:
        """Gera a folha de estilo CSS premium para o Portal Wiki."""
        fallback_font = "sans-serif"
        if (
            "serif" in template.font_family.lower()
            or "georgia" in template.font_family.lower()
        ):
            fallback_font = "serif"
        elif "mono" in template.font_family.lower():
            fallback_font = "monospace"

        # Variáveis de Cores Harmoniosas baseadas no Template
        primary = template.primary_color
        secondary = template.secondary_color

        css_content = f"""/* GoTryx Wiki Style: {template.name} */

:root {{
    --font-family: "{template.font_family}", {fallback_font};
    --primary-color: {primary};
    --secondary-color: {secondary};
    --bg-color: #FFFFFF;
    --text-color: #1F2937;
    --sidebar-bg: #F9FAFB;
    --sidebar-border: #E5E7EB;
    --sidebar-text: #4B5563;
    --sidebar-text-active: {primary};
    --sidebar-bg-active: #F3F4F6;
    --card-bg: #FFFFFF;
    --border-color: #E5E7EB;
    --code-bg: #F3F4F6;
}}

.dark-theme {{
    --bg-color: #0F172A;
    --text-color: #F1F5F9;
    --sidebar-bg: #1E293B;
    --sidebar-border: #334155;
    --sidebar-text: #94A3B8;
    --sidebar-text-active: #38BDF8;
    --sidebar-bg-active: #334155;
    --card-bg: #1E293B;
    --border-color: #334155;
    --code-bg: #1E293B;
}}

* {{
    box-sizing: border-box;
}}

body {{
    font-family: var(--font-family);
    font-size: {template.font_size}pt;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    margin: 0;
    padding: 0;
    transition: background-color 0.3s ease, color 0.3s ease;
}}

/* Wiki Layout */
.wiki-wrapper {{
    display: flex;
    min-height: 100vh;
}}

/* Sidebar */
.wiki-sidebar {{
    width: 280px;
    background-color: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-border);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 100;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.3s ease, border-color 0.3s ease;
}}

.sidebar-header {{
    padding: 24px 20px;
    border-bottom: 1px solid var(--sidebar-border);
    display: flex;
    flex-direction: column;
    gap: 8px;
}}

.logo-area h3 {{
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--primary-color);
    letter-spacing: -0.5px;
}}

.version-tag {{
    font-size: 0.75rem;
    padding: 3px 8px;
    background-color: var(--sidebar-bg-active);
    color: var(--sidebar-text);
    border-radius: 9999px;
    font-weight: 500;
}}

.search-box {{
    padding: 16px 20px;
}}

.search-box input {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--sidebar-border);
    border-radius: 6px;
    background-color: var(--bg-color);
    color: var(--text-color);
    font-size: 0.875rem;
    outline: none;
    transition: border-color 0.2s ease;
}}

.search-box input:focus {{
    border-color: var(--secondary-color);
}}

.sidebar-nav {{
    flex: 1;
    overflow-y: auto;
    padding: 10px 12px;
}}

.nav-list {{
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
}}

.nav-link {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    color: var(--sidebar-text);
    text-decoration: none;
    border-radius: 6px;
    font-size: 0.925rem;
    font-weight: 500;
    transition: all 0.2s ease;
}}

.nav-link:hover {{
    background-color: var(--sidebar-bg-active);
    color: var(--text-color);
}}

.nav-link.active {{
    background-color: var(--sidebar-bg-active);
    color: var(--sidebar-text-active);
    font-weight: 600;
}}

.link-bullet {{
    width: 6px;
    height: 6px;
    background-color: currentColor;
    border-radius: 50%;
    opacity: 0.5;
}}

.sidebar-footer {{
    padding: 16px 20px;
    border-top: 1px solid var(--sidebar-border);
    font-size: 0.75rem;
    color: var(--sidebar-text);
    opacity: 0.8;
}}

/* Wiki Content Area */
.wiki-content {{
    flex: 1;
    margin-left: 280px;
    display: flex;
    flex-direction: column;
    min-width: 0;
}}

.content-header {{
    height: 64px;
    border-bottom: 1px solid var(--border-color);
    padding: 0 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background-color: var(--bg-color);
    z-index: 90;
}}

.breadcrumbs {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    color: var(--sidebar-text);
}}

.breadcrumbs .separator {{
    opacity: 0.5;
}}

.breadcrumbs .current {{
    font-weight: 600;
    color: var(--text-color);
}}

.theme-switcher button {{
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 8px;
    border-radius: 50%;
    transition: background-color 0.2s ease;
}}

.theme-switcher button:hover {{
    background-color: var(--sidebar-bg-active);
}}

.content-body {{
    flex: 1;
    padding: 40px;
    max-width: 800px;
    width: 100%;
    margin: 0 auto;
}}

.page-title {{
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--primary-color);
    border-bottom: 2px solid var(--secondary-color);
    padding-bottom: 0.3em;
    margin-top: 0;
    margin-bottom: 1.5rem;
    letter-spacing: -1px;
}}

h2, h3, h4, h5, h6 {{
    color: var(--primary-color);
    font-weight: 700;
    margin-top: 1.8rem;
    margin-bottom: 0.8rem;
}}

h2 {{
    font-size: 1.6rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.3em;
}}

h3 {{
    font-size: 1.25rem;
}}

p {{
    margin-top: 0;
    margin-bottom: 1.2rem;
    text-align: justify;
    color: var(--text-color);
    opacity: 0.95;
}}

a {{
    color: var(--secondary-color);
    text-decoration: none;
    font-weight: 500;
}}

a:hover {{
    text-decoration: underline;
}}

/* Listas */
ul, ol {{
    margin-top: 0;
    margin-bottom: 1.2rem;
    padding-left: 2rem;
}}

li {{
    margin-bottom: 0.5rem;
}}

/* Tabelas */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 2rem 0;
}}

th, td {{
    border: 1px solid var(--border-color);
    padding: 12px 16px;
    text-align: left;
    font-size: 0.95rem;
}}

th {{
    background-color: var(--primary-color);
    color: #FFFFFF;
    font-weight: 600;
}}

.dark-theme th {{
    color: #000000;
    background-color: var(--sidebar-text-active);
}}

tr:nth-child(even) {{
    background-color: var(--sidebar-bg-active);
}}

/* Imagens */
figure {{
    margin: 2rem 0;
    text-align: center;
}}

img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}}

figcaption {{
    font-size: 0.875rem;
    color: var(--sidebar-text);
    margin-top: 0.75rem;
    font-style: italic;
}}

.section-divider {{
    border: 0;
    height: 1px;
    background-color: var(--border-color);
    margin: 3rem 0;
}}

/* Footer */
.content-footer {{
    border-top: 1px solid var(--border-color);
    padding: 24px 40px;
    max-width: 800px;
    width: 100%;
    margin: 0 auto;
}}

.page-navigation {{
    display: flex;
    justify-content: space-between;
    gap: 16px;
}}

.nav-button {{
    padding: 10px 20px;
    background-color: var(--primary-color);
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: opacity 0.2s ease;
}}

.dark-theme .nav-button {{
    background-color: var(--sidebar-text-active);
    color: #000000;
}}

.nav-button:hover {{
    opacity: 0.9;
}}

.nav-button:disabled {{
    opacity: 0.4;
    cursor: not-allowed;
}}

/* Mobile Toggle Hamburger */
.mobile-toggle {{
    display: none;
    background: none;
    border: none;
    flex-direction: column;
    gap: 5px;
    cursor: pointer;
    padding: 8px;
    z-index: 110;
}}

.mobile-toggle span {{
    width: 22px;
    height: 2px;
    background-color: var(--text-color);
    transition: all 0.2s ease;
}}

/* Responsividade Mobile */
@media (max-width: 768px) {{
    .wiki-sidebar {{
        transform: translateX(-100%);
    }}
    .wiki-sidebar.open {{
        transform: translateX(0);
    }}
    .wiki-content {{
        margin-left: 0;
    }}
    .mobile-toggle {{
        display: flex;
    }}
    .content-header {{
        padding: 0 20px;
    }}
    .content-body {{
        padding: 24px 20px;
    }}
    .content-footer {{
        padding: 20px;
    }}
    .mobile-toggle.active span:nth-child(1) {{
        transform: rotate(45deg) translate(5px, 5px);
    }}
    .mobile-toggle.active span:nth-child(2) {{
        opacity: 0;
    }}
    .mobile-toggle.active span:nth-child(3) {{
        transform: rotate(-45deg) translate(5px, -5px);
    }}
}}
"""
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css_content)
