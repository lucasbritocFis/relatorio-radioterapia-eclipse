import os

# --- Diretório de assets (arquivos fixos no servidor) ---
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# --- Imagens e assinaturas fixas no servidor ---
LOGO_REDE_AMERICAS = os.path.join(ASSETS_DIR, "logo_rede_americas.png")
FAIXA_ROXA = os.path.join(ASSETS_DIR, "faixa_degrade_roxo.png")
PDF_MODELO_ALTA = os.path.join(ASSETS_DIR, "Modelo_RESUMO_ALTA_AMERICAS.pdf")

# Assinaturas
ASSINATURAS = {
    "Lucas": os.path.join(ASSETS_DIR, "ass_lucas.jpg"),
    "Guilherme": os.path.join(ASSETS_DIR, "ass_guilherme.jpg"),
}
