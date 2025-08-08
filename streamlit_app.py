import streamlit as st
import requests
from datetime import datetime
import PyPDF2
import io

# === CONFIGURACIÓN DE API (OpenRouter) ===
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY") or st.sidebar.text_input(
    "🔑 Ingresa tu API Key de OpenRouter", 
    type="password",
    help="Puedes obtener una API Key gratuita en openrouter.ai"
)


HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://tuproyecto.com",
    "X-Title": "chatbot-explicador"
}

# === MODELOS DISPONIBLES ===
model_options = {
    "Qwen3": "qwen/qwen3-235b-a22b-07-25:free",
    "DeepSeek R1": "deepseek/deepseek-r1-0528:free",
    "Gemini 2.0": "google/gemini-2.0-flash-exp:free",
}

# === FUNCIÓN PARA LEER PDF ===
def leer_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    texto = ""
    for page in pdf_reader.pages:
        texto += page.extract_text() + "\n"
    return texto

# === FUNCIÓN PARA CONSULTAR OPENROUTER ===
def ask_openrouter(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return f"❌ Error: {response.text}"

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(
    page_title="Analista de Paper - Visión de Negocio",
    page_icon="📊",
    layout="wide"
)

# === SIDEBAR ===
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Selección de modelo
    MODEL = st.selectbox("🧠 Modelo AI", list(model_options.keys()), index=0)
    MODEL = model_options[MODEL]
    
    # Subir PDF
    uploaded_pdf = st.file_uploader("📄 Sube el paper en PDF", type=["pdf"])
    
    # Botón para cargar contexto
    if uploaded_pdf:
        pdf_text = leer_pdf(uploaded_pdf)
        st.success("✅ PDF cargado y listo para usar")
    else:
        pdf_text = None
        st.warning("⚠️ Sube un PDF para iniciar el análisis")

# === INICIALIZACIÓN DEL CHAT ===
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if pdf_text:
    if not st.session_state.chat_history:
        # Contexto inicial
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"""
            Eres un analista experto en negocios. Tu tarea es analizar el siguiente documento académico y responder
            exclusivamente sobre:
            - Métricas clave encontradas en el estudio
            - Insights relevantes para la toma de decisiones
            - Proyecciones de negocio basadas en los datos

            Lenguaje:
            - Explica todo en palabras simples
            - Evita jerga técnica
            - Usa ejemplos fáciles de entender para gerencia

            Documento base:
            {pdf_text}
            """
        })

# === INTERFAZ PRINCIPAL ===
st.title("📊 Analista de Paper para Gerencia")
st.caption("Sube un paper y haz preguntas sobre métricas, insights y proyecciones de negocio")

# Mostrar historial
for msg in st.session_state.chat_history:
    if msg["role"] == "system": 
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de chat
if OPENROUTER_API_KEY and pdf_text:
    if prompt := st.chat_input("✍️ Pregunta sobre métricas, insights o proyecciones..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("Analizando el documento..."):
            respuesta = ask_openrouter(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        st.rerun()
elif not pdf_text:
    st.info("📄 Por favor sube primero un PDF para comenzar.")
else:
    st.warning("⚠️ Ingresa tu API Key para comenzar.")
