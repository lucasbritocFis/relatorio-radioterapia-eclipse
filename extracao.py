from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

from parsing import limpar_nome_coluna


# --- Constantes visuais ---

COR_FUNDO_BARRA = (0.85, 0.85, 0.85)
COR_BADGE_APROVADO = (0.9, 1, 0.9)
COR_BADGE_DESTAQUE = (1, 0.8, 0.8)
COR_BADGE_BOLUS = (1, 0.8, 0.8)
MARGEM_ESQUERDA = 50


# --- Primitivas ---

def desenhar_barra_fundo(c, x, y, largura, altura, radius=5):
    c.setFillColorRGB(*COR_FUNDO_BARRA)
    c.roundRect(x, y, largura, altura, radius=radius, fill=1, stroke=0)
    c.setFillColor(colors.black)


def desenhar_barra_com_texto(c, y_barra, texto, largura=535, fonte_tamanho=9):
    desenhar_barra_fundo(c, 45, y_barra, largura, 18)
    c.setFont("Helvetica-Bold", fonte_tamanho)
    c.drawString(MARGEM_ESQUERDA, y_barra + 6, texto)


def desenhar_separador(c, x_inicio, x_fim, y, espessura=0.5):
    c.setLineWidth(espessura)
    c.setStrokeColor(colors.black)
    c.line(x_inicio, y, x_fim, y)


def desenhar_badge(c, x, y, texto, cor_fundo, cor_texto, fonte="Helvetica-Bold", tamanho=7):
    largura = c.stringWidth(texto, fonte, tamanho) + 8
    c.setFillColorRGB(*cor_fundo)
    c.roundRect(x - 2, y - 3, largura, 10, 2, fill=1, stroke=0)
    c.setFillColor(cor_texto)
    c.setFont(fonte, tamanho)
    c.drawString(x, y, texto)


def restaurar_estado(c, fonte="Helvetica", tamanho=7):
    c.setFont(fonte, tamanho)
    c.setFillColor(colors.black)


# --- Logo e título ---

def desenhar_logo(c, caminho_logo, x=435, y=720, largura=170, altura=60):
    c.drawImage(caminho_logo, x, y, largura, altura)


def desenhar_titulo_relatorio(c, texto, x=60, y=740):
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, texto)
    c.rect(x - 2, y - 15, 530, 2, fill=1, stroke=0)


# --- Informações do paciente ---

def desenhar_informacoes_paciente(c, paciente, y_inicio=700, espacamento=20):
    COLUNA_ESQ = (60, 155)
    COLUNA_DIR = (315, 407)
    ITENS_POR_COLUNA = 4

    pares = [
        ("Nome", paciente.nome),
        ("Data de Nascimento", paciente.data_nascimento),
        ("Prontuário", paciente.prontuario),
        ("Radio-Oncologista", paciente.radio_oncologista),
        ("Curso/Plano", paciente.curso_plano),
        ("Tomografia", paciente.tomografia),
        ("Dose de Prescrição", paciente.dose_prescricao),
        ("Curva de Prescrição", paciente.curva_prescricao),
    ]

    c.setFillColor(colors.black)
    for i, (chave, valor) in enumerate(pares):
        x_chave, x_valor = COLUNA_ESQ if i < ITENS_POR_COLUNA else COLUNA_DIR
        linha = i % ITENS_POR_COLUNA
        y = y_inicio - linha * espacamento

        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_chave, y, f"{chave}:")
        c.setFont("Helvetica", 9)
        c.drawString(x_valor, y, valor)


# --- Retângulos fixos ---

def desenhar_retangulos_relatorio(c):
    posicoes = [(55, 610, 20), (55, 425, 20), (55, 370, 20), (55, 127, 18)]
    for x, y, altura in posicoes:
        desenhar_barra_fundo(c, x, y, 535, altura)


# --- Textos fixos ---

def desenhar_textos_fixos(c, maquina, ids_localizacao, tem_bolus):
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(60, 377, f"INFORMAÇÕES DOS CAMPOS DE TRATAMENTO - {maquina} EDGE_SN5253")
    c.drawString(60, 432, "INFORMAÇÕES ADICIONAIS")
    c.drawString(60, 132, "CONTROLE DE QUALIDADE - EQUIPAMENTO USADO: EPID, METODOLOGIA USADA: ANÁLISE GAMA")

    c.setFont("Helvetica", 7)
    c.drawString(60, 35, "PLANEJADO POR: ")
    c.drawString(330, 35, "VERIFICADO POR: ")
    c.drawString(60, 405, f"CAMPOS DE LOCALIZAÇÃO DO PLANO: {ids_localizacao}")

    texto_bolus = "TRATAMENTO COM BÓLUS" if tem_bolus else "TRATAMENTO SEM BÓLUS"

    if tem_bolus:
        desenhar_badge(c, 350, 405, texto_bolus, COR_BADGE_BOLUS, colors.black)
    else:
        c.setFont("Helvetica", 7)
        c.drawString(350, 405, texto_bolus)

    restaurar_estado(c)


# --- Labels laterais dos campos ---

INDICES_IGNORADOS_BASE = {1, 12, 13, 15, 20, 21, 22}
INDICE_EXTRA_SEM_BOLUS = {14}


def desenhar_labels_campos(c, cabecalho, tem_bolus, y_inicio=367, espacamento=12):
    indices_ignorados = (
        INDICES_IGNORADOS_BASE
        if tem_bolus
        else INDICES_IGNORADOS_BASE | INDICE_EXTRA_SEM_BOLUS
    )

    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    y = y_inicio

    for i, linha in enumerate(cabecalho):
        if i in indices_ignorados:
            continue
        y -= espacamento
        c.drawString(60, y, limpar_nome_coluna(linha))


# --- Valores dos campos ---

FILTRO_MAQUINA = "EDGE_SN5253"


def desenhar_valores_campos(c, campos_limpos, y_inicio=367, x_inicio=130, espaco_coluna=50, espacamento=12):
    c.setFont("Helvetica", 7)

    for col, campo in enumerate(campos_limpos):
        x = x_inicio + col * espaco_coluna
        y = y_inicio

        for i, valor in enumerate(campo):
            if FILTRO_MAQUINA in valor:
                continue

            y -= espacamento
            eh_ultimo = (i == len(campo) - 1)

            if eh_ultimo:
                desenhar_badge(c, x, y, valor, COR_BADGE_DESTAQUE, colors.red)
            else:
                c.setFont("Helvetica", 7)
                c.setFillColor(colors.black)
                c.drawString(x, y, valor)

    restaurar_estado(c)


# --- Controle de qualidade ---

LABELS_QA = ["Campo", "Gama DTA", "Tolerância", "Área gama < 1,0", "Resultado"]


def desenhar_controle_qualidade(c, dados_qa, y_inicio=120, x_inicio=130, espaco_coluna=60, espacamento=10):
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)

    for i, texto in enumerate(LABELS_QA):
        c.drawString(60, y_inicio - i * espacamento, texto)

    for i, (campo, gama, area, area_dupla, resultado) in enumerate(dados_qa):
        x = x_inicio + i * espaco_coluna
        y = y_inicio

        c.drawString(x, y, campo.replace("Campo", ""))
        c.drawString(x, y - 10, f"{gama[1]} % / {gama[0]} mm")
        c.drawString(x, y - 20, f"{area_dupla[1]} %")
        c.drawString(x, y - 30, f"{area} %")

        resultado_fmt = resultado.strip().lower().replace("aprovado", "Aprovado")
        desenhar_badge(c, x, y - 40, resultado_fmt, COR_BADGE_APROVADO, colors.limegreen)
        restaurar_estado(c)


# --- Deslocamento da mesa ---

def desenhar_deslocamento(c, deslocamento, imagens_desloc, y_barra=610):
    dados_colunas = [
        ("LATERAL",      deslocamento[2], deslocamento[6], 115),
        ("VERTICAL",     deslocamento[3], deslocamento[7], 300),
        ("LONGITUDINAL", deslocamento[4], deslocamento[8], 485),
    ]

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(60, y_barra + 7.5, deslocamento[0].upper())

    c.setFont("Helvetica", 7)
    for titulo, valor, direcao, x in dados_colunas:
        c.drawString(x, y_barra - 4.5, titulo)
        c.drawString(x, y_barra - 14.5, f"{valor.upper()} cm {direcao.upper()}")

    posicoes_x = [70, 225, 410]
    for x, imagem in zip(posicoes_x, imagens_desloc):
        if imagem:
            c.drawImage(imagem, x, y_barra - 132.5, width=160, height=100)


# --- Assinaturas ---

def desenhar_assinaturas(c, caminho_assinatura_1, caminho_assinatura_2):
    c.drawImage(caminho_assinatura_1, 130, 19, 110, 40)
    c.drawImage(caminho_assinatura_2, 400, 11, 120, 50)


# --- Rodapé ---

def desenhar_rodape_barra(c):
    c.setLineWidth(20)
    c.line(0, 5, 650, 5)
