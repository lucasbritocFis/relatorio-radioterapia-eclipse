import streamlit as st
import tempfile
import os

from config import LOGO_REDE_AMERICAS, FAIXA_ROXA, PDF_MODELO_ALTA, ASSINATURAS
from extracao import extrair_texto_com_fitz, extrair_texto_com_pdfplumber, extrair_dados_paciente
from parsing import (
    extrair_cabecalho_campos, encontrar_indice, separar_campos,
    limpar_campos, detectar_bolus, extrair_dados_qa,
    extrair_deslocamento, extrair_cabecalho_imagens,
)
from imagens import (
    extrair_imagens_de_multiplos_pdfs, mapear_imagens_deslocamento,
    converter_dvh_para_png, converter_pdfs_para_jpg,
)
from pdf_relatorio import gerar_pdf_relatorio
from pdf_imagens import gerar_pdf_imagens, gerar_paginas_individuais
from pdf_alta import gerar_pdf_alta


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Gerador de Relatórios - Radioterapia",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Gerador de Relatórios de Radioterapia")
st.caption("Faça upload dos PDFs, ajuste as opções e gere os relatórios.")


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

def salvar_upload_em_temp(uploaded_file) -> str:
    """Salva um arquivo uploaded pelo Streamlit em /tmp e retorna o caminho."""
    sufixo = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo, dir="/tmp") as f:
        f.write(uploaded_file.read())
        return f.name


def botao_download(label, caminho, nome_arquivo):
    """Cria um botão de download para um arquivo gerado."""
    with open(caminho, "rb") as f:
        st.download_button(
            label=label,
            data=f.read(),
            file_name=nome_arquivo,
            mime="application/pdf",
        )


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — UPLOADS E OPÇÕES
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("📁 Upload dos PDFs")

    upload_relatorio = st.file_uploader("PDF do Relatório (*REL.pdf)", type="pdf", key="rel")
    upload_qa = st.file_uploader("PDF do Controle de Qualidade (CQ.pdf)", type="pdf", key="qa")
    upload_dvh = st.file_uploader("PDF do DVH", type="pdf", key="dvh")

    st.markdown("**Imagens dos cortes** (AXI, COR, SAG, 3D)")
    upload_imagens = st.file_uploader(
        "Selecione os 4 PDFs de imagens",
        type="pdf",
        accept_multiple_files=True,
        key="imgs",
    )

    st.divider()
    st.header("⚙️ Opções")

    # --- Assinaturas ---
    nomes_disponiveis = list(ASSINATURAS.keys())

    planejador = st.selectbox(
        "Planejado por (1ª assinatura)",
        nomes_disponiveis,
        index=0,
    )

    verificador = st.selectbox(
        "Verificado por (2ª assinatura)",
        [n for n in nomes_disponiveis if n != planejador],
        index=0,
    )

    # --- Bólus ---
    opcao_bolus = st.radio(
        "O plano tem bólus?",
        ["Detectar automaticamente", "Sim", "Não"],
        index=0,
    )

    st.divider()
    gerar = st.button("🚀 Gerar Relatórios", type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def validar_uploads():
    erros = []
    if not upload_relatorio:
        erros.append("PDF do Relatório")
    if not upload_qa:
        erros.append("PDF do CQ")
    if not upload_dvh:
        erros.append("PDF do DVH")
    if not upload_imagens or len(upload_imagens) != 4:
        erros.append("4 PDFs de imagens (AXI, COR, SAG, 3D)")
    return erros


# ══════════════════════════════════════════════════════════════════════════════
# GERAÇÃO DOS RELATÓRIOS
# ══════════════════════════════════════════════════════════════════════════════

if gerar:
    erros = validar_uploads()
    if erros:
        st.error(f"Faltam arquivos: {', '.join(erros)}")
        st.stop()

    with st.spinner("Processando PDFs..."):

        # --- Salvar uploads em /tmp ---
        caminho_relatorio = salvar_upload_em_temp(upload_relatorio)
        caminho_qa = salvar_upload_em_temp(upload_qa)
        caminho_dvh_upload = salvar_upload_em_temp(upload_dvh)
        caminhos_imagens = [salvar_upload_em_temp(f) for f in upload_imagens]

        # --- Assinaturas do servidor ---
        caminho_ass_1 = ASSINATURAS[planejador]
        caminho_ass_2 = ASSINATURAS[verificador]

    with st.spinner("Extraindo texto dos PDFs..."):

        # --- Leitura ---
        texto_rel = extrair_texto_com_fitz(caminho_relatorio)
        texto_qa = extrair_texto_com_pdfplumber(caminho_qa)
        texto_img = extrair_texto_com_fitz(caminhos_imagens[0])
        linhas = texto_rel.splitlines()

        # --- Dados do paciente ---
        paciente = extrair_dados_paciente(texto_rel)

    with st.spinner("Parseando campos e dados..."):

        # --- Parsing campos ---
        cabecalho = extrair_cabecalho_campos(linhas)
        maquina = cabecalho[1].upper()

        idx_mu = encontrar_indice(linhas, "MU")
        idx_fim = encontrar_indice(linhas, "Físico(a) 1:")
        cps = linhas[idx_mu + 1 : idx_fim]
        setup, tratamento = separar_campos(cps)
        setup_limpo = limpar_campos(setup)
        tratamento_limpo = limpar_campos(tratamento)

        # --- Bólus: manual ou automático ---
        if opcao_bolus == "Sim":
            tem_bolus = True
        elif opcao_bolus == "Não":
            tem_bolus = False
        else:
            tem_bolus = detectar_bolus(tratamento_limpo)

        ids_localizacao = ", ".join(campo[0] for campo in setup_limpo if campo)

        # --- QA ---
        dados_qa = extrair_dados_qa(texto_qa)

        # --- Deslocamento ---
        deslocamento = extrair_deslocamento(linhas)
        imagens_desloc = mapear_imagens_deslocamento(caminho_relatorio, deslocamento)

        # --- Cabeçalho imagens ---
        cab_img = extrair_cabecalho_imagens(texto_img)

    with st.spinner("Extraindo imagens..."):

        # --- Imagens ---
        imagens_cortes = extrair_imagens_de_multiplos_pdfs(caminhos_imagens)
        caminho_dvh = converter_dvh_para_png(caminho_dvh_upload)

        # --- Preparar campos para PDF de imagens ---
        PALAVRAS_REMOVER = {"Bólus", "Horário", "Anti-Horário", "Campo de setup"}

        for item in setup_limpo:
            item[:] = [v for v in item if v not in PALAVRAS_REMOVER]
            item.insert(1, "STATIC-I")
            item[4] = "IEC61217"
            item.append("Localização")

        for i, item in enumerate(tratamento_limpo):
            item[:] = [v for v in item if v not in PALAVRAS_REMOVER]
            item[3] = "IEC61217"
            item.insert(1, cab_img.tecnicas_campo[i])
            del item[-2]

        todos_campos = setup_limpo + tratamento_limpo

    # --- Mostrar dados extraídos ---
    st.success(f"Paciente: **{paciente.nome_completo}** | Prontuário: **{paciente.prontuario}**")

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Campos de tratamento", len(tratamento_limpo))
    with col_info2:
        st.metric("Campos de setup", len(setup_limpo))
    with col_info3:
        st.metric("Bólus", "Sim" if tem_bolus else "Não")

    # --- Gerar PDFs ---
    with st.spinner("Gerando PDF do Relatório..."):
        pdf_rel = gerar_pdf_relatorio(
            paciente=paciente,
            cabecalho=cabecalho,
            campos_tratamento_limpos=tratamento_limpo,
            dados_qa=dados_qa,
            deslocamento=deslocamento,
            imagens_desloc=imagens_desloc,
            tem_bolus=tem_bolus,
            ids_localizacao=ids_localizacao,
            maquina=maquina,
            caminho_logo=LOGO_REDE_AMERICAS,
            caminho_assinatura_1=caminho_ass_1,
            caminho_assinatura_2=caminho_ass_2,
        )

    with st.spinner("Gerando PDF das Imagens..."):
        pdf_img = gerar_pdf_imagens(
            paciente=paciente,
            imagens_cortes=imagens_cortes,
            todos_campos=todos_campos,
            cab_img=cab_img,
            caminho_logo=LOGO_REDE_AMERICAS,
            caminho_faixa=FAIXA_ROXA,
        )

    with st.spinner("Gerando páginas individuais e relatório de alta..."):
        caminhos_individuais = gerar_paginas_individuais(
            paciente=paciente,
            imagens_cortes=imagens_cortes,
            todos_campos=todos_campos,
            cab_img=cab_img,
            caminho_dvh=caminho_dvh,
        )

        jpgs = converter_pdfs_para_jpg(caminhos_individuais)

        pdf_alta = gerar_pdf_alta(
            paciente=paciente,
            caminho_modelo=PDF_MODELO_ALTA,
            caminhos_jpg=jpgs,
        )

    # ══════════════════════════════════════════════════════════════════════
    # DOWNLOADS
    # ══════════════════════════════════════════════════════════════════════

    st.divider()
    st.header("📥 Downloads")

    col1, col2, col3 = st.columns(3)

    with col1:
        botao_download(
            "⬇️ Relatório de Tratamento",
            pdf_rel,
            f"RelatorioDoTratamento_ID_{paciente.prontuario}.pdf",
        )

    with col2:
        botao_download(
            "⬇️ Imagens do Tratamento",
            pdf_img,
            f"ImagensDoTratamento_ID_{paciente.prontuario}.pdf",
        )

    with col3:
        botao_download(
            "⬇️ Relatório de Alta",
            pdf_alta,
            f"ALTA - {paciente.nome_completo} (ID {paciente.prontuario}).pdf",
        )

    st.balloons()
