# Core Exporters Module

Módulo contendo os geradores de arquivos de saída do GoTryx Documentation Builder.

## Componentes
* `docx_exporter.py`: Tradutor de AST para parágrafos, runs, tabelas e imagens nativas do Microsoft Word.
* `pdf_exporter.py`: Convertedor DOCX/HTML para PDF utilizando o LibreOffice Headless em subprocesso.
* `html_exporter.py`: Tradutor de AST para HTML5 semântico limpo, com CSS separado em folha de estilos dedicada.
* `markdown_exporter.py`: Tradutor de AST para um único arquivo Markdown (GFM).
