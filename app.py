import streamlit as st
import pandas as pd
import altair as alt
import os
from google.cloud import storage
import json
from google.oauth2 import service_account
import tempfile

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

st.title("Reporte Escrituración 2024")

# Descargar datos desde el bucket de Google Cloud
bucket_name = "direccion"
blob_name = "inscripciones_empleo.csv"
csv_file_path = download_from_bucket(blob_name, bucket_name)

# Cargar los datos en un DataFrame
df = pd.read_csv(csv_file_path)

if not df.empty:
    # Coloca los filtros por encima del contenido principal
    st.header("Filtros")
    
    # Filtros de LOCALIDAD y DEPARTAMENTO
    localidades = st.multiselect("Filtrar por Localidad", options=df['LOCALIDAD'].unique(), default=df['LOCALIDAD'].unique())
    departamentos = st.multiselect("Filtrar por Departamento", options=df['DEPARTAMENTO'].unique(), default=df['DEPARTAMENTO'].unique())
    
    # Filtrar el DataFrame según las selecciones
    df = df[df['LOCALIDAD'].isin(localidades) & df['DEPARTAMENTO'].isin(departamentos)]

    # Filtro de fecha con control deslizante
    if 'fecha' in df.columns:
        fecha_min = pd.to_datetime(df['fecha'].min())
        fecha_max = pd.to_datetime(df['fecha'].max())
        fecha_range = st.slider("Selecciona el rango de fechas", min_value=fecha_min, max_value=fecha_max, value=(fecha_min, fecha_max))
        df = df[(pd.to_datetime(df['fecha']) >= fecha_range[0]) & (pd.to_datetime(df['fecha']) <= fecha_range[1])]

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

    # DNI por Estado
    if 'Estado (diario)' in df.columns:
        dni_por_estado = df.groupby('Estado (diario)').size().reset_index(name='DNI')
        st.subheader("DNI por Estado")
        bar_chart_estado = alt.Chart(dni_por_estado).mark_bar().encode(
            x=alt.X('Estado (diario):N', title='Estado (diario)', sort='-y'),
            y=alt.Y('DNI:Q', title='DNI'),
            color='Estado (diario):N'
        ).properties(width=600, height=400)
        st.altair_chart(bar_chart_estado, use_container_width=True)

    # DNI por Departamento
    if 'DEPARTAMENTO' in df.columns:
        dni_por_departamento = df.groupby('DEPARTAMENTO').size().reset_index(name='DNI')
        st.subheader("DNI por Departamento")
        pie_chart_departamento = alt.Chart(dni_por_departamento).mark_arc().encode(
            theta=alt.Theta(field="DNI", type="quantitative"),
            color=alt.Color(field='DEPARTAMENTO', type="nominal"),
            tooltip=['DEPARTAMENTO', 'DNI']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_departamento)

    # DNI por Localidad
    if 'LOCALIDAD' in df.columns:
        dni_por_localidad = df.groupby('LOCALIDAD').size().reset_index(name='DNI')
        st.subheader("DNI por Localidad")
        pie_chart_localidad = alt.Chart(dni_por_localidad).mark_arc().encode(
            theta=alt.Theta(field="DNI", type="quantitative"),
            color=alt.Color(field='LOCALIDAD', type="nominal"),
            tooltip=['LOCALIDAD', 'DNI']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_localidad)

    # DNI por Barrio/Cooperativa
    if 'BARRIO/COOPERATIVA' in df.columns:
        dni_por_barrio = df.groupby('BARRIO/COOPERATIVA').size().reset_index(name='DNI')
        st.subheader("DNI por Barrio/Cooperativa")
        pie_chart_barrio = alt.Chart(dni_por_barrio).mark_arc().encode(
            theta=alt.Theta(field="DNI", type="quantitative"),
            color=alt.Color(field='BARRIO/COOPERATIVA', type="nominal"),
            tooltip=['BARRIO/COOPERATIVA', 'DNI']
        ).properties(width=600, height=400)
        st.altair_chart(pie_chart_barrio)

else:
    st.error("No se encontraron datos en el archivo CSV.")
