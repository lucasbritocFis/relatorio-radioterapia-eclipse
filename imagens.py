import io
import numpy as np
import fitz
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
from typing import List, Optional


def extrair_imagens_de_pdf(caminho: str) -> List[str]:
    doc = fitz.open(caminho)
    caminhos = []

    for page in doc:
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            imagem = Image.open(io.BytesIO(base_image["image"]))

            path = f"/tmp/temp_img_{len(caminhos)}.png"
            imagem.save(path, format="PNG")
            caminhos.append(path)

    return caminhos


def extrair_imagens_de_multiplos_pdfs(caminhos_pdf: List[str]) -> List[str]:
    todos_caminhos = []
    for pdf_path in caminhos_pdf:
        todos_caminhos.extend(extrair_imagens_de_pdf(pdf_path))
    return todos_caminhos


def _eixos_com_imagem(deslocamento: list) -> List[bool]:
    return [
        float(deslocamento[2]) != 0.0,
        float(deslocamento[3]) != 0.0,
        float(deslocamento[4]) != 0.0,
    ]


def mapear_imagens_deslocamento(caminho_pdf: str, deslocamento: list) -> List[Optional[str]]:
    eixos = _eixos_com_imagem(deslocamento)
    imagens_brutas = extrair_imagens_de_pdf(caminho_pdf)
    iter_imagens = iter(imagens_brutas)

    resultado = []
    for i, tem_imagem in enumerate(eixos):
        if tem_imagem:
            imagem_path = next(iter_imagens, None)
            if imagem_path:
                novo_path = f"/tmp/temp_desloc_{i}.png"
                Image.open(imagem_path).save(novo_path, format="PNG")
                resultado.append(novo_path)
            else:
                resultado.append(None)
        else:
            resultado.append(None)

    return resultado


def converter_dvh_para_png(caminho_pdf: str, dpi: int = 300) -> str:
    paginas = convert_from_path(caminho_pdf, dpi=dpi)
    path = "/tmp/anexo_dvh.png"
    paginas[0].save(path, "PNG")
    return path


def arredondar_imagem(caminho: str, raio: int = 20) -> str:
    img = Image.open(caminho).convert("RGBA")
    largura, altura = img.size

    mascara = Image.new("L", (largura, altura), 0)
    draw = ImageDraw.Draw(mascara)
    draw.rounded_rectangle([(0, 0), (largura, altura)], radius=raio, fill=255)

    img_final = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    img_final.paste(img, (0, 0), mascara)
    img_final.save(caminho, "PNG")
    return caminho


def converter_pdfs_para_jpg(caminhos_pdf: List[str], dpi: int = 300) -> List[str]:
    caminhos_jpg = []
    for pdf_path in caminhos_pdf:
        paginas = convert_from_path(pdf_path, dpi=dpi)
        jpg_path = pdf_path.replace(".pdf", ".jpg")
        paginas[0].save(jpg_path, "JPEG")
        caminhos_jpg.append(jpg_path)
    return caminhos_jpg


def cortar_ate_texto(imagem: Image.Image, dpi: int = 300, cm_topo: float = 4, margem_px: int = 20) -> Image.Image:
    pixels_topo = int((cm_topo / 2.54) * dpi)
    largura, altura = imagem.size
    img_cortada = imagem.crop((0, pixels_topo, largura, altura))

    img_array = np.array(img_cortada.convert("L"))
    nova_altura, nova_largura = img_array.shape

    ultima_linha_com_conteudo = 0
    for y in range(nova_altura):
        if np.mean(img_array[y, :]) < 245:
            ultima_linha_com_conteudo = y

    bottom = min(ultima_linha_com_conteudo + margem_px, nova_altura)
    return img_cortada.crop((0, 0, nova_largura, bottom))
