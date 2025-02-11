import streamlit as st
from dotenv import load_dotenv
import os

# Import namespaces
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient
from azure.ai.language.conversations import ConversationAnalysisClient

# Cargar las variables de entorno
load_dotenv()
ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
ai_key = os.getenv('AI_SERVICE_KEY')
ai_project_name = os.getenv('QA_PROJECT_NAME')
ai_deployment_name = os.getenv('QA_DEPLOYMENT_NAME')

# Crear clientes usando endpoint y key
credential = AzureKeyCredential(ai_key)
qa_client = QuestionAnsweringClient(endpoint=ai_endpoint, credential=credential)
conversation_client = ConversationAnalysisClient(endpoint=ai_endpoint, credential=credential)

# Función para obtener respuestas
def get_answer(question):
    response = qa_client.get_answers(
        question=question,
        project_name=ai_project_name,
        deployment_name=ai_deployment_name
    )
    return response.answers


# Función para analizar la intención de la pregunta
def analyze_intent(query):
    cls_project = 'Restaurant'
    deployment_slot = 'production'
    
    result = conversation_client.analyze_conversation(
        task={
            "kind": "Conversation",
            "analysisInput": {
                "conversationItem": {
                    "participantId": "1",
                    "id": "1",
                    "modality": "text",
                    "language": "es",
                    "text": query
                },
                "isLoggingEnabled": False
            },
            "parameters": {
                "projectName": cls_project,
                "deploymentName": deployment_slot,
                "verbose": True
            }
        }
    )
    
    top_intent = result["result"]["prediction"]["topIntent"]
    confidence_score = result["result"]["prediction"]["intents"][0]["confidenceScore"]
    entities = result["result"]["prediction"]["entities"]
    return top_intent, confidence_score, entities


# Configurar la aplicación de Streamlit
st.title("Chatbot de Restaurante Andy 🍕🍜")
st.write("""Esto es un chatbot para un restaurante de comida asiática y española. Si tiene alguna consulta, no dudes en preguntar. 🍣🥗     
    **Ejemplos de preguntas:**   
         

Pregunta 1:
         
    - ¿Ofrecen servicio de entrega a domicilio?   
         
Pregunta 2:  
          
    - ¿Ofrecen opciones para personas con alergias alimentarias? 

Pregunta 3:   
           
    - ¿Se puede hacer reservas después de las 4pm?   
         
Pregunta 4:  
          
    - ¿Hay reservas para cumpleaños con grupos grandes?  
         
Pregunta 5:   
         
    - ¿Dónde puedo solicitar una hoja de reclamaciones? 
    """)


# Historial de conversación
if 'history' not in st.session_state:
    st.session_state.history = []


# Controlar el input de texto usando st.session_state
if 'user_question' not in st.session_state:
    st.session_state.user_question = ""  # Inicializar la pregunta


# Entrada de usuario (usando el componente chat_input)
user_question = st.chat_input("Pregunta", key="chat_input")

# Procesar la pregunta del usuario
if user_question:
    if user_question.strip():  # Solo si la pregunta no está vacía
        # Obtener la respuesta del chatbot
        answers = get_answer(user_question)
        
        # Analizar la intención del usuario
        top_intent, confidence_score, entities = analyze_intent(user_question)
        
        # Agregar al historial
        st.session_state.history.append((user_question, answers, top_intent, confidence_score, entities))

# Mostrar historial de conversación
for i, (question, answers, top_intent, confidence_score, entities) in enumerate(st.session_state.history):
    st.write(f"**Pregunta {i+1}:** {question}")
    
    for answer in answers:
        st.write(f"- **Respuesta:** {answer.answer}")
        st.write(f"  **Confianza de respuesta:** {answer.confidence * 100:.2f}%")  # Para mostrar la confianza de la respuesta
        # st.write(f"  **Fuente:** {answer.source}")  # Para mostrar la fuente de la respuesta
    
    st.write(f"**Intención:** {top_intent}")
    st.write(f"**Confianza en la intención:** {confidence_score * 100:.2f}%")
    
    # Concatenar toda la información en una sola línea
    response_summary = (
        f"**Intención:** {top_intent} | "
        f"**Confianza en la intención:** {confidence_score * 100:.2f}% | "
    )

    # Si no hay entidades, agregar el mensaje correspondiente
    if not entities:
        response_summary += "No se encontraron entidades."
    else:
        # Imprimir la estructura completa de entidades para depuración
        # st.write(f"Entidades: {entities}")

        # Si hay entidades, mostrar los tipos de entidad
        entity_types = set()

        for entity in entities:
            entity_types.add(entity.get('category', 'No disponible'))
            # entity_types.add(entity.get('entity', 'No disponible')) # Para mostrar el nombre de la entidad
            # entity_types.add(entity.get('confidenceScore', 'No disponible')) # Para mostrar la confianza en la entidad
        response_summary += f"**Tipos de entidad:** {', '.join(entity_types)}"

    # Mostrar el resumen
    st.write(response_summary)

# Botón para borrar el historial
if st.button("Borrar historial"):
    st.session_state.history = []  # Borra el historial
    st.rerun()  # Fuerza la actualización de la interfaz