import json 
import geopandas as gpd
import streamlit as st
from moduls.carga import load_data_from_bucket, download_geojson_from_bucket
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
    "vt_inscripciones_empleo.txt",     
    "vt_empresas_adheridas.txt",        
    "vt_reportes_ppp_mas26.txt",        
    "vt_inscripciones_empleo_e26empr.txt", 
    "vt_respuestas.txt",                 
    "departamentos_poblacion.csv"        
]

# Cargar datos desde el bucket
dfs, file_dates = load_data_from_bucket(blob_names, bucket_name, credentials)

# Descargar el archivo GeoJSON
geojson_bytes = download_geojson_from_bucket('capa_departamentos_2010.geojson', bucket_name, credentials)

# Verificar si geojson_bytes es de tipo bytes y decodificar solo si es necesario
if isinstance(geojson_bytes, bytes):
    geojson_dict = json.loads(geojson_bytes.decode('utf-8'))
else:
    geojson_dict = geojson_bytes  # Ya es un dict

# Crear un GeoDataFrame desde las características del GeoJSON
gdf = gpd.GeoDataFrame.from_features(geojson_dict['features'])

# Verificar y asignar el CRS original si es necesario
if gdf.crs is None or gdf.crs.to_string() != 'EPSG:22174':
    gdf = gdf.set_crs(epsg=22174)  # Asegúrate de que este sea el CRS correcto

# Convertir a WGS 84 para la visualización (EPSG:4326)
gdf = gdf.to_crs(epsg=4326)

# Convertir el GeoDataFrame a GeoJSON para la visualización
geojson_data = gdf.__geo_interface__

# Crear las pestañas
tab1, tab2, tab3 = st.tabs(["Inscripciones", "Empresas", "Respuestas"])

with tab1:
    # Mostrar inscripciones
    show_inscriptions(dfs[0], dfs[2], dfs[5], file_dates[0], file_dates[2], file_dates[5], geojson_data)

with tab2:
    # Mostrar empresas
    show_companies(dfs[1], dfs[2], file_dates[1])

with tab3:
    # Mostrar respuestas
    show_responses(dfs[4], file_dates[4])
