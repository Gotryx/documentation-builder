"""
Script de Entrada Principal (Entrypoint) do GoTryx Documentation Builder.
Permite iniciar em modo gráfico (GUI) ou em modo automação headless (CLI)
através da passagem do argumento '--cli'.
"""

import sys
from pathlib import Path

# Adiciona o diretório atual ao sys.path para garantir as importações corretas do pacote docbuilder
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def main() -> None:
    # Verifica se a chamada deve ser desviada para a CLI (modo ferramenta headless)
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # Remove a flag '--cli' para que o argparse na cli.py não quebre
        sys.argv.pop(1)
        from docbuilder.app.cli import main as cli_main

        cli_main()
    else:
        # Modo GUI por padrão
        from docbuilder.ui.main_window import run_app

        # Pode passar um diretório inicial se for provido como argumento
        start_dir = (
            Path(sys.argv[1])
            if len(sys.argv) > 1 and Path(sys.argv[1]).exists()
            else None
        )
        run_app(start_dir)


if __name__ == "__main__":
    main()
