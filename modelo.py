from dataclasses import dataclass


@dataclass
class DadosPaciente:
    nome: str
    nome_completo: str
    prontuario: str
    data_nascimento: str
    radio_oncologista: str
    curso_plano: str
    tomografia: str
    dose_prescricao: str
    curva_prescricao: str
    cabecalho_relatorio: str


@dataclass
class DadosCabecalhoImagens:
    hospital: str
    curso: str
    plano: str
    orientacao: str
    imagem: str
    normalizacao: str
    grade_calculo: str
    coluna_doses: list
    plano_curso_texto: str
    nome_paciente_img: str
    rodape_impresso_por: str
    rodape_ultima_mod: str
    tecnicas_campo: list
