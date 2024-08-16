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

# Configuración de las pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

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

with tab1:
    st.title("Nueva  Oportunidad")

    # Filtrar los datos solo para la pestaña "Inscripciones"
    df_inscripciones = df[df['N_EMPRESA'].isnull()]

    # Filtros en la barra lateral
    st.sidebar.header("Filtros de Inscripciones")
    if 'N_LOCALIDAD' in df_inscripciones.columns:
        localidades = df_inscripciones['N_LOCALIDAD'].unique()
        selected_localidad = st.sidebar.multiselect("Filtrar por Localidad", localidades, default=localidades)

    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        selected_departamento = st.sidebar.multiselect("Filtrar por Departamento", departamentos, default=departamentos)

    # Aplicar filtros
    if 'N_LOCALIDAD' in df_inscripciones.columns:
        df_inscripciones = df_inscripciones[df_inscripciones['N_LOCALIDAD'].isin(selected_localidad)]

    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        df_inscripciones = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)]

    # Sección de fechas
    col1, col2 = st.columns(2)
    fecha_min = df_inscripciones['FEC_INSCRIPCION'].min().date() if not df_inscripciones['FEC_INSCRIPCION'].isnull().all() else None
    fecha_max = df_inscripciones['FEC_INSCRIPCION'].max().date() if not df_inscripciones['FEC_INSCRIPCION'].isnull().all() else None

    if fecha_min and fecha_max:
        with col1:
            fecha_inicio = st.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        with col2:
            fecha_fin = st.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)

        # Filtrar los datos según el rango de fechas seleccionado
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
    else:
        st.error("No se pueden determinar todas las fechas en el archivo CSV.")

    # Gráficos predefinidos para inscripciones
    st.subheader("Conteo de ID Inscripción por Departamento")
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        dni_por_departamento = df_inscripciones.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
        bar_chart_departamento = alt.Chart(dni_por_departamento).mark_bar().encode(
            x=alt.X('N_DEPARTAMENTO:N', title='Departamento', sort='-y'),
            y=alt.Y('Conteo:Q', title='Conteo'),
            color='N_DEPARTAMENTO:N'
        ).properties(width=600, height=400)
        st.altair_chart(bar_chart_departamento, use_container_width=True)

        pie_chart_departamento = alt.Chart(dni_por_departamento).mark_arc().encode(
            theta=alt.Theta(field="Conteo", type="quantitative"),
            color=alt.Color(field='N_DEPARTAMENTO', type="nominal"),
            tooltip=['N_DEPARTAMENTO', 'Conteo']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_departamento, use_container_width=True)

    st.subheader("Conteo de ID Inscripción por Localidad")
    if 'N_LOCALIDAD' in df_inscripciones.columns:
        dni_por_localidad = df_inscripciones.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
        bar_chart_localidad = alt.Chart(dni_por_localidad).mark_bar().encode(
            x=alt.X('N_LOCALIDAD:N', title='Localidad', sort='-x'),
            y=alt.Y('Conteo:Q', title='Conteo'),
            color='N_LOCALIDAD:N'
        ).properties(width=600, height=400)
        st.altair_chart(bar_chart_localidad, use_container_width=True)

        pie_chart_localidad = alt.Chart(dni_por_localidad).mark_arc().encode(
            theta=alt.Theta(field="Conteo", type="quantitative"),
            color=alt.Color(field='N_LOCALIDAD', type="nominal"),
            tooltip=['N_LOCALIDAD', 'Conteo']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_localidad, use_container_width=True)

with tab2:
    st.title("Empresas y Rubros")

    # Filtrar los datos solo para la pestaña "Empresas"
    df_empresas = df[df['N_EMPRESA'].notnull()]


    # Gráficos predefinidos para empresas
    if not df_empresas.empty:
        st.subheader("Recuento Distintivo de N_EMPRESA por N_CATEGORIA_EMPLEO")
        empresa_categoria_distinctivo = df_empresas.groupby(['N_EMPRESA', 'N_CATEGORIA_EMPLEO']).size().reset_index(name='Conteo')
        pie_chart_empresa_categoria = alt.Chart(empresa_categoria_distinctivo).mark_arc().encode(
            theta=alt.Theta(field="Conteo", type="quantitative"),
            color=alt.Color(field='N_CATEGORIA_EMPLEO', type="nominal"),
            tooltip=['N_EMPRESA', 'N_CATEGORIA_EMPLEO', 'Conteo']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_empresa_categoria, use_container_width=True)

        st.subheader("Recuento Distintivo de N_EMPRESA, CANTIDAD_EMPLEADOS y N_PUESTO_EMPLEO")
        empleados_puestos_distinctivo = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS': 'sum'}).reset_index()
        pie_chart_empleados_puestos = alt.Chart(empleados_puestos_distinctivo).mark_arc().encode(
            theta=alt.Theta(field="CANTIDAD_EMPLEADOS", type="quantitative"),
            color=alt.Color(field='N_EMPRESA', type="nominal"),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_empleados_puestos, use_container_width=True)
    else:
        st.error("No se encontraron datos de empresas para mostrar.")
