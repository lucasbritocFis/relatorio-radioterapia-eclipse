import re
from datetime import datetime
import pdfplumber
import fitz

from modelo import DadosPaciente


def buscar_no_texto(texto: str, padrao: str, default: str = "") -> str:
    match = re.search(padrao, texto)
    return match.group(1).strip() if match else default


def extrair_texto_com_pdfplumber(caminho: str) -> str:
    with pdfplumber.open(caminho) as pdf:
        if not pdf.pages:
            raise ValueError("O PDF está vazio.")
        texto = "\n".join(
            page.extract_text() for page in pdf.pages if page.extract_text()
        )
        if not texto.strip():
            raise ValueError("Não foi possível extrair texto do PDF.")
        return texto


def extrair_texto_com_fitz(caminho: str) -> str:
    doc = fitz.open(caminho)
    return "".join(page.get_text() for page in doc)


def _formatar_cabecalho_relatorio(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto).split("-")[0].strip()
    texto = re.sub(r'(\b\w) (?=\w\b)', r'\1', texto)
    return f"{texto[:9]} {texto[9:11]} {texto[11:16]} {texto[16:18]} {texto[18:28]}"


def extrair_dados_paciente(texto_relatorio: str) -> DadosPaciente:
    nome_completo = buscar_no_texto(texto_relatorio, r"Nome:\s*(.+?)\s*Data")

    data_nasc_str = buscar_no_texto(texto_relatorio, r"Data de Nasc.:\s*(.+?)\s*Pront")
    try:
        data_nascimento = datetime.strptime(data_nasc_str, "%A, %B %d, %Y").strftime("%d/%m/%Y")
    except ValueError:
        data_nascimento = data_nasc_str

    return DadosPaciente(
        nome=nome_completo[:28],
        nome_completo=nome_completo,
        prontuario=buscar_no_texto(texto_relatorio, r"Prontuário:\s*(\d+)"),
        data_nascimento=data_nascimento,
        radio_oncologista=buscar_no_texto(texto_relatorio, r"Radio-Oncologista:\s*(.+)"),
        curso_plano=buscar_no_texto(texto_relatorio, r"Curso / Plano:\s*(.+)"),
        tomografia=buscar_no_texto(texto_relatorio, r"Imagem Utilizada:\s*(.+)"),
        dose_prescricao=buscar_no_texto(texto_relatorio, r"Dose de Prescrição:\s*(.+)"),
        curva_prescricao=buscar_no_texto(texto_relatorio, r"Curva de Prescrição:\s*(.+)"),
        cabecalho_relatorio=_formatar_cabecalho_relatorio(texto_relatorio),
    )
