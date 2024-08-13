import streamlit as st
import pandas as pd
from datetime import datetime
import tempfile
from google.cloud import storage
from google.oauth2 import service_account
import altair as alt

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

st.title("Reporte 2024")

# Descargar datos desde el bucket de Google Cloud
bucket_name = "direccion"
blob_name = "inscripciones_empleo.csv"
csv_file_path = download_from_bucket(blob_name, bucket_name)

# Cargar los datos en un DataFrame
df = pd.read_csv(csv_file_path)

# Convertir las fechas en el DataFrame a un formato estándar
df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], format='%m/%d/%Y %H:%M:%S')

if 'FEC_INSCRIPCION' in df.columns:
    # Obtener las fechas mínima y máxima
    fecha_min = df['FEC_INSCRIPCION'].min()
    fecha_max = df['FEC_INSCRIPCION'].max()

    # Crear los selectores de fechas para seleccionar el rango de fechas
    fecha_inicio = st.date_input("Fecha de Inicio", min_value=fecha_min, max_value=fecha_max, value=fecha_min)
    fecha_fin = st.date_input("Fecha de Fin", min_value=fecha_inicio, max_value=fecha_max, value=fecha_max)
    
    # Filtrar los datos según el rango de fechas seleccionado
    df = df[(df['FEC_INSCRIPCION'] >= fecha_inicio) & (df['FEC_INSCRIPCION'] <= fecha_fin)]

    # Selección de campos para el gráfico
    x_column = st.selectbox("Selecciona el campo para el eje X", df.columns)
    y_column = st.selectbox("Selecciona el campo para el eje Y (conteo)", ['Conteo'] + list(df.columns))
    chart_type = st.selectbox("Selecciona el tipo de gráfico", ['Bar', 'Line', 'Scatter', 'Pie'])

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
