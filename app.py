
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import base64

# 1. Configuração inicial da página web
st.set_page_config(page_title="Gerador de Relatórios de Planejamentos Eclipse", layout="centered")
st.title("Gerador de Relatórios de Planejamentos Eclipse")
st.markdown("Faça o upload dos PDFs do sistema para extrair os dados.")

# 2. Caminhos das imagens fixas (Banco de dados de imagens)
# Como estarão na pasta "assets" do seu GitHub, usamos o caminho relativo:
LOGO_AMERICAS = "assets/logo_rede_americas.png"
FAIXA_ROXA = "assets/faixa_degrade_roxo.png"
ASS_GUILHERME = "assets/ass_guilherme_carimbada.jpg"
ASS_LUCAS = "assets/ass_lucas_carimbada.jpg"

# 3. Funções de Extração (Adaptadas para Memória RAM)
def extrair_texto_pdf_qa(arquivo_uplodado):
    """Extrai texto do CQ usando pdfplumber diretamente da memória"""
    texto_completo = ""
    with pdfplumber.open(arquivo_uplodado) as pdf:
        for page in pdf.pages:
            texto_extraido = page.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
    return texto_completo

def extrair_texto_pdf_relatorio(arquivo_uplodado):
    """Extrai texto do Relatório usando PyMuPDF (fitz) da memória"""
    bytes_pdf = arquivo_uplodado.read()
    doc = fitz.open(stream=bytes_pdf, filetype="pdf")
    texto_completo = ""
    for page in doc:
        texto_completo += page.get_text()
    
    # Reseta o ponteiro do arquivo caso precisemos ler de novo depois
    arquivo_uplodado.seek(0) 
    return texto_completo

# --- 1. A SUA FUNÇÃO DE DESENHO (Exatamente como você fez) ---
def desenhar_retangulos(c):
    c.setFillColorRGB(0.85, 0.85, 0.85) # cinza
    c.roundRect(55, 610, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 425, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 370, 535, 20, radius=5, fill=1, stroke=0)
    c.roundRect(55, 127, 535, 18, radius=5, fill=1, stroke=0)

# --- 2. GERADOR DO PDF NA MEMÓRIA ---
def gerar_pdf_relatorio():
    """Gera o PDF na Memória RAM e retorna o arquivo em bytes"""
    buffer_pdf = io.BytesIO()
    
    # Apontamos o Canvas para o 'buffer' em vez de um arquivo no disco
    c_relatorio = canvas.Canvas(buffer_pdf, pagesize=letter)
    
    # Desenhamos os retângulos
    desenhar_retangulos(c_relatorio)
    
    # Salva o arquivo na memória
    c_relatorio.save()
    
    # Volta o "ponteiro" da leitura para o começo do arquivo
    buffer_pdf.seek(0)
    return buffer_pdf

# --- 3. FUNÇÃO DE PREVIEW NO STREAMLIT ---
def mostrar_preview_pdf(buffer_pdf):
    """Lê os bytes do PDF e mostra um visualizador dentro do site"""
    # Converte os bytes do PDF para o formato Base64
    base64_pdf = base64.b64encode(buffer_pdf.getvalue()).decode('utf-8')
    
    # Cria o visualizador usando HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    
    # Renderiza o HTML no Streamlit
    st.markdown(pdf_display, unsafe_allow_html=True)

# 4. Interface do Usuário: Botões de Upload
st.subheader("1. Importação dos Arquivos")
pdf_relatorio = st.file_uploader("Upload do Relatório (REL)", type=["pdf"])
pdf_qa = st.file_uploader("Upload do Controle de Qualidade (CQ)", type=["pdf"])

# O accept_multiple_files permite selecionar AXI, COR, SAG e 3D de uma vez
pdfs_imagens = st.file_uploader("Upload dos PDFs de Imagens", type=["pdf"], accept_multiple_files=True)

# 5. Ação principal
st.subheader("2. Processamento")
if st.button("Extrair Dados Iniciais"):
    
    # Validação de segurança (Fail Fast)
    if not pdf_relatorio or not pdf_qa:
        st.error("Por favor, envie o Relatório e o CQ para continuar.")
    else:
        with st.spinner("Lendo PDFs em memória..."):
            
            # Executa as funções de leitura
            text_relatorio = extrair_texto_pdf_relatorio(pdf_relatorio)
            text_qa = extrair_texto_pdf_qa(pdf_qa)
            
            st.success("Leitura concluída com sucesso!")
            
            # Mostra uma prévia na tela apenas para você confirmar que a extração funcionou
            with st.expander("Ver prévia do texto extraído (Relatório)"):
                st.text(text_relatorio[:1000]) # Mostra os primeiros 1000 caracteres

st.subheader("Geração do Relatório")

if st.button("Gerar Preview do Relatório"):
    with st.spinner("Desenhando o PDF..."):
        
        # 1. Gera o PDF na memória
        pdf_gerado = gerar_pdf_relatorio()
        
        # 2. Mostra o Preview na tela
        st.success("PDF gerado com sucesso! Confira o preview abaixo:")
        mostrar_preview_pdf(pdf_gerado)
        
        # 3. Libera o botão de Download (com nome dinâmico fictício por enquanto)
        prontuario_teste = "123456" 
        nome_arquivo = f"RelatorioDoTratamento_ID_{prontuario_teste}.pdf"
        
        st.download_button(
            label="📥 Baixar PDF Final",
            data=pdf_gerado,
            file_name=nome_arquivo,
            mime="application/pdf"
        )
