import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

from imagens import arredondar_imagem


def _criar_overlay_nome(nome, prontuario, x=66, y_nome=740, y_id=715, tamanho=15):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)
    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(1, 1, 1)
    c.setFont("Helvetica", tamanho)
    c.drawString(x, y_nome, nome)
    c.drawString(x, y_id, f"ID: {prontuario}")
    c.save()
    packet.seek(0)
    return PdfReader(packet)


def gerar_pdf_alta(
    paciente,
    caminho_modelo,
    caminhos_jpg,
    raio_borda=60,
) -> str:

    modelo = PdfReader(caminho_modelo)
    output = PdfWriter()

    # Página 1: Capa
    pagina_capa = modelo.pages[0]
    overlay_capa = _criar_overlay_nome(
        paciente.nome_completo, paciente.prontuario,
        x=32, y_nome=620, y_id=595,
    )
    pagina_capa.merge_page(overlay_capa.pages[0])
    output.add_page(pagina_capa)

    # Página 2: Relatório de alta
    pagina_alta = modelo.pages[1]
    overlay_alta = _criar_overlay_nome(paciente.nome_completo, paciente.prontuario)
    pagina_alta.merge_page(overlay_alta.pages[0])
    output.add_page(pagina_alta)

    # Páginas 3-7: Imagens do tratamento
    for i in range(2, 7):
        pagina = modelo.pages[i]
        img_path = arredondar_imagem(caminhos_jpg[i - 2], raio=raio_borda)

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColorRGB(1, 1, 1)
        c.setFont("Helvetica", 15)
        c.drawString(66, 740, paciente.nome_completo)
        c.drawString(66, 715, f"ID: {paciente.prontuario}")
        c.drawImage(img_path, 85, 40, width=420, height=530, mask="auto")
        c.save()
        packet.seek(0)

        pagina.merge_page(PdfReader(packet).pages[0])
        output.add_page(pagina)

    # Página 8: Intacta
    output.add_page(modelo.pages[7])

    # Salvar
    caminho_saida = f"/tmp/ALTA - {paciente.nome_completo} (ID {paciente.prontuario}).pdf"
    with open(caminho_saida, "wb") as f:
        output.write(f)

    return caminho_saida
