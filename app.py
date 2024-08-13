import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
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

# Función para crear gráfico basado en selecciones del usuario
def create_chart(df, x_column, y_column, chart_type):
    if chart_type == 'Bar':
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(x_column, sort='-y'),
            y=y_column
        )
    elif chart_type == 'Line':
        chart = alt.Chart(df).mark_line().encode(
            x=x_column,
            y=y_column
        )
    elif chart_type == 'Scatter':
        chart = alt.Chart(df).mark_circle().encode(
            x=x_column,
            y=y_column
        )
    elif chart_type == 'Pie':
        chart = alt.Chart(df).mark_arc().encode(
            theta=y_column,
            color=x_column
        )
    return chart.properties(width=600, height=400)

# Configuración de la barra lateral
st.sidebar.title("Filtros")

# Descargar datos desde el bucket de Google Cloud
bucket_name = "direccion"
blob_name = "inscripciones_empleo.csv"
csv_file_path = download_from_bucket(blob_name, bucket_name)

# Cargar los datos en un DataFrame
df = pd.read_csv(csv_file_path)

# Convertir las fechas en el DataFrame a un formato estándar
df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], format='%m/%d/%Y %H:%M:%S')

# Filtros en la barra lateral
if 'N_LOCALIDAD' in df.columns:
    localidades = df['N_LOCALIDAD'].unique()
    selected_localidad = st.sidebar.multiselect("Filtrar por Localidad", localidades, default=localidades)

if 'N_DEPARTAMENTO' in df.columns:
    departamentos = df['N_DEPARTAMENTO'].unique()
    selected_departamento = st.sidebar.multiselect("Filtrar por Departamento", departamentos, default=departamentos)

# Aplicar filtros
if 'N_LOCALIDAD' in df.columns:
    df = df[df['N_LOCALIDAD'].isin(selected_localidad)]

if 'N_DEPARTAMENTO' in df.columns:
    df = df[df['N_DEPARTAMENTO'].isin(selected_departamento)]

# Sección de fechas
st.title("Reporte 2024")

# Obtener la fecha mínima y máxima y convertirlas a cadenas
fecha_min = df['FEC_INSCRIPCION'].min().strftime('%Y-%m-%d')
fecha_max = df['FEC_INSCRIPCION'].max().strftime('%Y-%m-%d')

# Mostrar fechas en la parte principal
col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input("Fecha de Inicio", value=datetime.strptime(fecha_min, '%Y-%m-%d'), min_value=datetime.strptime(fecha_min, '%Y-%m-%d'), max_value=datetime.strptime(fecha_max, '%Y-%m-%d'))
with col2:
    fecha_fin = st.date_input("Fecha de Fin", value=datetime.strptime(fecha_max, '%Y-%m-%d'), min_value=datetime.strptime(fecha_min, '%Y-%m-%d'), max_value=datetime.strptime(fecha_max, '%Y-%m-%d'))

# Filtrar los datos según el rango de fechas seleccionado
df = df[(df['FEC_INSCRIPCION'] >= fecha_inicio) & (df['FEC_INSCRIPCION'] <= fecha_fin)]

# Apartado de personalización de gráficos
st.sidebar.header("Personalización de Gráficos")
x_column = st.sidebar.selectbox("Selecciona el campo para el eje X", df.columns)
y_column = st.sidebar.selectbox("Selecciona el campo para el eje Y (conteo)", ['Conteo'] + list(df.columns))
chart_type = st.sidebar.selectbox("Selecciona el tipo de gráfico", ['Bar', 'Line', 'Scatter', 'Pie'])

# Preparar datos para el gráfico
if y_column == 'Conteo':
    chart_data = df.groupby(x_column).size().reset_index(name='Conteo')
else:
    chart_data = df[[x_column, y_column]]

# Crear y mostrar el gráfico personalizado
st.header("Gráfico Personalizado")
chart = create_chart(chart_data, x_column, 'Conteo' if y_column == 'Conteo' else y_column, chart_type)
st.altair_chart(chart, use_container_width=True)

# Mostrar los datos utilizados para el gráfico
st.header("Datos Utilizados")
st.dataframe(chart_data)

# Gráficos predefinidos
st.header("Gráficos Predefinidos")

# DNI por Departamento (Barras)
if 'N_DEPARTAMENTO' in df.columns:
    dni_por_departamento = df.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
    st.subheader("Conteo de ID Inscripción por Departamento (Barras)")
    bar_chart_departamento = alt.Chart(dni_por_departamento).mark_bar().encode(
        x=alt.X('N_DEPARTAMENTO:N', title='Departamento', sort='-y'),
        y=alt.Y('Conteo:Q', title='Conteo'),
        color='N_DEPARTAMENTO:N'
    ).properties(width=600, height=400)
    st.altair_chart(bar_chart_departamento, use_container_width=True)

# DNI por Departamento (Torta)
if 'N_DEPARTAMENTO' in df.columns:
    dni_por_departamento = df.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
    st.subheader("Conteo de ID Inscripción por Departamento (Torta)")
    pie_chart_departamento = alt.Chart(dni_por_departamento).mark_arc().encode(
        theta=alt.Theta(field="Conteo", type="quantitative"),
        color=alt.Color(field='N_DEPARTAMENTO', type="nominal"),
        tooltip=['N_DEPARTAMENTO', 'Conteo']
    ).properties(width=600, height=400)
    st.altair_chart(pie_chart_departamento, use_container_width=True)

# DNI por Localidad (Barras)
if 'N_LOCALIDAD' in df.columns:
    dni_por_localidad = df.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
    st.subheader("Conteo de ID Inscripción por Localidad (Barras)")
    bar_chart_localidad = alt.Chart(dni_por_localidad).mark_bar().encode(
        x=alt.X('N_LOCALIDAD:N', title='Localidad', sort='-y'),
        y=alt.Y('Conteo:Q', title='Conteo'),
        color='N_LOCALIDAD:N'
    ).properties(width=600, height=400)
    st.altair_chart(bar_chart_localidad, use_container_width=True)

# DNI por Localidad (Torta)
if 'N_LOCALIDAD' in df.columns:
    dni_por_localidad = df.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
    st.subheader("Conteo de ID Inscripción por Localidad (Torta)")
    pie_chart_localidad = alt.Chart(dni_por_localidad).mark_arc().encode(
        theta=alt.Theta(field="Conteo", type="quantitative"),
        color=alt.Color(field='N_LOCALIDAD', type="nominal"),
        tooltip=['N_LOCALIDAD', 'Conteo']
    ).properties(width=600, height=400)
    st.altair_chart(pie_chart_localidad, use_container_width=True)

else:
    st.error("No se encontraron datos en el archivo CSV.")
