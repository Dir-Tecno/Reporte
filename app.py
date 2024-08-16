import streamlit as st
import pandas as pd
import altair as alt
import tempfile
from google.cloud import storage
from google.oauth2 import service_account

# Configura las credenciales de Google Cloud usando la variable de entorno
credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Función para descargar el archivo desde el bucket de Google Cloud
def download_from_bucket(blob_name, bucket_name):
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        blob.download_to_filename(temp_file.name)
        return temp_file.name

# Función para cargar y procesar datos
def load_data_from_bucket(blob_names, bucket_name):
    dfs = []
    for blob_name in blob_names:
        csv_file_path = download_from_bucket(blob_name, bucket_name)
        df = pd.read_csv(csv_file_path)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Configuración de la aplicación
st.set_page_config(page_title="Reporte Ejecutivo de Empleo", layout="wide")

# Descargar datos desde el bucket de Google Cloud
bucket_name = "direccion"
blob_names = ["inscripciones_empleo.csv", "SQL_EMPRESAS_ADHERIDAS.csv"]
df = load_data_from_bucket(blob_names, bucket_name)

# Convertir las fechas usando diferentes formatos
try:
    df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
except Exception as e:
    st.error(f"Error al convertir las fechas: {e}")

# Verificar si hay fechas nulas después de la conversión
if df['FEC_INSCRIPCION'].isnull().any():
    st.error("Algunas fechas no pudieron ser convertidas. Verifica que todos los formatos de fecha en el archivo CSV sean consistentes.")

# Configuración de las pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

# Filtros de fechas globales
st.sidebar.header("Filtros de Fechas")
fecha_min = df['FEC_INSCRIPCION'].min().date() if not df['FEC_INSCRIPCION'].isnull().all() else None
fecha_max = df['FEC_INSCRIPCION'].max().date() if not df['FEC_INSCRIPCION'].isnull().all() else None

if fecha_min and fecha_max:
    fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
else:
    st.error("No se pueden determinar todas las fechas en el archivo CSV.")

# Pestaña de Inscripciones
with tab1:
    st.title("Reporte de Inscripciones 2024")
    st.markdown("### Análisis de inscripciones de empleo para el año 2024.")

    # Filtrar los datos solo para la pestaña "Inscripciones"
    df_inscripciones = df[df['N_EMPRESA'].isnull()]

    # Aplicar filtros de fechas
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
    
    # Conteo total de inscripciones
    total_inscripciones = df_inscripciones.shape[0]
    st.markdown(f"**Conteo Total de Inscripciones:** {total_inscripciones}")

    # Filtros en la barra lateral
    st.sidebar.header("Filtros de Inscripciones")
    if 'N_LOCALIDAD' in df_inscripciones.columns:
        localidades = df_inscripciones['N_LOCALIDAD'].unique()
        selected_localidad = st.sidebar.multiselect("Filtrar por Localidad", localidades, default=localidades)

    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        selected_departamento = st.sidebar.multiselect("Filtrar por Departamento", departamentos, default=departamentos)

    # Aplicar filtros adicionales
    if 'N_LOCALIDAD' in df_inscripciones.columns:
        df_inscripciones = df_inscripciones[df_inscripciones['N_LOCALIDAD'].isin(selected_localidad)]

    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        df_inscripciones = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)]

    # Gráficos predefinidos para inscripciones
    st.markdown("### Gráficos de Inscripciones")
    
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        dni_por_departamento = df_inscripciones.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
        st.subheader("Conteo de ID Inscripción por Departamento")
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(
                alt.Chart(dni_por_departamento).mark_bar().encode(
                    x=alt.X('N_DEPARTAMENTO:N', title='Departamento', sort='-y'),
                    y=alt.Y('Conteo:Q', title='Conteo'),
                    color='N_DEPARTAMENTO:N'
                ).properties(width=300, height=300),
                use_container_width=True
            )
        with col2:
            st.altair_chart(
                alt.Chart(dni_por_departamento).mark_arc().encode(
                    theta=alt.Theta(field="Conteo", type="quantitative"),
                    color=alt.Color(field='N_DEPARTAMENTO', type="nominal"),
                    tooltip=['N_DEPARTAMENTO', 'Conteo']
                ).properties(width=300, height=300),
                use_container_width=True
            )

    if 'N_LOCALIDAD' in df_inscripciones.columns:
        dni_por_localidad = df_inscripciones.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
        st.subheader("Conteo de ID Inscripción por Localidad")
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(
                alt.Chart(dni_por_localidad).mark_bar().encode(
                    x=alt.X('N_LOCALIDAD:N', title='Localidad', sort='-x'),
                    y=alt.Y('Conteo:Q', title='Conteo'),
                    color='N_LOCALIDAD:N'
                ).properties(width=300, height=300),
                use_container_width=True
            )
        with col2:
            st.altair_chart(
                alt.Chart(dni_por_localidad).mark_arc().encode(
                    theta=alt.Theta(field="Conteo", type="quantitative"),
                    color=alt.Color(field='N_LOCALIDAD', type="nominal"),
                    tooltip=['N_LOCALIDAD', 'Conteo']
                ).properties(width=300, height=300),
                use_container_width=True
            )

# Pestaña de Empresas
with tab2:
    st.title("Análisis de Empresas y Rubros")
    st.markdown("### Información sobre empresas y sus respectivos rubros.")

    # Filtrar los datos solo para la pestaña "Empresas"
    df_empresas = df[df['N_EMPRESA'].notnull()]

    # Conteo total de empresas
    total_empresas = df_empresas['CUIT'].nunique()

    # Botón con el conteo distintivo de CUIT
    st.markdown(f"**Conteo Distintivo de CUIT:**")
    st.button(f"{total_empresas} Empresas Únicas")

    # Gráficos predefinidos para empresas
    if not df_empresas.empty:
        st.subheader("Recuento Distintivo de N_EMPRESA por N_CATEGORIA_EMPLEO")
        st.altair_chart(
            alt.Chart(df_empresas.groupby(['N_EMPRESA', 'N_CATEGORIA_EMPLEO']).size().reset_index(name='Conteo')).mark_arc().encode(
                theta=alt.Theta(field="Conteo", type="quantitative"),
                color=alt.Color(field='N_CATEGORIA_EMPLEO', type="nominal"),
                tooltip=['N_EMPRESA', 'N_CATEGORIA_EMPLEO', 'Conteo']
            ).properties(width=600, height=400),
            use_container_width=True
        )

        st.subheader("Recuento Distintivo de N_EMPRESA, CANTIDAD_EMPLEADOS y N_PUESTO_EMPLEO")
        st.altair_chart(
            alt.Chart(df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS': 'sum'}).reset_index()).mark_arc().encode(
                theta=alt.Theta(field="CANTIDAD_EMPLEADOS", type="quantitative"),
                color=alt.Color(field='N_EMPRESA', type="nominal"),
                tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
            ).properties(width=600, height=400),
            use_container_width=True
        )
