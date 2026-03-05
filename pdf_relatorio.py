from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from desenho import (
    desenhar_logo, desenhar_rodape_barra, desenhar_barra_com_texto,
    desenhar_separador, desenhar_barra_fundo, MARGEM_ESQUERDA,
)


# --- Constantes de layout ---

ROTULOS_CAMPOS = [
    ("ID do Campo", 50),  ("Técnica", 90),        ("Máquina", 122),
    ("Energia", 170),     ("Escala", 195),         ("X1[cm]", 230),
    ("X2[cm]", 250),      ("Y1[cm]", 270),         ("Y2[cm]", 290),
    ("Gantry[deg]", 318), ("Colimador[deg]", 362), ("Mesa[deg]", 410),
    ("X[cm]", 445),       ("Y[cm]", 465),          ("Z[cm]", 485),
    ("SSD[cm]", 505),     ("UM", 540),
]

X_POSICOES_VALORES = [50, 90, 122, 170, 195, 230, 250, 270, 290, 318, 362, 410, 445, 465, 485, 505, 540]

POSICOES_IMAGENS_CORTE = [(60, 40), (320, 40), (60, 285), (320, 285)]
TAMANHO_IMAGENS_CORTE = (240, 230)
COORD_LINHAS_GRADE = [
    (50, 518, 580, 518),
    (50, 35, 580, 35),
    (50, 275, 580, 275),
    (300, 35, 300, 518),
]

INDICE_DVH = 4
NUM_PAGINAS = 5


def _desenhar_rotulos_campos(c, y):
    c.setFont("Helvetica", 6)
    for texto, x in ROTULOS_CAMPOS:
        c.drawString(x, y, texto)


def _desenhar_valores_campos(c, campos, y):
    c.setFont("Helvetica", 6)
    for bloco in campos:
        for valor, x in zip(bloco, X_POSICOES_VALORES):
            c.drawString(x, y, str(valor))
        y -= 8


def _desenhar_cabecalho_imagens(c, y, paciente, cab):
    ESPACO_LINHA = 10

    coluna_1 = [
        ("Nome do Paciente:", paciente.nome_completo),
        ("Prontuário:", paciente.prontuario),
        ("Hospital:", cab.hospital),
    ]
    coluna_2 = [
        ("Curso:", cab.curso),
        ("Imagem:", cab.imagem),
        ("Plano:", cab.plano),
        ("Orientação:", cab.orientacao),
    ]
    coluna_3 = cab.coluna_doses

    def _desenhar_coluna(x_rotulo, x_valor, itens):
        y_atual = y
        for rotulo, valor in itens:
            c.setFont("Helvetica-Bold", 6.5)
            c.drawString(x_rotulo, y_atual, str(rotulo))
            c.setFont("Helvetica", 6.5)
            c.drawString(x_valor, y_atual, str(valor))
            y_atual -= ESPACO_LINHA

    _desenhar_coluna(50, 110, coluna_1)
    _desenhar_coluna(270, 310, coluna_2)
    _desenhar_coluna(400, 540, coluna_3)


def gerar_pdf_imagens(
    paciente,
    imagens_cortes,
    todos_campos,
    cab_img,
    caminho_logo,
    caminho_faixa,
) -> str:

    caminho_saida = f"/tmp/ImagensDoTratamento_ID_{paciente.prontuario}.pdf"
    c = canvas.Canvas(caminho_saida, pagesize=letter)

    desenhar_logo(c, caminho_logo, x=480, y=735, largura=110, altura=40)
    c.drawImage(caminho_faixa, 50, 725, width=530, height=3)

    desenhar_rodape_barra(c)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.black)
    c.drawString(MARGEM_ESQUERDA, 754, "INFORMAÇÕES TÉCNICAS DO PLANEJAMENTO DO TRATAMENTO")

    desenhar_barra_com_texto(c, 643, cab_img.plano_curso_texto, fonte_tamanho=9)
    desenhar_separador(c, MARGEM_ESQUERDA, 580, 632)

    _desenhar_cabecalho_imagens(c, 705, paciente, cab_img)
    _desenhar_rotulos_campos(c, 635)
    _desenhar_valores_campos(c, todos_campos, 622)

    desenhar_barra_fundo(c, 48, 520, 535, 20)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(MARGEM_ESQUERDA, 527,
        f"Representação Gráfica do Planejamento do Tratamento: {cab_img.nome_paciente_img}")

    for img, (x, y) in zip(imagens_cortes[:4], POSICOES_IMAGENS_CORTE):
        c.drawImage(img, x, y, width=TAMANHO_IMAGENS_CORTE[0], height=TAMANHO_IMAGENS_CORTE[1])

    for x1, y1, x2, y2 in COORD_LINHAS_GRADE:
        c.line(x1, y1, x2, y2)

    c.setFont("Helvetica", 6)
    c.setFillColor(colors.black)
    c.drawString(50, 20, cab_img.rodape_impresso_por)
    c.drawString(310, 20, f"Última Modificação do plano: {cab_img.rodape_ultima_mod}")

    c.save()
    return caminho_saida


def gerar_paginas_individuais(
    paciente,
    imagens_cortes,
    todos_campos,
    cab_img,
    caminho_dvh,
) -> list:

    caminhos_pdf = []

    for idx in range(NUM_PAGINAS):
        pdf_path = f"/tmp/imagens_{idx}.pdf"
        caminhos_pdf.append(pdf_path)

        c = canvas.Canvas(pdf_path, pagesize=letter)

        desenhar_barra_com_texto(c, 704, f"Informações dos {cab_img.plano_curso_texto}")
        c.setFont("Helvetica", 6)
        c.setStrokeColor(colors.black)

        _desenhar_cabecalho_imagens(c, 770, paciente, cab_img)
        _desenhar_rotulos_campos(c, 690)
        desenhar_separador(c, 50, 580, 688)
        _desenhar_valores_campos(c, todos_campos, 675)

        if idx < INDICE_DVH:
            c.drawImage(imagens_cortes[idx], 70, 50, width=500, height=500)
            desenhar_barra_com_texto(c, 554,
                "Representação Gráfica do Planejamento do Tratamento")
        else:
            c.drawImage(caminho_dvh, 45, 170, width=540, height=400)
            desenhar_barra_com_texto(c, 554, "Histograma Dose Volume")

        c.save()

    return caminhos_pdf
