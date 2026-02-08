import os
import streamlit as st
from docxtpl import DocxTemplate
import google.generativeai as genai
import json

# Configuración de la página
st.set_page_config(page_title="Generador de Actas - Clínica La Ermita", page_icon="🏥")

# Conectar con la IA (usando los Secrets de Streamlit que configuraremos después)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Falta la clave API en los Secrets")

model = genai.GenerativeModel('gemini-2.0-flash')

def extract_info(text):
    prompt = f"""
    Analiza esta transcripción de reunión de la Clínica La Ermita y extrae:
    FECHA, CIUDAD, SEDE, OBJETIVO_DE_LA_REUNION,
    ASISTENTES_REUNION (lista con nombreasistentereu y cargoasistentereunion),
    TEMAS_TRATADOS (lista con tema y desarrollo),
    COMPROMISOS_R (lista con compromiso, responsable y fechaejecucion).
    Devuelve SOLO un JSON válido.
    TEXTO: {text}
    """
    response = model.generate_content(prompt)
    # Limpieza básica de la respuesta de la IA
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json)

st.title("🏥 Generador de Actas - Clínica La Ermita")
st.info("Pega la transcripción y la IA redactará el acta automáticamente.")

transcripcion = st.text_area("🗒️ Transcripción de la reunión", height=300)

if st.button("✨ Generar Acta en Word"):
    if not transcripcion:
        st.warning("Por favor, pega un texto primero.")
    else:
        with st.spinner("La IA está procesando la información..."):
            try:
                datos = extract_info(transcripcion)
                
                # Cargar la plantilla (debe estar en la carpeta 'templates')
                doc = DocxTemplate("templates/CLINICA_LA_ERMITA.docx")
                doc.render(datos)
                
                output_name = "acta_generada.docx"
                doc.save(output_name)
                
                with open(output_name, "rb") as f:
                    st.download_button("📥 Descargar Acta Lista", f, file_name=f"Acta_Ermita.docx")
                st.success("¡Acta procesada con éxito!")
            except Exception as e:
                st.error(f"Hubo un error: {e}")
