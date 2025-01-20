import streamlit as st
import requests
from moduls.carga import load_data_from_gitlab
from moduls.inscripciones import show_inscriptions
from moduls.empresas import show_companies

def enviar_a_slack(comentario, valoracion):
    """
    Envía el feedback a Slack usando un webhook.
    """
    try:
        SLACK_WEBHOOK_URL = st.secrets["slack"]["webhook_url"]
        mensaje = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Nuevo Feedback del Dashboard",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Comentario:*\n{comentario}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Valoración:*\n{'⭐' * valoracion}"
                        }
                    ]
                }
            ]
        }
        response = requests.post(SLACK_WEBHOOK_URL, json=mensaje)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al enviar a Slack: {str(e)}")
        return False

# Configuración de la página
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Configuración de las credenciales
repo_id = 'agustinarraya10%2Farchivos'  # Reemplaza con el ID del repositorio
file_path = '*.parquet'  # Reemplaza con la ruta del archivo en el repositorio
branch = 'main'  # O la rama que desees
token = st.secrets["gitlab"]["token"]  # Usar token desde secrets

# Cargar datos desde GitLab
df, file_dates = load_data_from_gitlab(repo_id, file_path, branch, token)


if df is not None:
    # Crear las pestañas
    tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])
    
    with tab1:
        try:
            
            show_inscriptions(df[8], df[1], df[2], df[4], df[3], file_dates[7])
        except Exception as e:
            st.error(f"Error al mostrar inscripciones: {str(e)}")
    
    with tab2:
        try:
            show_companies(df[6], df[3])
        except Exception as e:
            st.error(f"Error al mostrar empresas: {str(e)}")
else:
    st.error("No se pudieron cargar los datos. Verifica el token y los permisos.")


