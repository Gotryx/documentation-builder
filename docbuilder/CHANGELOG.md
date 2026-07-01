# Changelog - GoTryx Documentation Builder

Todas as mudanças relevantes deste projeto serão documentadas neste arquivo.

## [1.0.0.1] - 2026-07-01
### Adicionado
* Estrutura do projeto desacoplada utilizando Clean Architecture e Domain-Driven Design (DDD).
* Entidades de Domínio (`Project`, `Volume`, `Part`, `Chapter`, `Document`, `Version`, `TemplateStyle`) com validações lógicas e encapsulamento em `entities.py`.
* AST (Abstract Syntax Tree) unificada para documentos (`document_ast.py`), garantindo o isolamento total de formatos de entrada e de saída.
* Persistência robusta de projetos via manifesto YAML em `project_repository.py`.
* Casos de uso de negócio para criação, carregamento, salvamento, importação de documentos e reordenação.
* Validador de consistência profunda pré-compilação (`ValidateProjectUseCase`), checando arquivos existentes e analisando links/imagens locais quebrados dentro do texto.
* Orquestrador de build (`BuildProjectUseCase`) e exportadores nativos:
  * `DocxExporter` (via python-docx com aplicação de margens, fontes e numeração de página dinâmica).
  * `PdfExporter` (através de subprocesso com LibreOffice headless).
  * `HtmlExporter` (HTML5 limpo com CSS separado).
  * `MarkdownExporter` (arquivo GFM único unificado).
* Interface gráfica Desktop moderna (PySide6) na pasta `ui/` com árvore reordenável via **Drag and Drop**, aba de preview de conteúdo e formulários dinâmicos de propriedades de metadados.
* Interface de Linha de Comando Headless (`app/cli.py`) retornando exclusivamente dados em **JSON** via `stdout` para possibilitar automação externa.
* Suíte de testes unitários e de integração abrangente em `tests/`.
