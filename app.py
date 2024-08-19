import streamlit as st
import pandas as pd
import altair as alt
import tempfile
from google.cloud import storage
from google.oauth2 import service_account

# Configura las credenciales de Google Cloud
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
        temp_file_name = download_from_bucket(blob_name, bucket_name)
        # Especificar tipos de datos para evitar advertencias
        df = pd.read_csv(temp_file_name, dtype={'column_29': 'str', 'column_30': 'str', 'column_31': 'str', 'column_32': 'str'}, low_memory=False)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Configuración de la aplicación
st.set_page_config(page_title="Reporte Ejecutivo de Empleo", layout="wide")

# Descargar y procesar los datos
bucket_name = "direccion"
blob_names = ["vt_inscripciones_empleo.csv", "SQL_EMPRESAS_ADHERIDAS.csv"]
df = load_data_from_bucket(blob_names, bucket_name)

# Convertir las fechas
if 'FEC_INSCRIPCION' in df.columns:
    df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
    if df['FEC_INSCRIPCION'].isnull().any():
        st.error("Algunas fechas no pudieron ser convertidas. Verifica los formatos de fecha en el archivo CSV.")


# Configuración de pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

# Pestaña de Inscripciones
with tab1:
    st.title("Reporte de Inscripciones 2024")
    st.markdown("### Inscripciones Programas Empleo 2024")

    df_inscripciones = df[df['N_EMPRESA'].isnull()]

    if 'FEC_INSCRIPCION' in df.columns:
        st.sidebar.header("Filtros de Fechas")
        fecha_min, fecha_max = df['FEC_INSCRIPCION'].min().date(), df['FEC_INSCRIPCION'].max().date()
        fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & 
                                            (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]

    total_inscripciones = df_inscripciones.shape[0]
    st.metric(label="Adhesiones", value=total_inscripciones)

    if 'N_LOCALIDAD' in df.columns:
        top_10_localidades = df.groupby('N_LOCALIDAD').size().reset_index(name='Conteo').sort_values(by='Conteo', ascending=False).head(10)
        st.subheader("Top 10 de ID Inscripción por Localidad (Barras)")
        bar_chart_localidad = alt.Chart(top_10_localidades).mark_bar().encode(
            y=alt.Y('N_LOCALIDAD:N', title='Localidad', sort='-x'),
            x=alt.X('Conteo:Q', title='Conteo'),
            color='N_LOCALIDAD:N'
        ).properties(width=600, height=400)
        st.altair_chart(bar_chart_localidad, use_container_width=True)

    st.markdown("### Gráficos de Inscripciones")
    departamentos = st.multiselect("Filtrar por Departamento", df_inscripciones['N_DEPARTAMENTO'].unique(), default=["CAPITAL", "RIO CUARTO"])
    localidades = st.multiselect("Filtrar por Localidad", df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(departamentos)]['N_LOCALIDAD'].unique(),default=["CORDOBA", "RIO CUARTO"])

    df_filtered = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(departamentos) & df_inscripciones['N_LOCALIDAD'].isin(localidades)]

    if not df_filtered.empty:
        col1, col2 = st.columns(2)
        dni_por_departamento = df_filtered.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
        dni_por_localidad = df_filtered.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')

        with col1:
            st.altair_chart(alt.Chart(dni_por_departamento).mark_arc().encode(
                theta=alt.Theta(field="Conteo", type="quantitative"),
                color=alt.Color(field='N_DEPARTAMENTO', type="nominal"),
                tooltip=['N_DEPARTAMENTO', 'Conteo']
            ).properties(width=300, height=300), use_container_width=True)

        with col2:
            st.altair_chart(alt.Chart(dni_por_localidad).mark_bar().encode(
                x=alt.X('N_LOCALIDAD:N', title='Localidad', sort='-y'),
                y=alt.Y('Conteo:Q', title='Conteo'),
                color='N_LOCALIDAD:N'
            ).properties(width=300, height=300), use_container_width=True)

# Pestaña de Empresas
with tab2:
    st.title("Análisis de Empresas y Rubros")
    st.markdown("### Información sobre empresas y sus respectivos rubros.")

    df_empresas = df[df['N_EMPRESA'].notnull()]
    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Conteo Total de Empresas Adheridas", value=total_empresas)

    if st.button("Mostrar empresas distintivas"):
        st.write(df_empresas[['CUIT', 'N_EMPRESA', 'N_CATEGORIA_EMPLEO']].drop_duplicates())

    if not df_empresas.empty:
        st.subheader("Recuento Distintivo de N_EMPRESA por N_CATEGORIA_EMPLEO")
        st.altair_chart(alt.Chart(df_empresas.groupby(['N_EMPRESA', 'N_CATEGORIA_EMPLEO']).size().reset_index(name='Conteo')).mark_arc().encode(
            theta=alt.Theta(field="Conteo", type="quantitative"),
            color=alt.Color(field='N_CATEGORIA_EMPLEO', type="nominal"),
            tooltip=['N_EMPRESA', 'N_CATEGORIA_EMPLEO', 'Conteo']
        ).properties(width=600, height=400), use_container_width=True)

        st.subheader("Distribución de Empleados por Empresa y Puesto")
        st.altair_chart(alt.Chart(df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()).mark_arc().encode(
            theta=alt.Theta(field="CANTIDAD_EMPLEADOS", type="quantitative"),
            color=alt.Color(field='N_PUESTO_EMPLEO', type="nominal"),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400), use_container_width=True)
