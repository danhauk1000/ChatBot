import streamlit as st
import google.generativeai as genai
import os
import json
from PIL import Image
import io

# --- Configuration ---
st.set_page_config(page_title="Clara - Assistente Farmacêutica", layout="wide")

# Initialize session state
if "catalog" not in st.session_state:
    st.session_state.catalog = "Dipirona 500mg - R$ 5,00\nParacetamol 750mg - R$ 8,50\nIbuprofeno 600mg - R$ 12,00"

if "settings" not in st.session_state:
    st.session_state.settings = {
        "name": "Farmácia Central",
        "address": "Rua Principal, 123",
        "phone": "(11) 99999-9999",
        "openingHours": "08:00 - 20:00"
    }

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Gemini API Setup ---
# In Streamlit, you should set GEMINI_API_KEY in your secrets or environment
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Por favor, configure a variável de ambiente GEMINI_API_KEY.")

def get_clara_response(user_input, history):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    system_instruction = f"""
    Você é a Clara, uma assistente virtual de atendimento para a farmácia {st.session_state.settings['name']}.
    Seu objetivo é ser prestativa, educada e eficiente.

    INFORMAÇÕES DA FARMÁCIA:
    - Endereço: {st.session_state.settings['address']}
    - Telefone: {st.session_state.settings['phone']}
    - Horário: {st.session_state.settings['openingHours']}

    CATÁLOGO DE PRODUTOS E PREÇOS:
    {st.session_state.catalog}

    REGRAS CRÍTICAS:
    1. Use APENAS os preços listados no catálogo acima.
    2. Se um produto não estiver no catálogo, informe educadamente que não temos no momento ou peça para o cliente consultar um atendente humano.
    3. NUNCA invente preços ou descontos que não estejam documentados.
    4. Mantenha um tom profissional e acolhedor.
    5. Responda sempre em Português do Brasil.
    """
    
    # Format history for Gemini
    chat = model.start_chat(history=[])
    # We'll simulate the system instruction by prepending it or using the model's system_instruction feature if available
    # For simplicity in this script, we'll use a single prompt with context
    
    full_prompt = f"{system_instruction}\n\nHistórico da conversa:\n"
    for msg in history:
        full_prompt += f"{msg['role']}: {msg['content']}\n"
    full_prompt += f"user: {user_input}\nclara:"
    
    response = model.generate_content(full_prompt)
    return response.text

def extract_from_file(uploaded_file):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if uploaded_file.type.startswith('image'):
        image = Image.open(uploaded_file)
        prompt = "Extraia todos os nomes de produtos e seus respectivos preços desta imagem. Formate como uma lista simples: 'Produto - R$ Preço'. Retorne apenas a lista."
        response = model.generate_content([prompt, image])
    else:
        # For PDF/Text, read as string
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        prompt = f"Extraia produtos e preços deste texto e formate como 'Produto - R$ Preço':\n\n{content}"
        response = model.generate_content(prompt)
        
    return response.text

# --- UI Layout ---
st.title("💊 Clara - Assistente Farmacêutica")

tabs = st.tabs(["💬 Chat", "📋 Catálogo", "⚙️ Configurações"])

# --- Tab 1: Chat ---
with tabs[0]:
    st.subheader(f"Atendimento: {st.session_state.settings['name']}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Clara está pensando..."):
                response = get_clara_response(prompt, st.session_state.messages[:-1])
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# --- Tab 2: Catalog ---
with tabs[1]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Catálogo Atual")
        new_catalog = st.text_area("Edite seu catálogo (Produto - R$ Preço)", 
                                  value=st.session_state.catalog, 
                                  height=400)
        if st.button("Salvar Catálogo"):
            st.session_state.catalog = new_catalog
            st.success("Catálogo atualizado!")

    with col2:
        st.subheader("Importar via IA")
        st.write("Suba uma foto ou arquivo para extrair dados.")
        uploaded_file = st.file_uploader("Escolha um arquivo", type=["png", "jpg", "jpeg", "pdf", "txt", "csv"])
        
        if uploaded_file is not None:
            if st.button("Extrair com IA"):
                with st.spinner("Analisando arquivo..."):
                    extracted_text = extract_from_file(uploaded_file)
                    st.text_area("Resultado da Extração (Copie para o catálogo)", value=extracted_text, height=300)
                    st.info("Revise o texto acima e adicione manualmente ao seu catálogo à esquerda.")

# --- Tab 3: Settings ---
with tabs[2]:
    st.subheader("Configurações da Farmácia")
    with st.form("settings_form"):
        name = st.text_input("Nome da Farmácia", value=st.session_state.settings['name'])
        address = st.text_input("Endereço", value=st.session_state.settings['address'])
        phone = st.text_input("Telefone", value=st.session_state.settings['phone'])
        hours = st.text_input("Horário de Funcionamento", value=st.session_state.settings['openingHours'])
        
        if st.form_submit_button("Salvar Configurações"):
            st.session_state.settings = {
                "name": name,
                "address": address,
                "phone": phone,
                "openingHours": hours
            }
            st.success("Configurações salvas!")

st.sidebar.markdown("---")
st.sidebar.info("Este é um protótipo da Clara rodando em Streamlit. Certifique-se de configurar sua chave do Gemini nas variáveis de ambiente.")
