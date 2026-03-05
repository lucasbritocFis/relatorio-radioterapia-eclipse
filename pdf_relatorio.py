from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from desenho import (
    desenhar_retangulos_relatorio, desenhar_logo, desenhar_titulo_relatorio,
    desenhar_informacoes_paciente, desenhar_deslocamento, desenhar_textos_fixos,
    desenhar_labels_campos, desenhar_valores_campos, desenhar_controle_qualidade,
    desenhar_assinaturas,
)


def gerar_pdf_relatorio(
    paciente,
    cabecalho,
    campos_tratamento_limpos,
    dados_qa,
    deslocamento,
    imagens_desloc,
    tem_bolus,
    ids_localizacao,
    maquina,
    caminho_logo,
    caminho_assinatura_1,
    caminho_assinatura_2,
) -> str:

    caminho_saida = f"/tmp/RelatorioDoTratamento_ID_{paciente.prontuario}.pdf"
    c = canvas.Canvas(caminho_saida, pagesize=letter)

    desenhar_retangulos_relatorio(c)
    desenhar_logo(c, caminho_logo)
    desenhar_titulo_relatorio(c, paciente.cabecalho_relatorio)
    desenhar_informacoes_paciente(c, paciente)
    desenhar_deslocamento(c, deslocamento, imagens_desloc)
    desenhar_textos_fixos(c, maquina, ids_localizacao, tem_bolus)
    desenhar_labels_campos(c, cabecalho, tem_bolus)
    desenhar_valores_campos(c, campos_tratamento_limpos)
    desenhar_controle_qualidade(c, dados_qa)
    desenhar_assinaturas(c, caminho_assinatura_1, caminho_assinatura_2)

    c.save()
    return caminho_saida
