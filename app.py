import streamlit as st
from docxtpl import DocxTemplate
import google.generativeai as genai
import json
import re
import os

# 1. Configuración de la página
st.set_page_config(page_title="Generador de Actas - Clínica La Ermita", page_icon="🏥")

# 2. Conexión segura con Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Falta la clave API en los Secrets de Streamlit.")
    st.stop()

# Usamos el nombre de modelo más estable para evitar errores 404
model = genai.GenerativeModel('models/gemini-1.5-flash')

def extract_info(text):
    """Extrae datos de la transcripción y los limpia para asegurar un JSON válido."""
    prompt = f"""
    Analiza esta transcripción de reunión de la Clínica La Ermita y extrae los datos.
    Debes devolver estrictamente un objeto JSON con estas llaves exactas:
    FECHA, CIUDAD, SEDE, OBJETIVO_DE_LA_REUNION, 
    ASISTENTES_REUNION (lista con nombreasistentereu y cargoasistentereunion),
    TEMAS_TRATADOS (lista con tema y desarrollo),
    COMPROMISOS_R (lista con compromiso, responsable y fechaejecucion).
    
    TEXTO: {text}
    """
    
    response = model.generate_content(prompt)
    texto_respuesta = response.text
    
    # Buscamos solo el contenido entre llaves { } para ignorar texto extra de la IA
    match = re.search(r'\{.*\}', texto_respuesta, re.DOTALL)
    if match:
        return json.loads(match.group())
    else:
        raise Exception("La IA no generó un formato de datos reconocido.")

# 3. Interfaz de Usuario (UI)
st.title("🏥 Asistente de Actas - Clínica La Ermita")
st.markdown("---")

transcripcion = st.text_area("🗒️ Pega aquí la transcripción de la reunión:", height=350)

if st.button("✨ Procesar y Generar Word"):
    if not transcripcion.strip():
        st.warning("Por favor, introduce el texto de la reunión.")
    else:
        with st.spinner("La IA está redactando el acta..."):
            try:
                # Extraer datos con la IA
                datos = extract_info(transcripcion)
                
                # Cargar la plantilla Word
                template_path = "templates/CLINICA_LA_ERMITA.docx"
                
                if not os.path.exists(template_path):
                    st.error(f"No se encontró la plantilla en: {template_path}")
                else:
                    doc = DocxTemplate(template_path)
                    
                    # Rellenar la plantilla con los datos
                    doc.render(datos)
                    
                    # Guardar temporalmente
                    archivo_salida = "Acta_Generada_Ermita.docx"
                    doc.save(archivo_salida)
                    
                    # Botón de descarga
                    with open(archivo_salida, "rb") as f:
                        st.success("✅ ¡Acta generada con éxito!")
                        st.download_button(
                            label="📥 Descargar Acta en Word",
                            data=f,
                            file_name="Acta_Clinica_La_Ermita.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
                st.info("Tip: Intenta con un texto un poco más corto o verifica tu conexión.")
