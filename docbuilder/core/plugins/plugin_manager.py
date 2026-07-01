"""
Gerenciador dinâmico de plugins (PluginManager) do GoTryx Documentation Platform.
Permite estender os exportadores e funcionalidades da plataforma sem alterar o Core.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import List, Dict
from docbuilder.core.domain.interfaces import IPlugin, IExporter


class PluginManager:
    """
    Carregador e orquestrador de plugins dinâmicos da plataforma.
    Varre um diretório de plugins e registra novos exportadores do sistema.
    """

    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir
        self._loaded_plugins: Dict[str, IPlugin] = {}
        self._registered_exporters: List[IExporter] = []

    def discover_and_load_plugins(self) -> None:
        """Varre o diretório de plugins e importa dinamicamente os arquivos python válidos."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return

        # Adiciona o diretório de plugins ao path do Python para evitar problemas de importação
        plugins_dir_str = str(self.plugins_dir.resolve())
        if plugins_dir_str not in sys.path:
            sys.path.append(plugins_dir_str)

        # Escaneia por módulos python (ex: arquivo.py ou pastas com __init__.py)
        for entry in os.scandir(self.plugins_dir):
            if (
                entry.is_file()
                and entry.name.endswith(".py")
                and not entry.name.startswith("__")
            ):
                self._load_plugin_from_file(Path(entry.path))
            elif entry.is_dir() and not entry.name.startswith("__"):
                init_file = Path(entry.path) / "__init__.py"
                if init_file.exists():
                    self._load_plugin_from_dir(Path(entry.path))

    def get_registered_exporters(self) -> List[IExporter]:
        """Retorna todos os exportadores extras que foram injetados por plugins carregados."""
        return self._registered_exporters

    def get_loaded_plugins(self) -> List[IPlugin]:
        return list(self._loaded_plugins.values())

    def _load_plugin_from_file(self, file_path: Path) -> None:
        module_name = file_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Procura por classes que implementam IPlugin
                self._register_plugin_classes(module)
        except Exception as e:
            # Imprime no stderr do log do sistema caso falhe em carregar o plugin
            print(
                f"[PluginManager] Falha ao carregar plugin {module_name}: {e}",
                file=sys.stderr,
            )

    def _load_plugin_from_dir(self, dir_path: Path) -> None:
        module_name = dir_path.name
        try:
            module = importlib.import_module(module_name)
            self._register_plugin_classes(module)
        except Exception as e:
            print(
                f"[PluginManager] Falha ao carregar plugin de diretório {module_name}: {e}",
                file=sys.stderr,
            )

    def _register_plugin_classes(self, module) -> None:
        # Varre todos os atributos expostos no módulo
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # Verifica se é uma classe, subclasse de IPlugin e não a própria interface IPlugin
            if (
                isinstance(attr, type)
                and issubclass(attr, IPlugin)
                and attr is not IPlugin
            ):
                try:
                    plugin_instance = attr()
                    plugin_name = plugin_instance.get_name()

                    if plugin_name not in self._loaded_plugins:
                        # Inicializa o plugin passando este gerenciador como contexto
                        plugin_instance.initialize(self)
                        self._loaded_plugins[plugin_name] = plugin_instance
                except Exception as e:
                    print(
                        f"[PluginManager] Falha ao instanciar classe de plugin {attr_name}: {e}",
                        file=sys.stderr,
                    )

    def register_exporter(self, exporter: IExporter) -> None:
        """Porta exposta para que os plugins injetem exportadores de novos formatos."""
        self._registered_exporters.append(exporter)
