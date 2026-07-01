# GoTryx Documentation Platform

A **GoTryx Documentation Platform** é a plataforma oficial da GoTryx para gerenciamento, compilação, estruturação, validação, publicação e controle de versão do portfólio de documentação corporativa a partir de documentos locais independentes.

Esta aplicação foi desenvolvida sob os mais altos padrões de engenharia de software, priorizando manutenção de longo prazo, alta coesão, baixo acoplamento e desacoplamento absoluto através de **Clean Architecture** e **DDD (Domain-Driven Design)**.

---

## 🌟 Recursos Principais da Plataforma

### 1. Painel de Portfólio (Workspace Mode)
* **Gestão de Múltiplos Projetos**: Gerencia um catálogo central corporativo (`workspace.yaml`) contendo todas as documentações.
* **Dashboard Central**: Exibe informações consolidadas de cada projeto (Nome, Versão, Autor e Caminho físico).
* **Navegação Inteligente**: Permite alternar rapidamente entre o Dashboard e o editor de qualquer projeto.

### 2. Visualizador Web Integrado (Portal Wiki Local)
* **Servidor HTTP integrado**: Inicia um mini-servidor web local (usando `http.server` nativo em thread separada) que serve os HTMLs compilados.
* **Portal Interativo**: Permite visualizar a documentação gerada em tempo real diretamente no navegador padrão em `http://localhost:8080` com folha de estilos externa.

### 3. Controle de Versão e Publicação Cloud (Git)
* **Sincronização Integrada**: Inicializa repositórios Git, realiza commits automáticos com a versão gerada e gera tags locais de release (ex: `v1.0.0.2`).
* **Push Remoto**: Se configurado, envia commits e tags automaticamente para os repositórios remotos no GitHub/GitLab.

### 4. Compilador de Documentos e Conversores (Builder/Exporters)
* **Consolidador**: Lê, ordena e unifica arquivos de entrada (Markdown, HTML, DOCX, TXT e ODT via LibreOffice) traduzindo-os para blocos AST e inserindo sumários estruturais automaticamente em [document_builder.py](file:///mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/docbuilder/core/builders/document_builder.py).
* **Exportador Word (DOCX)**: Gera arquivos `.docx` profissionais com aplicação de fontes, margens, cores do template, cabeçalhos/rodapés e numeração dinâmica nativa (oxml).
* **Exportador PDF**: Converte o arquivo DOCX em PDF utilizando LibreOffice Headless via subprocesso.
* **Exportador HTML**: Gera HTML5 semântico limpo acompanhado de uma folha de estilos externa `.css` isolada.
* **Exportador Markdown**: Consolida toda a estrutura em um único Markdown unificado GFM.

### 5. Extensibilidade via Plugins
* **PluginManager**: Carrega dinamicamente arquivos python colocados no diretório `plugins/` e registra novos exportadores personalizados (como saídas EPUB, Confluence, etc.).

---

## 📁 Estrutura do Projeto
```text
docbuilder/
  ├── app/                  # Ponto de entrada (CLI, CLI de Workspace e Launcher híbrido)
  ├── config/               # Configurações globais e paths do sistema
  ├── core/                 # Lógica de negócio (Desacoplada)
  │     ├── domain/         # Entidades puras de domínio (Workspace, Projeto, AST)
  │     ├── services/       # Use Cases, DTOs e serviços de aplicação
  │     ├── repositories/   # Persistência do manifesto e do workspace
  │     │     └── cloud/    # Provedor Git de controle de versão
  │     ├── builders/       # Compilador de arquivos e servidor Wiki local
  │     └── exporters/      # Conversores específicos de saída (DOCX, PDF, HTML, MD)
  ├── plugins/              # Diretório de carregamento de plugins dinâmicos
  ├── resources/            # Imagens, ícones e templates corporativos base
  ├── tests/                # Testes unitários e de integração
  └── ui/                   # Interface gráfica desktop PySide6 (Dashboard e Editor)
```

---

## 🛠️ Como Executar a Aplicação

### 1. Instalação de Dependências
Certifique-se de ativar o seu ambiente virtual e instalar as bibliotecas do `requirements.txt`:
```bash
source /mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/ambiente/bin/activate
pip install -r /mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/requirements.txt
```

### 2. Executar em Modo Gráfico (GUI)
Para abrir a aplicação Desktop moderna:
```bash
python /mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/main.py
```

### 3. Executar em Modo Headless (CLI / Tool de Automação de Agentes)
O script CLI aceita a flag `--cli` no início para desviar para a interface de automação estruturada. As saídas são em JSON no `stdout`:

* **Cadastrar Projeto no Workspace:**
  ```bash
  python main.py --cli workspace-register --project "./meu_projeto" --dir "."
  ```

* **Listar Projetos do Workspace:**
  ```bash
  python main.py --cli workspace-list --dir "."
  ```

* **Criar Documentação no Projeto:**
  ```bash
  python main.py --cli create --name "Manual Gotryx" --author "Engenharia" --dir "./meu_projeto"
  ```

* **Importar Documento:**
  ```bash
  python main.py --cli import --file "/caminho/doc.md" --project "./meu_projeto"
  ```

* **Validar Estrutura e Links:**
  ```bash
  python main.py --cli validate --project "./meu_projeto"
  ```

* **Compilar e Exportar:**
  ```bash
  python main.py --cli build --project "./meu_projeto" --formats "docx,pdf,html,md"
  ```

* **Sincronizar Cloud (Git Push):**
  ```bash
  python main.py --cli sync --project "./meu_projeto" --remote "https://github.com/empresa/repo.git"
  ```

---

## 🧪 Testes Automatizados
* **Testes de Domínio** em [test_domain.py](file:///mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/docbuilder/tests/test_domain.py) (validações de domínio, parsers de versão e incrementos).
* **Testes de Integração de Build** em [test_build_pipeline.py](file:///mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/docbuilder/tests/test_build_pipeline.py).
* **Testes de Workspace** em [test_workspace.py](file:///mnt/home/alexandre/Projetos/Gotryx/projeto/documentation/builder/docbuilder/tests/test_workspace.py) (cadastro de projetos e persistência de catálogo).

Rode os testes com:
```bash
pytest docbuilder/tests/
```
