import streamlit as st
from moduls.carga import load_data_from_bucket
from moduls.inscripciones import show_inscriptions
from moduls.empresas import show_companies
#from moduls.respuestas import show_responses


# Configuración de las credenciales


# Configuración de la página
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Nombres de los archivos en el bucket
url = st.secrets['supabase']['url']
key = st.secrets['supabase']['key']
bucket_name = "empleo"

# Cargar datos desde el bucket
dfs, file_dates = load_data_from_bucket(bucket_name, url, key)


# Crear las pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

with tab1:
    # Mostrar inscripciones
    show_inscriptions(dfs[3], dfs[4], dfs[6], dfs[1], file_dates[2],dfs[0])

with tab2:
    # Mostrar empresas
    show_companies(dfs[2],dfs[0])


