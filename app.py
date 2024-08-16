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

# Encabezado con imagen y título
st.image("https://via.placeholder.com/800x150.png?text=Reporte+Corporativo", use_column_width=True)
st.title("Reporte de Datos 2024")
st.markdown("---")

# Configuración de la barra lateral
with st.sidebar:
    st.title("Configuración")
    st.markdown("**Filtros generales**")
    if 'N_LOCALIDAD' in df.columns:
        localidades = df['N_LOCALIDAD'].unique()
        selected_localidad = st.multiselect("Filtrar por Localidad", localidades, default=localidades)
    if 'N_DEPARTAMENTO' in df.columns:
        departamentos = df['N_DEPARTAMENTO'].unique()
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=departamentos)

    # Aplicar filtros
    if 'N_LOCALIDAD' in df.columns:
        df = df[df['N_LOCALIDAD'].isin(selected_localidad)]
    if 'N_DEPARTAMENTO' in df.columns:
        df = df[df['N_DEPARTAMENTO'].isin(selected_departamento)]

    st.markdown("**Rango de fechas**")
    fecha_min = df['FEC_INSCRIPCION'].min().date() if not df['FEC_INSCRIPCION'].isnull().all() else None
    fecha_max = df['FEC_INSCRIPCION'].max().date() if not df['FEC_INSCRIPCION'].isnull().all() else None

    if fecha_min and fecha_max:
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        with col2:
            fecha_fin = st.date_input("Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        df = df[(df['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & (df['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
    else:
        st.error("No se pueden determinar todas las fechas en el archivo CSV.")

# Tabs para navegar entre las secciones
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

with tab1:
    st.subheader("Reporte de Inscripciones")
    
    # DNI por Departamento (Barras)
    if 'N_DEPARTAMENTO' in df.columns:
        dni_por_departamento = df.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Conteo por Departamento (Barras)")
            bar_chart_departamento = alt.Chart(dni_por_departamento).mark_bar().encode(
                x=alt.X('N_DEPARTAMENTO:N', title='Departamento', sort='-y'),
                y=alt.Y('Conteo:Q', title='Conteo'),
                color=alt.Color('N_DEPARTAMENTO:N', scale=alt.Scale(scheme='blues'), legend=None)
            ).properties(width=350, height=350).configure_axis(
                labelFontSize=12,
                titleFontSize=14
            )
            st.altair_chart(bar_chart_departamento, use_container_width=True)

        with col2:
            st.subheader("Conteo por Departamento (Torta)")
            pie_chart_departamento = alt.Chart(dni_por_departamento).mark_arc().encode(
                theta=alt.Theta(field="Conteo", type="quantitative"),
                color=alt.Color(field='N_DEPARTAMENTO', type="nominal", scale=alt.Scale(scheme='blues')),
                tooltip=['N_DEPARTAMENTO', 'Conteo']
            ).properties(width=350, height=350)
            st.altair_chart(pie_chart_departamento, use_container_width=True)

    # DNI por Localidad (Barras)
    if 'N_LOCALIDAD' in df.columns:
        dni_por_localidad = df.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Conteo por Localidad (Barras)")
            bar_chart_localidad = alt.Chart(dni_por_localidad).mark_bar().encode(
                x=alt.X('N_LOCALIDAD:N', title='Localidad', sort='-x'),
                y=alt.Y('Conteo:Q', title='Conteo'),
                color=alt.Color('N_LOCALIDAD:N', scale=alt.Scale(scheme='greens'), legend=None)
            ).properties(width=350, height=350).configure_axis(
                labelFontSize=12,
                titleFontSize=14
            )
            st.altair_chart(bar_chart_localidad, use_container_width=True)

        with col4:
            st.subheader("Conteo por Localidad (Torta)")
            pie_chart_localidad = alt.Chart(dni_por_localidad).mark_arc().encode(
                theta=alt.Theta(field="Conteo", type="quantitative"),
                color=alt.Color(field='N_LOCALIDAD', type="nominal", scale=alt.Scale(scheme='greens')),
                tooltip=['N_LOCALIDAD', 'Conteo']
            ).properties(width=350, height=350)
            st.altair_chart(pie_chart_localidad, use_container_width=True)

with tab2:
    st.subheader("Empresas y Rubros")

    # Filtrar para el segundo CSV
    df_empresas = df[df['N_EMPRESA'].notnull()]

    if not df_empresas.empty:
        # Recuento distintivo para N_EMPRESA y N_CATEGORIA_EMPLEO
        st.subheader("Recuento Distintivo por Rubro")
        empresa_categoria_distinctivo = df_empresas.groupby(['N_EMPRESA', 'N_CATEGORIA_EMPLEO']).size().reset_index(name='Conteo')
        pie_chart_empresa_categoria = alt.Chart(empresa_categoria_distinctivo).mark_arc().encode(
            theta=alt.Theta(field="Conteo", type="quantitative"),
            color=alt.Color(field='N_CATEGORIA_EMPLEO', type="nominal", scale=alt.Scale(scheme='reds')),
            tooltip=['N_EMPRESA', 'N_CATEGORIA_EMPLEO', 'Conteo']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_empresa_categoria, use_container_width=True)

        # Recuento distintivo para N_EMPRESA, CANTIDAD_EMPLEADOS, y N_PUESTO_EMPLEO
        st.subheader("Recuento Distintivo de Empleados")
        empleados_puestos_distinctivo = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS': 'sum'}).reset_index()
        pie_chart_empleados_puestos = alt.Chart(empleados_puestos_distinctivo).mark_arc().encode(
            theta=alt.Theta(field="CANTIDAD_EMPLEADOS", type="quantitative"),
            color=alt.Color(field='N_EMPRESA', type="nominal", scale=alt.Scale(scheme='oranges')),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_empleados_puestos, use_container_width=True)
    else:
        st.error("No se encontraron datos de empresas para mostrar.")
