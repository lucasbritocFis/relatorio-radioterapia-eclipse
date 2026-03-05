import re
from typing import List, Tuple

from modelo import DadosCabecalhoImagens


# --- Constantes de parsing ---

TAMANHO_BLOCO_SETUP = 18
TAMANHO_BLOCO_TRATAMENTO = 23

SUBSTITUICOES_LIMPEZA = {
    "cm": "", "UM": "", "cGy": "",
    "Y1:": "", "Y2:": "", "X1:": "", "X2:": "",
    "SH": "Horário", "SAH": "Anti-Horário",
}

RENOMEAR_COLUNAS = {
    "Tam. Campo": "X x Y (cm x cm)",
    "Y1": "Y1 (cm)",
    "Y2": "Y2 (cm)",
    "X1": "X1 (cm)",
    "X2": "X2 (cm)",
    "Rot Gantry": "Gantry",
    "Sentido de Rot": "Sentido",
    "Rot Colimador": "Colimador",
    "Isocentro X": "Isocentro X (cm)",
    "Isocentro Y": "Isocentro Y (cm)",
    "Isocentro Z": "Isocentro Z (cm)",
    "Rot Mesa": "Mesa",
    "(Pto Ref)Dose": "(Pto Ref)Dose (cGy)",
    "SSD": "SSD (cm)",
    "MU": "UM",
}

REGEX_CAMPO = re.compile(r'Campo (\d+)')
REGEX_AREA_GAMA = re.compile(r'Área gama < 1,0\s+(\d+\.\d+) %')
REGEX_AREA_GAMA_DUPLA = re.compile(r'Área gama < 1,0\s+(\d+\.\d+) %\s+(\d+\.\d+) %')
REGEX_RESULTADO = re.compile(r'Resultado da análise\s*[:.-]?\s*(.*?(?=\n|$))', re.IGNORECASE)
REGEX_GAMA_DTA = re.compile(r'Gama DTA\s*:\s*(\d+\.\d+)\s*mm\s*Tol\.\s*:\s*(\d+\.\d+) %')

MARCADOR_INICIO_DESLOCAMENTO = "Deslocamento da mesa da posição de setup de referência:"
MARCADORES_FIM_DESLOCAMENTO = ["Dentro", "Fora", "-"]

PADRAO_DATA_EN = re.compile(
    r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),'
    r'\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)'
)

CRITERIOS_FILTRO_CABECALHO = {
    "dose":         "a em",
    "cgy":          " cGy",
    "ultima_mod":   "Última",
    "hospital":     "ONCOBARRA",
    "grade":        "mm",
    "normalizacao":  "%",
    "impresso_por": "Impresso",
    "plano_curso":  "Campos no",
}


# --- Utilitários ---

def encontrar_indice(linhas: list, texto_busca: str) -> int | None:
    for i, item in enumerate(linhas):
        if texto_busca in item:
            return i
    return None


def extrair_entre_marcadores(linhas: list, inicio: str, fim: str) -> list:
    try:
        idx_inicio = linhas.index(inicio)
        idx_fim = linhas.index(fim) + 1
    except ValueError as e:
        raise ValueError(f"Marcador não encontrado: {e}")
    return linhas[idx_inicio:idx_fim]


def _obter_seguro(lista: list, indice: int, padrao: str = "-") -> str:
    if isinstance(lista, list) and len(lista) > indice:
        return str(lista[indice])
    return padrao


def _filtrar_linhas(linhas: list, criterios: dict) -> dict:
    return {
        nome: [l for l in linhas if chave in l]
        for nome, chave in criterios.items()
    }


# --- Cabeçalho dos campos ---

def extrair_cabecalho_campos(linhas: list) -> list:
    return extrair_entre_marcadores(linhas, "Campo", "MU")


def limpar_nome_coluna(nome: str) -> str:
    for original, novo in RENOMEAR_COLUNAS.items():
        nome = nome.replace(original, novo)
    return nome.strip()


# --- Separação e limpeza de campos ---

def separar_campos(lista: list) -> Tuple[list, list]:
    campos_setup = []
    campos_tratamento = []

    for i, item in enumerate(lista):
        if item == "Campo de setup":
            inicio = max(i - TAMANHO_BLOCO_SETUP + 1, 0)
            campos_setup.append(lista[inicio:i + 1])
        elif item.endswith("UM"):
            inicio = max(i - TAMANHO_BLOCO_TRATAMENTO + 1, 0)
            campos_tratamento.append(lista[inicio:i + 1])

    return campos_setup, campos_tratamento


def _limpar_valor(valor: str) -> str:
    for original, novo in SUBSTITUICOES_LIMPEZA.items():
        valor = valor.replace(original, novo)
    return valor.strip()


def limpar_campos(campos: list) -> list:
    resultado = []
    for campo in campos:
        campo_limpo = [_limpar_valor(item) for item in campo]
        campo_limpo = [item for item in campo_limpo if item != "-"]
        resultado.append(campo_limpo)
    return resultado


# --- Detecção de bólus ---

def detectar_bolus(campos_limpos: list) -> bool:
    return any(
        "bólu" in item.lower()
        for campo in campos_limpos
        for item in campo
    )


# --- Controle de qualidade ---

def extrair_dados_qa(texto_qa: str) -> list:
    return list(zip(
        REGEX_CAMPO.findall(texto_qa),
        REGEX_GAMA_DTA.findall(texto_qa),
        REGEX_AREA_GAMA.findall(texto_qa),
        REGEX_AREA_GAMA_DUPLA.findall(texto_qa),
        REGEX_RESULTADO.findall(texto_qa),
    ))


# --- Deslocamento da mesa ---

def extrair_deslocamento(linhas: list) -> list:
    idx_inicio = encontrar_indice(linhas, MARCADOR_INICIO_DESLOCAMENTO)
    if idx_inicio is None:
        raise ValueError(f"Marcador de início não encontrado: {MARCADOR_INICIO_DESLOCAMENTO}")

    idx_fim = None
    for marcador in MARCADORES_FIM_DESLOCAMENTO:
        idx_fim = encontrar_indice(linhas, marcador)
        if idx_fim is not None:
            idx_fim += 1
            break

    if idx_fim is None:
        raise ValueError(f"Nenhum marcador de fim encontrado: {MARCADORES_FIM_DESLOCAMENTO}")

    trecho = linhas[idx_inicio:idx_fim]
    trecho[0] = trecho[0].upper()
    return trecho


# --- Cabeçalho das imagens ---

def extrair_cabecalho_imagens(texto_pdf_imagens: str) -> DadosCabecalhoImagens:
    linhas = texto_pdf_imagens.splitlines()

    nome_paciente_img = linhas[3] if len(linhas) > 3 else "-"

    idx_inicio = encontrar_indice(linhas, "Nome do paciente:")
    idx_fim = encontrar_indice(linhas, "ID do campo")
    if idx_inicio is None or idx_fim is None:
        raise ValueError("Marcadores do cabeçalho de imagens não encontrados.")
    cabecalho = linhas[idx_inicio:idx_fim]

    filtrado = _filtrar_linhas(cabecalho, CRITERIOS_FILTRO_CABECALHO)

    plano_curso_texto = _obter_seguro(filtrado["plano_curso"], 0)
    nomes = re.findall(r"'(.*?)'", plano_curso_texto)
    plano = nomes[0] if len(nomes) > 0 else "-"
    curso = nomes[1] if len(nomes) > 1 else "-"

    idx_orient = encontrar_indice(cabecalho, "Fator de escala")
    idx_fim_orient = encontrar_indice(cabecalho, "Compensação")
    if idx_orient is not None and idx_fim_orient is not None:
        orientacao_linhas = cabecalho[idx_orient + 1 : idx_fim_orient]
        orientacao = orientacao_linhas[0] if orientacao_linhas else "-"
    else:
        orientacao = "-"

    idx_norm = encontrar_indice(cabecalho, "Valor de normalização do plano:")
    imagem = cabecalho[idx_norm - 1] if idx_norm and idx_norm > 0 else "-"

    doses_rotulos = filtrado.get("dose", [])
    coluna_doses = [
        (_obter_seguro(doses_rotulos, 0), _obter_seguro(cabecalho, 34)),
        (_obter_seguro(doses_rotulos, 1), _obter_seguro(cabecalho, 35)),
        (_obter_seguro(doses_rotulos, 2), _obter_seguro(cabecalho, 36)),
    ]

    linhas_com_data = [l for l in cabecalho if PADRAO_DATA_EN.search(l)]
    rodape_ultima_mod = linhas_com_data[1] if len(linhas_com_data) > 1 else "-"

    idx_ultimo_setup = None
    idx_prox_nome = len(linhas)
    for i, val in enumerate(linhas):
        if val == "Campo de setup":
            idx_ultimo_setup = i
    if idx_ultimo_setup is not None:
        for i in range(idx_ultimo_setup + 1, len(linhas)):
            if linhas[i] == "Nome do paciente:":
                idx_prox_nome = i
                break
    campos_img = linhas[idx_ultimo_setup + 1 : idx_prox_nome] if idx_ultimo_setup else []
    tecnicas = [item for item in campos_img if "-I" in item]

    return DadosCabecalhoImagens(
        hospital=_obter_seguro(filtrado.get("hospital", []), 0),
        curso=curso,
        plano=plano,
        orientacao=orientacao,
        imagem=imagem,
        normalizacao=_obter_seguro(filtrado.get("normalizacao", []), 1),
        grade_calculo=_obter_seguro(filtrado.get("grade", []), 0),
        coluna_doses=coluna_doses,
        plano_curso_texto=plano_curso_texto,
        nome_paciente_img=nome_paciente_img,
        rodape_impresso_por=_obter_seguro(filtrado.get("impresso_por", []), 0),
        rodape_ultima_mod=rodape_ultima_mod,
        tecnicas_campo=tecnicas,
    )
