import streamlit as st
from moduls.carga import load_data_from_bucket
from moduls.inscripciones import show_inscriptions
from moduls.empresas import show_companies
from moduls.respuestas import show_responses
from google.oauth2 import service_account

# Configuración de las credenciales
credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Configuración de la página
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Nombres de los archivos en el bucket
bucket_name = "direccion"
blob_names = [
    "vt_inscripciones_empleo.csv",     # DataFrame 0
    "vt_empresas_adheridas.csv",        # DataFrame 1
    "VT_REPORTES_PPP_MAS26.csv",        # DataFrame 2
    "vt_inscripciones_empleo_e26empr.csv", # DataFrame 3
    "vt_respuestas.csv"                 # DataFrame 4
]

# Cargar datos desde el bucket
dfs, file_dates = load_data_from_bucket(blob_names, bucket_name, credentials)

# Crear las pestañas
tab1, tab2, tab3 = st.tabs(["Inscripciones", "Empresas", "Respuestas"])

with tab1:
    # Mostrar inscripciones
    show_inscriptions(dfs[0], file_dates[0])

with tab2:
    # Mostrar empresas
    show_companies(dfs[1], dfs[2], dfs[3])

with tab3:
    # Mostrar respuestas
    show_responses(dfs[4], file_dates[4])

