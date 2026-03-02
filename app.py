import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors # Necessário para cores
import io
import base64
import fitz  
import pdfplumber  
import re # Necessário para busca de texto

# 1. Configuração inicial da página web
st.set_page_config(page_title="Gerador de Relatórios de Planejamentos Eclipse", layout="centered")
st.title("Gerador de Relatórios de Planejamentos Eclipse")
st.markdown("Faça o upload dos PDFs do sistema para extrair os dados.")

# 2. Caminhos das imagens fixas
LOGO_AMERICAS = "assets/logo_rede_americas.png"
FAIXA_ROXA = "assets/faixa_degrade_roxo.png"
ASS_GUILHERME = "assets/ass_guilherme_carimbada.jpg"
ASS_LUCAS = "assets/ass_lucas_carimbada.jpg"

# 3. Funções de Extração de Texto
def extrair_texto_pdf_qa(arquivo_uplodado):
    texto_completo = ""
    with pdfplumber.open(arquivo_uplodado) as pdf:
        for page in pdf.pages:
            texto_extraido = page.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
    return texto_completo

def extrair_texto_pdf_relatorio(arquivo_uplodado):
    bytes_pdf = arquivo_uplodado.read()
    doc = fitz.open(stream=bytes_pdf, filetype="pdf")
    texto_completo = ""
    for page in doc:
        texto_completo += page.get_text()
    arquivo_uplodado.seek(0) 
    return texto_completo

# --- FUNÇÕES DE BUSCA (Regex) ---
def buscar_no_texto(texto, padrao, default="Não encontrado"):
    match = re.search(padrao, texto)
    return match.group(1).strip() if match else default

def extrair_dados_basicos(texto):
    """Retorna um dicionário com os dados fundamentais do paciente"""
    return {
        "Nome": buscar_no_texto(texto, r"Nome:\s*(.+?)\s*Data")[:28],
        "Prontuário": buscar_no_texto(texto, r"Prontuário:\s*(\d+)"),
        "Hospital": "ONCOBARRA - REDE AMÉRICAS" 
    }

# --- FUNÇÕES DE DESENHO DO PDF ---
def inserir_logo_no_relatorio(c):
    try:
        c.drawImage(LOGO_AMERICAS, 435, 720, 150, 50, mask='auto')
    except:
        st.warning("⚠️ Logo não encontrada na pasta assets.")

def desenhar_retangulos(c):
    c.setFillColorRGB(0.85, 0.85, 0.85) 
    c.roundRect(55, 610, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 425, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 370, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 127, 535, 18, radius=5, fill=1, stroke=0)

def desenhar_informacoes_paciente(c, dados):
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    
    # Textos do cabeçalho
    c.drawString(60, 705, f"Nome: {dados['Nome']}")
    c.drawString(60, 685, f"Prontuário: {dados['Prontuário']}")
    c.drawString(60, 665, f"Hospital: {dados['Hospital']}")
    
    # Título do primeiro retângulo
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, 617, "DESLOCAMENTO DA MESA (SETUP)")

# --- GERADOR DO PDF NA MEMÓRIA ---
def gerar_pdf_relatorio(dados_paciente):
    buffer_pdf = io.BytesIO()
    c_relatorio = canvas.Canvas(buffer_pdf, pagesize=letter)
    
    inserir_logo_no_relatorio(c_relatorio)
    desenhar_retangulos(c_relatorio)
    desenhar_informacoes_paciente(c_relatorio, dados_paciente)
    
    c_relatorio.save()
    buffer_pdf.seek(0)
    return buffer_pdf

# --- FUNÇÃO DE PREVIEW ---
def mostrar_preview_pdf(buffer_pdf):
    doc = fitz.open(stream=buffer_pdf.read(), filetype="pdf")
    pagina = doc.load_page(0)
    pix = pagina.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_data = pix.tobytes("png")
    st.image(img_data, caption="Pré-visualização do Relatório", use_container_width=True)
    buffer_pdf.seek(0)

# 4. Interface do Usuário
st.subheader("1. Importação dos Arquivos")
pdf_relatorio = st.file_uploader("Upload do Relatório (REL)", type=["pdf"])
pdf_qa = st.file_uploader("Upload do Controle de Qualidade (CQ)", type=["pdf"])
pdfs_imagens = st.file_uploader("Upload dos PDFs de Imagens", type=["pdf"], accept_multiple_files=True)

# 5. Lógica de Processamento
st.subheader("2. Processamento")

# Usamos session_state para manter os dados na tela entre cliques de botões
if pdf_relatorio and pdf_qa:
    if st.button("Extrair Dados do Paciente"):
        with st.spinner("Lendo PDFs..."):
            texto_rel = extrair_texto_pdf_relatorio(pdf_relatorio)
            # Guardamos os dados extraídos no "estado" do site
            st.session_state.dados_paciente = extrair_dados_basicos(texto_rel)
            st.success("Dados extraídos!")

# Se os dados já foram extraídos, mostramos as opções de geração
if 'dados_paciente' in st.session_state:
    dados = st.session_state.dados_paciente
    st.info(f"📋 **Paciente:** {dados['Nome']} | **ID:** {dados['Prontuário']}")

    st.subheader("3. Geração do Relatório")
    if st.button("Gerar Preview do Relatório"):
        with st.spinner("Desenhando PDF..."):
            pdf_final = gerar_pdf_relatorio(dados)
            mostrar_preview_pdf(pdf_final)
            
            st.download_button(
                label="📥 Baixar PDF Final",
                data=pdf_final,
                file_name=f"Relatorio_{dados['Nome']}_{dados['Prontuário']}.pdf",
                mime="application/pdf"
            )
