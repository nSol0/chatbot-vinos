import streamlit as st
import requests
import joblib
import numpy as np

# === CONFIGURACIÓN DE API (OpenRouter) ===
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY") or st.sidebar.text_input(
    "🔑 Ingresa tu API Key de OpenRouter", 
    type="password",
    help="Puedes obtener una API Key gratuita en openrouter.ai"
)

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://tuproyecto.com",
    "X-Title": "chatbot-modelos"
}

# === MODELOS DISPONIBLES ===
model_options = {
    "Qwen3": "qwen/qwen3-coder:free",
    "DeepSeek R1": "deepseek/deepseek-r1-0528:free",
    "Gemini 2.0": "google/gemini-2.0-flash-exp:free",
}

# === FUNCIONES AUXILIARES ===
def describir_modelo(path_modelo, nombre_modelo):
    modelo = joblib.load(path_modelo)
    
    # Asumimos pipeline con scaler y modelo
    scaler = modelo.named_steps.get("scaler", None)
    modelo_reg = [v for k, v in modelo.named_steps.items() if k != "scaler"][0]
    
    # Extraer hiperparámetros
    hiperparams = modelo_reg.get_params()
    
    # Coeficientes
    if hasattr(modelo_reg, "coef_"):
        importancias = dict(zip(modelo.feature_names_in_, modelo_reg.coef_))
    else:
        importancias = {}
    
    descripcion = f"""
    Modelo: {nombre_modelo}
    Tipo: {modelo_reg.__class__.__name__}
    Scaler: {type(scaler).__name__ if scaler else 'Ninguno'}
    Hiperparámetros: {hiperparams}
    Importancia de variables (coeficientes): {importancias}
    """
    return descripcion

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
    page_title="Wine Advisor Bot",
    page_icon="🍷",
    layout="wide"
)

# === SIDEBAR ===
with st.sidebar:
    st.title("⚙️ Configuración")
    
    MODEL = st.selectbox("🧠 Modelo AI", list(model_options.keys()), index=0)
    MODEL = model_options[MODEL]
    
    # Cargar modelos desde archivos locales
    try:
        contexto_modelo_dole = describir_modelo("mejor_modelo.pkl", "Vino Rojo")
        contexto_modelo_white = describir_modelo("mejor_modelo_white.pkl", "Vino Blanco")
        st.success("✅ Modelos cargados correctamente")
    except Exception as e:
        contexto_modelo_dole = ""
        contexto_modelo_white = ""
        st.error(f"❌ Error al cargar modelos: {e}")

# === INICIALIZACIÓN DEL CHAT ===
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if contexto_modelo_dole and contexto_modelo_white:
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"""
            Eres un analista de negocios especializado en interpretar resultados de estudios y modelos.
            Tu función es conversar de forma clara y accesible para la gerencia, sin usar jerga técnica.

            Contexto:
            Dispones de la información de dos modelos de regresión, incluyendo métricas,
            importancia de variables y configuraciones clave.

            Información disponible:
            {contexto_modelo_dole}

            {contexto_modelo_white}

            Instrucciones:
            - Explica las métricas en términos que cualquier persona de gerencia pueda entender.
            - Extrae insights relevantes que puedan ayudar en la toma de decisiones.
            - Ofrece proyecciones de negocio basadas en los datos presentados.
            - Evita explicaciones técnicas sobre machine learning o programación.
            - Usa ejemplos prácticos y cercanos al contexto empresarial.
            - Mantén un tono profesional pero fácil de comprender.
            - No hagas referencia a que recibiste información previamente; responde como si la tuvieras desde el inicio.
            """
        })



# === INTERFAZ PRINCIPAL ===
st.title("🍷 Wine Advisor Bot")
st.caption("Haz preguntas sobre métricas, insights y proyecciones de negocio.")

# Mostrar historial
for msg in st.session_state.chat_history:
    if msg["role"] == "system": 
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de chat
if OPENROUTER_API_KEY and contexto_modelo_dole and contexto_modelo_white:
    if prompt := st.chat_input("✍️ Pregunta sobre los modelos..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("Analizando..."):
            respuesta = ask_openrouter(st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        st.rerun()
else:
    st.info("📄 No se han cargado los modelos o falta API Key.")
