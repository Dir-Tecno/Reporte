import streamlit as st
import pandas as pd
import altair as alt
import tempfile
from datetime import timedelta
from google.cloud import storage
from google.oauth2 import service_account

# Configura las credenciales de Google Cloud
credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Función para descargar el archivo desde el bucket de Google Cloud y obtener la fecha de modificación
def download_from_bucket(blob_name, bucket_name):
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Obtener la fecha de última modificación del archivo
    blob.reload()  # Asegúrate de recargar los metadatos del blob
    file_date = blob.updated  # Esta es la fecha de modificación del archivo

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        blob.download_to_filename(temp_file.name)
        return temp_file.name, file_date - timedelta(hours=3)


# Función para cargar y procesar datos, y retornar la fecha de los archivos
def load_data_from_bucket(blob_names, bucket_name):
    file_dates = []  # Lista para almacenar las fechas de modificación de los archivos
    for blob_name in blob_names:
        temp_file_name, file_date = download_from_bucket(blob_name, bucket_name)
        # Especificar tipos de datos para evitar advertencias
        df = pd.read_csv(temp_file_name, low_memory=False)
        dfs.append(df)
        file_dates.append(file_date)  # Almacenar la fecha de modificación
    #combined_df = pd.concat(dfs, ignore_index=True)
    return dfs, file_dates

# Configuración de la aplicación
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Descargar y procesar los datos
dfs = []
bucket_name = "direccion"
blob_names = ["vt_inscripciones_empleo.csv", "vt_empresas_adheridas.csv"]
dfs, file_dates = load_data_from_bucket(blob_names, bucket_name)

df_inscripciones = dfs[0]
df_empresas = dfs[1]



# Convertir las fechas
if 'FEC_INSCRIPCION' in df_inscripciones.columns:
    df_inscripciones['FEC_INSCRIPCION'] = pd.to_datetime(df_inscripciones['FEC_INSCRIPCION'],  errors='coerce')
if 'FEC_NACIMIENTO' in df_inscripciones.columns:
    df_inscripciones['FEC_NACIMIENTO'] = pd.to_datetime(df_inscripciones['FEC_NACIMIENTO'], errors='coerce')
df_inscripciones = df_inscripciones.dropna(subset=['FEC_INSCRIPCION', 'FEC_NACIMIENTO'])

# Configuración de pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

# Pestaña de Inscripciones
with tab1:
    st.markdown("### Inscripciones Programas Empleo 2024")
    st.write(f"Datos del archivo actualizados al: {file_dates[0].strftime('%d/%m/%Y %H:%M:%S')}")


    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        st.sidebar.header("Filtros de Fechas")
        fecha_min, fecha_max = df_inscripciones['FEC_INSCRIPCION'].min().date(), df_inscripciones['FEC_INSCRIPCION'].max().date()
        fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & 
                                            (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]

    # Calcular edades
    df_inscripciones['Edad'] = (pd.Timestamp('2024-08-19') - df_inscripciones['FEC_NACIMIENTO']).dt.days // 365

    # Calcular el total de adhesiones
    total_inscripciones = df_inscripciones.shape[0]

    # Calcular el conteo de personas de 26 años o menos
    count_26_or_less = df_inscripciones[df_inscripciones['Edad'] <= 26].shape[0]

    # Calcular el conteo de personas entre 27 y 44 años
    count_26_44 = df_inscripciones[(df_inscripciones['Edad'] > 26) & (df_inscripciones['Edad'] < 45)].shape[0]

    # Calcular el conteo de personas de 45 años o más
    count_45 = df_inscripciones[df_inscripciones['Edad'] >= 45].shape[0]

    # Validar si los conteos suman el total de adhesiones
    sum_edades = count_26_or_less + count_26_44 + count_45

    # Mostrar las métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Adhesiones", value=total_inscripciones)
    with col2:
        st.metric(label="26 años o menos", value=count_26_or_less)
    with col3:
        st.metric(label="Entre 26 y 44 años", value=count_26_44)   
    with col4:
        st.metric(label="45 años o más", value=count_45)

    # Separador
    st.markdown("###")

    # DNI por Localidad (Barras)
    if 'N_LOCALIDAD' in df_inscripciones.columns and 'N_DEPARTAMENTO' in df_inscripciones.columns:
        # Agrupar por N_LOCALIDAD y N_DEPARTAMENTO
        dni_por_localidad = df_inscripciones.groupby(['N_LOCALIDAD', 'N_DEPARTAMENTO']).size().reset_index(name='Conteo')

        # Reemplazar N_DEPARTAMENTO: todo lo que no es "CAPITAL" se convierte en "INTERIOR"
        dni_por_localidad['N_DEPARTAMENTO'] = dni_por_localidad['N_DEPARTAMENTO'].apply(lambda x: 'INTERIOR' if x != 'CAPITAL' else 'CAPITAL')

        # Crear un filtro de selección entre "CAPITAL" e "INTERIOR"
        dni_por_localidad_filter = st.multiselect("Filtrar por Región", dni_por_localidad['N_DEPARTAMENTO'].unique(), default=dni_por_localidad['N_DEPARTAMENTO'].unique())

        # Filtrar los datos según la selección del filtro
        dni_por_localidad = dni_por_localidad[dni_por_localidad['N_DEPARTAMENTO'].isin(dni_por_localidad_filter)]

        # Ordenar por conteo en orden descendente y seleccionar los 10 primeros
        top_10_localidades = dni_por_localidad.sort_values(by='Conteo', ascending=False).head(10)

        st.subheader("Top 10 de Adhesiones por Localidad")

        # Gráfico de barras horizontales
        bar_chart_localidad = alt.Chart(top_10_localidades).mark_bar().encode(
            y=alt.Y('N_LOCALIDAD:N', title='Localidad', sort='-x'),
            x=alt.X('Conteo:Q', title='Conteo'),
            color=alt.Color('N_LOCALIDAD:N', legend=None)  # Se elimina la leyenda
        ).properties(width=600, height=400)

        # Etiquetas de conteo en las barras
        text = bar_chart_localidad.mark_text(
            align='left',
            baseline='middle',
            dx=3  # Desplazamiento del texto a la derecha de las barras
        ).encode(
            text='Conteo:Q'
        )

        # Combinar el gráfico de barras con las etiquetas
        final_chart = bar_chart_localidad + text

        # Mostrar el gráfico en Streamlit
        st.altair_chart(final_chart, use_container_width=True)

    # Gráficos predefinidos para inscripciones
    st.markdown("### Gráficos de Inscripciones por Departamentos")

    # Filtros debajo del título
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=departamentos)
        df_filtered_departamentos = df_inscripciones[
            df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)
        ]
    else:
        df_filtered_departamentos = df_inscripciones

    # Agrupar y contar los datos
    departamento_counts = df_filtered_departamentos.groupby(['N_DEPARTAMENTO', 'N_LOCALIDAD']).size().reset_index(name='Conteo de ID_INSCRIPCION')

    # Ordenar la tabla en orden descendente por 'Conteo de ID_INSCRIPCION'
    departamento_counts_sorted = departamento_counts.sort_values(by='Conteo de ID_INSCRIPCION', ascending=False)

    # Mostrar el gráfico y la tabla
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Conteo por Departamento")
        st.altair_chart(
            alt.Chart(departamento_counts_sorted).mark_bar().encode(
                y=alt.Y('N_DEPARTAMENTO:N', title='Departamento', sort='-x'),
                x=alt.X('Conteo de ID_INSCRIPCION:Q', title='Conteo'),
                color=alt.Color('N_DEPARTAMENTO:N', legend=None),
                tooltip=['N_DEPARTAMENTO', 'Conteo de ID_INSCRIPCION']
            ).properties(
                width=600,
                height=400
            ),
            use_container_width=True
        )

    with col1:
        st.subheader("Tabla de Adhesiones")
        st.dataframe(departamento_counts_sorted, hide_index=True)

# Pestaña de Empresas
with tab2:
    st.markdown("### Información sobre empresas y puestos.")
    st.write(f"Datos del archivo actualizados al: {file_dates[1].strftime('%d/%m/%Y %H:%M:%S')}")

    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Empresas Adheridas", value=total_empresas)

    if st.button("Mostrar empresas"):
        st.dataframe(df_empresas[['CUIT','N_LOCALIDAD','N_EMPRESA', 'CANTIDAD_EMPLEADOS']].drop_duplicates(),hide_index=True)

    # Verificar si el DataFrame no está vacío antes de continuar
    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        # Agrupar los datos
        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()

        # Crear el gráfico de barras apiladas
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(
            width=600,
            height=400
        )

        # Mostrar el gráfico en Streamlit si el DataFrame no está vacío
        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

        # Agrupar los datos por N_PUESTO_EMPLEO y contar las apariciones de cada puesto
        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')

        # Ordenar los puestos por conteo descendente
        conteo_puestos = conteo_puestos.sort_values(by='Conteo', ascending=False).reset_index(drop=True)

        # Mostrar el resultado como una tabla en Streamlit
        st.subheader("Conteo de Apariciones por Puesto de Empleo")
        st.dataframe(conteo_puestos, hide_index=True)
        #st.write(conteo_puestos)

        # Crear un gráfico de barras horizontales
        grafico_puestos = alt.Chart(conteo_puestos).mark_bar().encode(
            x=alt.X('Conteo:Q', title='Conteo'),
            y=alt.Y('N_PUESTO_EMPLEO:N', title='Puesto de Empleo', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', legend=None),  # Se elimina la leyenda si no es necesaria
            tooltip=['N_PUESTO_EMPLEO', 'Conteo']
        ).properties(
            width=600,
            height=400
        )

        # Mostrar el gráfico en Streamlit
        st.subheader("Gráfico de Barras de Apariciones por Puesto de Empleo")
        st.altair_chart(grafico_puestos, use_container_width=True)
        