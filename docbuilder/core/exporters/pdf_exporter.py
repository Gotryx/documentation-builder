"""
Implementação do exportador de formato PDF utilizando o LibreOffice Headless.
Utiliza o DocxExporter para gerar uma versão do Word intermediária e a converte em PDF via linha de comando do LibreOffice.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from docbuilder.core.domain.entities import TemplateStyle
from docbuilder.core.domain.interfaces import IExporter
from docbuilder.core.exporters.docx_exporter import DocxExporter


class PdfExporter(IExporter):
    """
    Exportador encarregado de gerar arquivos PDF de alta qualidade gráfica
    utilizando a engine de renderização do LibreOffice headless.
    """

    def __init__(self, docx_exporter: DocxExporter = None) -> None:
        # Reutiliza o exportador de DOCX para a primeira etapa do pipeline
        self._docx_exporter = docx_exporter or DocxExporter()

    def get_supported_format(self) -> str:
        return "pdf"

    def export(self, source_document_path: Path, output_path: Path, template: TemplateStyle) -> None:
        # Cria uma pasta temporária segura para a conversão intermediária
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_docx_path = temp_dir_path / "documento_intermediario.docx"

            # 1. Gera o DOCX intermediário
            self._docx_exporter.export(source_document_path, temp_docx_path, template)

            # 2. Invoca o LibreOffice Headless para converter DOCX em PDF
            # A chamada padrão é: libreoffice --headless --convert-to pdf --outdir <dir> <arquivo>
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_dir_path),
                str(temp_docx_path)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"O LibreOffice headless falhou ao converter o arquivo para PDF.\n"
                    f"Erro CLI: {e.stderr.strip() or e.stdout.strip()}"
                )
            except FileNotFoundError:
                raise RuntimeError(
                    "O executável 'libreoffice' não foi encontrado no PATH do sistema.\n"
                    "Certifique-se de que o LibreOffice está instalado."
                )

            # O LibreOffice cria um arquivo com o mesmo nome, alterando apenas a extensão para .pdf
            generated_pdf = temp_dir_path / "documento_intermediario.pdf"
            if not generated_pdf.exists():
                raise FileNotFoundError("O arquivo PDF esperado não foi gerado pelo LibreOffice.")

            # 3. Move o PDF temporário para o caminho final de saída
            # Garante que a pasta de destino exista
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()
            
            shutil.move(generated_pdf, output_path)
