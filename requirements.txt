# Gerador de Relatórios de Radioterapia — Streamlit

## Estrutura do Projeto

```
streamlit_app/
├── app.py                  ← Entrada principal (Streamlit)
├── config.py               ← Caminhos dos assets no servidor
├── modelo.py               ← Dataclasses (DadosPaciente, DadosCabecalhoImagens)
├── extracao.py             ← Leitura de PDFs e extração do paciente
├── parsing.py              ← Regex, campos, QA, deslocamento
├── imagens.py              ← Extração e manipulação de imagens
├── desenho.py              ← Primitivas de desenho no canvas
├── pdf_relatorio.py        ← Montagem do PDF do relatório
├── pdf_imagens.py          ← Montagem do PDF das imagens
├── pdf_alta.py             ← Montagem do relatório de alta
├── requirements.txt        ← Dependências Python
├── packages.txt            ← Dependências do sistema (poppler)
├── assets/                 ← Arquivos fixos no servidor (NÃO fazer upload)
│   ├── logo_rede_americas.png
│   ├── faixa_degrade_roxo.png
│   ├── ass_lucas.jpg
│   ├── ass_guilherme.jpg
│   └── Modelo_RESUMO_ALTA_AMERICAS.pdf
└── README.md
```

## Como Configurar

### 1. Preparar os assets

Copie os seguintes arquivos para a pasta `assets/`:

| Arquivo original                      | Renomear para                        |
|---------------------------------------|--------------------------------------|
| `ass Lucas carimbada.jpg`             | `ass_lucas.jpg`                      |
| `ass Guilherme carimbada.jpg`         | `ass_guilherme.jpg`                  |
| `logo_rede_americas.png`              | (manter)                             |
| `faixa_degrade_roxo.png`              | (manter)                             |
| `Modelo_RESUMO_ALTA_AMERICAS.pdf`     | (manter)                             |

### 2. Subir para o GitHub

```bash
git init
git add .
git commit -m "Primeiro deploy"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

### 3. Deploy no Streamlit Community Cloud

1. Acesse https://share.streamlit.io
2. Clique em "New app"
3. Selecione o repositório e branch `main`
4. Main file path: `app.py`
5. Clique em "Deploy"

O `packages.txt` instala o Poppler automaticamente.

## Como Usar

1. Faça upload dos PDFs na sidebar:
   - PDF do Relatório (*REL.pdf)
   - PDF do CQ
   - PDF do DVH
   - 4 PDFs de imagens (AXI, COR, SAG, 3D)

2. Configure as opções:
   - Quem planejou (1ª assinatura)
   - Quem verificou (2ª assinatura)
   - Bólus: automático, sim ou não

3. Clique em "Gerar Relatórios"

4. Faça download dos 3 PDFs gerados
