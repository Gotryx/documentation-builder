# GoTryx Documentation Builder

O **GoTryx Documentation Builder** é a ferramenta oficial da GoTryx para a compilação, estruturação, validação e exportação de documentações corporativas integradas a partir de documentos independentes.

Esta aplicação foi desenvolvida sob os mais altos padrões de engenharia de software, priorizando manutenção de longo prazo, alta coesão, baixo acoplamento e desacoplamento absoluto através de **Clean Architecture** e **DDD (Domain-Driven Design)**.

---

## Tecnologias
* **Backend**: Python 3.12+
* **Frontend**: PySide6 (Qt)
* **Persistência**: YAML (PyYAML)
* **Geração de Word**: python-docx
* **Geração de PDF**: LibreOffice Headless
* **Suporte de Entrada**: Markdown, DOCX, ODT, HTML, TXT

---

## Estrutura do Projeto
```text
docbuilder/
  ├── app/                  # Ponto de entrada (CLI e Launcher híbrido)
  ├── config/               # Configurações globais e paths do sistema
  ├── core/                 # Lógica de negócio (Desacoplada)
  │     ├── domain/         # Entidades puras de domínio, regras e interfaces
  │     ├── services/       # Use Cases, DTOs e serviços de aplicação
  │     ├── repositories/   # Persistência do manifesto
  │     ├── builders/       # Compilador de arquivos estruturados (AST)
  │     └── exporters/      # Conversores específicos de saída (DOCX, PDF, HTML, MD)
  ├── resources/            # Imagens, ícones e templates corporativos base
  ├── tests/                # Testes unitários e de integração
  └── ui/                   # Interface gráfica desktop PySide6
```

---

## Modo de Execução

### 1. Pré-requisitos
Certifique-se de que possui o **LibreOffice** instalado em seu sistema operacional (necessário para a geração perfeita de PDFs).

Instale as dependências listadas no `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Modo Gráfico (Desktop GUI)
Para abrir a aplicação Desktop moderna:
```bash
python main.py
```

### 3. Modo Headless (Tool de Automação / CLI)
Para executar comandos diretamente pelo terminal (comunicação limpa via JSON em `stdout` e códigos de retorno tradicionais), ideal para integração de scripts ou agentes:

* **Criar Projeto:**
  ```bash
  python main.py --cli create --name "Manual Gotryx" --author "Engenharia" --dir "./meu_projeto"
  ```

* **Validar Projeto:**
  ```bash
  python main.py --cli validate --project "./meu_projeto"
  ```

* **Compilar e Exportar:**
  ```bash
  python main.py --cli build --project "./meu_projeto" --formats "docx,pdf,html,md"
  ```

* **Importar Documento:**
  ```bash
  python main.py --cli import --file "/caminho/doc.md" --project "./meu_projeto"
  ```

---

## Arquitetura de Validação
Antes de iniciar qualquer compilação (build), o sistema executa o `ValidateProjectUseCase` que valida:
1. Existência física de todos os documentos listados na árvore.
2. Nomes/Títulos duplicados na hierarquia de volumes/capítulos.
3. Links locais quebrados e imagens ausentes dentro de documentos Markdown e HTML.
4. Integridade de templates e logos.

---

## Testes Automatizados
Para rodar a suíte de testes unitários e de integração:
```bash
pytest docbuilder/tests/
```
