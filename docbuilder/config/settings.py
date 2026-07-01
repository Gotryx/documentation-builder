"""
Configurações globais e definições de caminhos do GoTryx Documentation Builder.
"""

from pathlib import Path

# Diretórios principais
APP_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = APP_DIR.parent

# Diretórios de recursos e templates
RESOURCES_DIR = APP_DIR / "resources"
TEMPLATES_DIR = APP_DIR / "core" / "templates"

# Garante a existência dos diretórios de recursos
RESOURCES_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Configurações de logging e debug
DEBUG = True
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Nome do arquivo de manifesto padrão
MANIFEST_FILENAME = "manifest.yaml"

# Idioma padrão da aplicação
DEFAULT_LANGUAGE = "pt-BR"
