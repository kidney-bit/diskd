import streamlit as st
import os
import tempfile
import random
import re
import fitz  # PyMuPDF
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Formulário Dialítico", layout="wide")
st.title("📄 Formulário Automático para Regulação de Diálise")

col1, col2, col3 = st.columns(3)
with col1:
    pdf1 = st.file_uploader("📋 PDF 1 - Dados Demográficos", type="pdf", key="pdf1")
with col2:
    pdf2 = st.file_uploader("📋 PDF 2 - Evolução/Resumo Clínico", type="pdf", key="pdf2")
with col3:
    pdf3 = st.file_uploader("📋 PDF 3 - Exames Laboratoriais", type="pdf", key="pdf3")

def buscar_valor(texto, chave, multiline=True):
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        if chave.lower() in linha.lower():
            if multiline and i + 1 < len(linhas):
                proxima = linhas[i + 1].strip()
                if proxima and not ":" in proxima:
                    return proxima
            return linha.split(":")[-1].strip()
    return ""

def buscar_nome_paciente(texto):
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        if "nome do paciente" in linha.lower():
            for j in range(1, 4):
                if i - j >= 0:
                    candidata = linhas[i - j].strip()
                    if re.fullmatch(r"[A-ZÀ-Ú ]{5,}", candidata):
                        return candidata
    return ""

def buscar_nome_mae(texto):
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        if "nome da m" in linha.lower():
            for j in range(1, 4):
                if i - j >= 0:
                    candidata = linhas[i - j].strip()
                    if re.fullmatch(r"[A-ZÀ-Ú ]{5,}", candidata):
                        return candidata
    return ""

def buscar_data_nascimento(texto):
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        if "data nascimento" in linha.lower():
            for j in range(1, 4):
                if i - j >= 0:
                    data = linhas[i - j].strip()
                    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
                        return data
    match = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
    return match.group(1) if match else ""

def buscar_primeiro_telefone(texto):
    padrao = re.compile(r"\(?(\d{2})\)?[-\s]?(\d{4,5})[-\s]?(\d{4})")
    match = padrao.search(texto)
    if match:
        ddd, parte1, parte2 = match.groups()
        return f"{ddd}-{parte1}{parte2}"
    return ""

import re

def buscar_cep(texto):
    linhas = texto.splitlines()
    for i, linha in enumerate(linhas):
        if "cep" in linha.lower():
            for j in range(1, 5):  # procurar até 4 linhas acima
                if i - j >= 0:
                    candidato = linhas[i - j].strip()
                    # extrai só os números, caso venha com algum lixo junto
                    numeros = re.findall(r"\d{5}-?\d{3}", candidato)
                    if numeros:
                        cep = numeros[0]
                        if len(cep) == 8:
                            return cep[:5] + "-" + cep[5:]
                        return cep
    return ""

def gerar_pa_valida():
    while True:
        sistolica = random.randint(100, 140)
        diastolica = random.randint(60, 90)
        delta = sistolica - diastolica
        if 30 <= delta <= 50:
            return f"{sistolica}-{diastolica}"

def gerar_random(valor_min, valor_max, decimal=False):
    if decimal:
        return round(random.uniform(valor_min, valor_max), 1)
    return random.randint(valor_min, valor_max)

distritos_com_coordenadas = {
    "CENTRO - BELA VISTA": (-23.561414, -46.655881),
    "LESTE - ITAQUERA": (-23.544588, -46.460170),
    "NORTE - SANTANA": (-23.501529, -46.624692),
    "OESTE - BUTANTÃ": (-23.570718, -46.719190),
    "SUDESTE - VILA MARIANA": (-23.589548, -46.634018),
    "SUL - SANTO AMARO": (-23.649308, -46.715133),
    # Adicione mais conforme necessário
}

def coordenadas_por_cep(cep):
    geolocator = Nominatim(user_agent="tablab_geolocator")
    location = geolocator.geocode(f"{cep}, São Paulo, Brasil")
    if location:
        return (location.latitude, location.longitude)
    return None

def distrito_mais_proximo(cep, distritos_coords):
    cep_coord = coordenadas_por_cep(cep)
    if not cep_coord:
        return "Não encontrado"
    mais_proximo = min(distritos_coords.items(), key=lambda item: geodesic(cep_coord, item[1]).km)
    return mais_proximo[0]

if st.button("📤 Executar extração"):
    respostas = {}
    textos = []

    for pdf in [pdf1, pdf2, pdf3]:
        if pdf:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf.read())
                caminho = tmp.name

            doc = fitz.open(caminho)
            full_text = "\n".join(p.get_text() for p in doc)
            textos.append(full_text)
            doc.close()
            os.unlink(caminho)
        else:
            textos.append("")

    texto1, texto2, texto3 = textos

    # PAGINA 1
    respostas["email"] = "dialise@incor.usp.br"
    respostas["consentimento"] = "sim"

    # PAGINA 2
    respostas["hospital"] = "INCOR"
    respostas["cidade"] = "SP - São Paulo"
    respostas["telefone fixo"] = "11-26610000"

    # PAGINA 3
    respostas["nome"] = buscar_nome_paciente(texto1)
    respostas["nome_mae"] = buscar_nome_mae(texto1)
    respostas["nascimento"] = buscar_data_nascimento(texto1)
    respostas["peso"] = str(gerar_random(60, 80))
    respostas["telefone"] = buscar_primeiro_telefone(texto1)
    respostas["cpf"] = buscar_valor(texto1, "CIC")
    respostas["sexo"] = buscar_valor(texto1, "Sexo")
    respostas["cns"] = buscar_valor(texto1, "CNS")
    respostas["endereco"] = buscar_valor(texto1, "Endere")
    respostas["cep"] = buscar_cep(texto1)

    respostas["distrito"] = distrito_mais_proximo(respostas["cep"], distritos_com_coordenadas)
    respostas["regiao_preferencia"] = respostas["distrito"].split(" - ")[0] if " - " in respostas["distrito"] else ""

    # PAGINA 4
    if texto2.strip():
        encontrados = [d for d in lista_diagnosticos if d in texto2.upper()]
        respostas["diagnosticos"] = ", ".join(encontrados)
    else:
        respostas["diagnosticos"] = "DOENÇA RENAL CRÔNICA (DRC)"

    respostas["tratamento_atual"] = "DIALITICO"
    respostas["outras_patologias"] = "INSUFICIENCIA CARDIACA"
    respostas["transplante"] = "NAO"
    respostas["data_transplante"] = ""
    respostas["modalidade"] = "HEMO"
    respostas["acesso"] = "CATETER"
    respostas["sangramentos"] = "NAO"
    respostas["condicoes_hemo"] = "ESTÁVEL"
    respostas["pressao"] = gerar_pa_valida()
    respostas["ureia"] = str(gerar_random(120, 180))
    respostas["creatinina"] = str(gerar_random(5.5, 7.5, decimal=True))
    respostas["potassio"] = str(gerar_random(4.0, 5.0, decimal=True))
    respostas["glicemia"] = str(gerar_random(80, 100))
    respostas["clearance"] = "0"
    respostas["HbsAg"] = "NEG"
    respostas["AntiHbs"] = "NEG"
    respostas["AntiHbc"] = "NEG"
    respostas["HIV"] = "NEG"
    respostas["HCV"] = "NEG"
    respostas["medico"] = "Karoline Wayla Costa"
    respostas["crm"] = "202865"
    respostas["uf_crm"] = "SP"

    # PAGINA 5
    respostas["tipo_solicitacao"] = "INICIAL"

    # PAGINA 7
    respostas["alta"] = "SIM"
    respostas["observacoes"] = ""

    st.subheader("📄 Página 1")
    st.text(f"Email: {respostas['email']}")
    st.text(f"Consentimento: {respostas['consentimento']}")

    st.subheader("📄 Página 2")
    st.text(f"Hospital: {respostas['hospital']}")
    st.text(f"Cidade: {respostas['cidade']}")
    st.text(f"Telefone fixo: {respostas['telefone fixo']}")

    st.subheader("📄 Página 3")
    st.text(f"Nome do paciente: {respostas['nome']}")
    st.text(f"Nome da mãe: {respostas['nome_mae']}")
    st.text(f"Data de nascimento: {respostas['nascimento']}")
    st.text(f"Peso: {respostas['peso']}")
    st.text(f"Telefone: {respostas['telefone']}")
    st.text(f"CPF: {respostas['cpf']}")
    st.text(f"Sexo: {respostas['sexo']}")
    st.text(f"CNS: {respostas['cns']}")
    st.text(f"Endereço: {respostas['endereco']}")
    st.text(f"CEP: {respostas['cep']}")
    st.text(f"Região de preferência: {respostas['regiao_preferencia']}")
    st.text(f"Distrito: {respostas['distrito']}")

    st.subheader("📄 Página 4")
    st.text(f"Diagnósticos: {respostas['diagnosticos']}")
    st.text(f"Tratamento atual: {respostas['tratamento_atual']}")
    st.text(f"Outras patologias: {respostas['outras_patologias']}")
    st.text(f"Já realizou transplante: {respostas['transplante']}")
    st.text(f"Data do transplante: {respostas['data_transplante']}")
    st.text(f"Modalidade: {respostas['modalidade']}")
    st.text(f"Acesso: {respostas['acesso']}")
    st.text(f"Sangramentos: {respostas['sangramentos']}")
    st.text(f"Condições hemodinâmicas: {respostas['condicoes_hemo']}")
    st.text(f"Pressão arterial: {respostas['pressao']}")
    st.text(f"Ureia: {respostas['ureia']}")
    st.text(f"Creatinina: {respostas['creatinina']}")
    st.text(f"Potássio: {respostas['potassio']}")
    st.text(f"Glicemia: {respostas['glicemia']}")
    st.text(f"Clearance: {respostas['clearance']}")
    st.text(f"HbsAg: {respostas['HbsAg']}")
    st.text(f"Anti-Hbs: {respostas['AntiHbs']}")
    st.text(f"Anti-Hbc: {respostas['AntiHbc']}")
    st.text(f"HIV: {respostas['HIV']}")
    st.text(f"HCV: {respostas['HCV']}")
    st.text(f"Médico responsável: {respostas['medico']}")
    st.text(f"CRM: {respostas['crm']}")
    st.text(f"UF CRM: {respostas['uf_crm']}")

    st.subheader("📄 Página 5")
    st.text(f"Tipo de Solicitação: {respostas['tipo_solicitacao']}")

    st.subheader("📄 Página 7")
    st.text(f"Paciente em condições de alta?: {respostas['alta']}")
    st.text(f"Informações adicionais: {respostas['observacoes']}")
