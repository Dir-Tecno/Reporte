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
    dfs = []
    file_dates = []  # Lista para almacenar las fechas de modificación de los archivos
    
    for blob_name in blob_names:
        temp_file_name, file_date = download_from_bucket(blob_name, bucket_name)
        # Especificar tipos de datos para evitar advertencias
        df = pd.read_csv(temp_file_name, low_memory=False)
        dfs.append(df)
        file_dates.append(file_date)  # Almacenar la fecha de modificación
    
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df, file_dates


# Configuración de la aplicación
st.set_page_config(page_title="Reporte Ejecutivo de Empleo", layout="wide")

# Descargar y procesar los datos
bucket_name = "direccion"
blob_names = ["vt_inscripciones_empleo.csv", "vt_empresas_adheridas.csv"]
df, file_dates = load_data_from_bucket(blob_names, bucket_name)

# Convertir las fechas
if 'FEC_INSCRIPCION' in df.columns:
    df['FEC_INSCRIPCION'] = pd.to_datetime(df['FEC_INSCRIPCION'], dayfirst=True)
    if df['FEC_INSCRIPCION'].isnull().any():
        pass
        #st.error("Algunas fechas no pudieron ser convertidas. Verifica los formatos de fecha en el archivo CSV.")


# Configuración de pestañas
tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])

# Pestaña de Inscripciones
with tab1:
    st.markdown("### Inscripciones Programas Empleo 2024")
    st.write(f"Datos del archivo actualizados al: {file_dates[0].strftime('%d/%m/%Y %H:%M:%S')}")

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

        # DNI por Localidad (Barras)
    if 'N_LOCALIDAD' in df.columns and 'N_DEPARTAMENTO' in df.columns:
        # Agrupar por N_LOCALIDAD y N_DEPARTAMENTO
        dni_por_localidad = df.groupby(['N_LOCALIDAD', 'N_DEPARTAMENTO']).size().reset_index(name='Conteo')

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
    st.markdown("### Gráficos de Inscripciones por departamentos")

     
    # Filtros debajo del título
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        default_departamentos = ["CAPITAL", "RIO CUARTO"]
        # Verificar si los valores predeterminados están en la lista de departamentos
        default_departamentos = [dep for dep in default_departamentos if dep in departamentos]
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=default_departamentos)    

    # Filtrar el DataFrame según el Departamento seleccionado para obtener las localidades correspondientes
    if 'N_LOCALIDAD' in df_inscripciones.columns and selected_departamento:
        localidades = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)]['N_LOCALIDAD'].unique()
        selected_localidad = st.multiselect("Filtrar por Localidad", localidades, default=localidades)
    else:
        selected_localidad = [] 

    # Filtrar el DataFrame basado en las selecciones
    df_filtered = df_inscripciones[
        (df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)) & 
        (df_inscripciones['N_LOCALIDAD'].isin(selected_localidad))
    ]

    # Gráficos que responden a los filtros
    if 'N_DEPARTAMENTO' in df_filtered.columns:
        dni_por_departamento = df_filtered.groupby('N_DEPARTAMENTO').size().reset_index(name='Conteo')
        st.subheader("Conteo de Adhesiones por Departamento")

        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(
            alt.Chart(dni_por_departamento).mark_bar().encode(
                y=alt.Y('N_DEPARTAMENTO:N', title='Departamento', sort='-x'),
                x=alt.X('Conteo:Q', title='Conteo'),
                color=alt.Color('N_DEPARTAMENTO:N', legend=None),  # Se elimina la leyenda si no es necesaria
                tooltip=['N_DEPARTAMENTO', 'Conteo']
            ).properties(
                width=300,
                height=300
            ),
            use_container_width=True    
        )

    if 'N_LOCALIDAD' in df_filtered.columns:
        dni_por_localidad = df_filtered.groupby('N_LOCALIDAD').size().reset_index(name='Conteo')
        with col2:
            st.table(dni_por_localidad.pivot_table(index='N_LOCALIDAD', columns='N_DEPARTAMENTO', values='Conteo', fill_value=0))

# Pestaña de Empresas
with tab2:
    st.markdown("### Información sobre empresas y puestos solicitados.")
    st.write(f"Datos del archivo actualizados al: {file_dates[1].strftime('%d/%m/%Y %H:%M:%S')}")


    df_empresas = df[df['N_EMPRESA'].notnull()]
    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Empresas Adheridas", value=total_empresas)

    if st.button("Mostrar empresas"):
        #st.write(df_empresas[['N_EMPRESA','CANTIDAD_EMPLEADOS','N_PUESTO_EMPLEO','N_CATEGORIA_EMPLEO']].drop_duplicates())
        st.write(df_empresas[['N_EMPRESA','CANTIDAD_EMPLEADOS']].drop_duplicates().reset_index(drop=True))
    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        # Agrupar los datos y generar el gráfico de barras apiladas
        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()

        stacked_bar_chart_2 = alt.Chart(df_puesto_agg).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(
            width=600,
            height=400
        )

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)
