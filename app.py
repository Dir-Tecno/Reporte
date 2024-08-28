import streamlit as st
from moduls.carga import load_data_from_bucket
from moduls.inscripciones import show_inscriptions
from moduls.empresas import show_companies
from google.oauth2 import service_account

# Configuración de las credenciales
credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Configuración de la página
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Nombres de los archivos en el bucket
bucket_name = "direccion"
blob_names = ["vt_inscripciones_empleo.csv", "vt_empresas_adheridas.csv", "VT_REPORTES_PPP_MAS26.csv", "vt_empresas_seleccionadas.csv"]
dfs, file_dates = load_data_from_bucket(blob_names, bucket_name, credentials)

# Crear las pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

with tab1:
    show_inscriptions(dfs[0], dfs[2],dfs[3], file_dates[0], file_dates[2],file_dates[3] )

with tab2:
    show_companies(dfs[1], file_dates[1])
