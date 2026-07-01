# Core Domain Module

Módulo contendo o núcleo de regras de negócios puras, entidades de domínio e especificações de interfaces (portas).

## Estrutura
* `entities.py`: Contém as estruturas de dados ricas de Projeto, Volume, Parte, Capítulo, Documento, Versão e Templates.
* `document_ast.py`: Estrutura de árvore de sintaxe abstrata unificada de blocos (tabelas, parágrafos, listas, imagens) para desacoplamento de arquivos.
* `interfaces.py`: Portas e contratos (Interfaces) a serem implementados pela infraestrutura.

---

# Changelog - Domain Module
## [1.0.0.1] - 2026-07-01
* Criação inicial das entidades de domínio e classes de AST de documentos.
