import os
import streamlit as st
from docxtpl import DocxTemplate
import google.generativeai as genai
import json
import re
import time
import base64
import requests

# ==============================================================
# CONFIGURACIÓN INICIAL
# ==============================================================
st.set_page_config(page_title="Generador de Actas - Clínica La Ermita", page_icon="🏥", layout="wide")

# Usamos st.secrets para Streamlit Cloud
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Falta la clave API en los Secrets")
    st.stop()

# Modelo estable para evitar errores 404
model = genai.GenerativeModel('models/gemini-1.5-flash')

TEMPLATES_DIR = "templates"

# ==============================================================
# CSS PERSONALIZADO (Estilo Ermita)
# ==============================================================
st.markdown("""
    <style>
        .app-header {
            display: flex; align-items: center; justify-content: center;
            gap: 15px; margin-bottom: 25px; background-color: #ffffff;
            padding: 15px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .app-header h1 { font-size: 2em; color: #1E3A8A; margin: 0; }
        .footer { text-align: center; color: #6B7280; font-size: 0.8em; margin-top: 50px; }
        .stButton button { background-color: #2563EB; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================
# FUNCIONES AUXILIARES
# ==============================================================

def normalizar_listas(data):
    """Asegura que las listas existan para que el Word no lance error."""
    claves = {
        "asistentes_reunion": ["nombreasistentereu", "cargoasistentereunion"],
        "temas_tratados": ["tema", "desarrollo"],
        "compromisos_r": ["compromiso", "responsable", "fechaejecucion"]
    }
    for clave, campos in claves.items():
        lista = data.get(clave.upper(), [])
        if not isinstance(lista, list): lista = []
        for item in lista:
            for campo in campos:
                item.setdefault(campo, "N/A")
        data[clave] = lista

def extract_info_with_gemini(text_to_process):
    prompt = f"""
    Analiza esta transcripción y devuelve SOLO un JSON válido para un acta de la Clínica La Ermita.
    Campos: FECHA (DD/MM/AAAA), CIUDAD, SEDE, OBJETIVO_DE_LA_REUNION.
    Listas:
    - ASISTENTES_REUNION: [{{nombreasistentereu, cargoasistentereunion}}]
    - TEMAS_TRATADOS: [{{tema, desarrollo}}]
    - COMPROMISOS_R: [{{compromiso, responsable, fechaejecucion}}]
    - DESARROLLO_DE_LA_REUNION_Y_CONCLUSIONES: Texto detallado.
    
    TEXTO: {text_to_process}
    """
    try:
        response = model.generate_content(prompt)
        # Extraer JSON puro entre llaves
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return None
    except Exception as e:
        st.error(f"Error IA: {e}")
        return None

# ==============================================================
# INTERFAZ PRINCIPAL
# ==============================================================

st.markdown('<div class="app-header"><h1>🏥 Generador de Actas Ermita</h1></div>', unsafe_allow_html=True)

# Manejo de Plantillas
if not os.path.exists(TEMPLATES_DIR): os.makedirs(TEMPLATES_DIR)
template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".docx")]

if not template_files:
    st.warning("⚠️ Sube tu plantilla .docx a la carpeta 'templates'")
    st.stop()

col_main, col_side = st.columns([2, 1])

with col_main:
    transcripcion = st.text_area("🗒️ Transcripción de la reunión", height=350)

with col_side:
    template_docx = st.selectbox("📂 Seleccionar Plantilla", template_files)
    elaborado = st.text_input("👤 Elaborado por")
    cargo = st.text_input("💼 Cargo")
    generar = st.button("📝 GENERAR ACTA")

if generar:
    if not transcripcion.strip():
        st.warning("⚠️ Pega el texto primero.")
    else:
        with st.spinner("Procesando con IA..."):
            extracted_data = extract_info_with_gemini(transcripcion)
            
            if extracted_data:
                # Inyectar datos manuales y normalizar
                extracted_data["ACTA_ELABORADA_POR"] = elaborado
                extracted_data["CARGO_ELA"] = cargo
                normalizar_listas(extracted_data)
                
                try:
                    doc = DocxTemplate(os.path.join(TEMPLATES_DIR, template_docx))
                    doc.render(extracted_data)
                    output_path = "acta_final.docx"
                    doc.save(output_path)
                    
                    st.success("✅ ¡Acta generada!")
                    with open(output_path, "rb") as f:
                        st.download_button("📥 Descargar Word", f, file_name=f"Acta_Ermita_{extracted_data.get('FECHA','AI')}.docx")
                except Exception as e:
                    st.error(f"Error al crear Word: {e}")
            else:
                st.error("No se pudo procesar el JSON. Intenta de nuevo.")

st.markdown("<div class='footer'>© 2026 Clínica La Ermita • Inteligencia Artificial aplicada</div>", unsafe_allow_html=True)
