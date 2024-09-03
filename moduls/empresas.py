import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

def calculate_cupo(cantidad_empleados):
    if cantidad_empleados <= 7:
        return 2
    elif cantidad_empleados <= 30:
        return math.floor(0.2 * cantidad_empleados)
    elif cantidad_empleados <= 165:
        return math.floor(0.15 * cantidad_empleados)
    else:
        return math.floor(0.1 * cantidad_empleados)

def show_companies(df_empresas, df_inscriptos, df_empresas_seleccionadas):
    # Validar columnas necesarias
    required_columns_inscriptos = ['FER_NAC', 'ID_EST_FIC', 'ID_MOD_CONT_AFIP', 'CUIL', 'RAZON_SOCIAL', 'N_DEPARTAMENTO']
    for col in required_columns_inscriptos:
        if col not in df_inscriptos.columns:
            st.error(f"Falta la columna {col} en df_inscriptos")
            return

    required_columns_empresas = ['CUIT', 'CANTIDAD_EMPLEADOS', 'N_EMPRESA', 'N_PUESTO_EMPLEO']
    for col in required_columns_empresas:
        if col not in df_empresas.columns:
            st.error(f"Falta la columna {col} en df_empresas")
            return

    # Convertir FER_NAC a fecha, manejar errores
    df_inscriptos['FER_NAC'] = pd.to_datetime(df_inscriptos['FER_NAC'], errors='coerce')
    df_inscriptos = df_inscriptos.copy()

     # Filtrar solo los CTI
    df_cti = df_inscriptos[df_inscriptos['ID_MOD_CONT_AFIP'] == 8.0]

    # Filtrar solo los registros con ID_EST_FICHA = 8
    df_inscriptos = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 8] 

    # Calcular métricas para inscriptos
    fecha_actual = pd.Timestamp(datetime.now())
    df_inscriptos['Edad'] = (fecha_actual - df_inscriptos['FER_NAC']).dt.days // 365
    
    # Contar CUILs únicos de personas de 45 años o más en inscriptos
    count_45_inscriptos_unique_cuil = df_inscriptos[df_inscriptos['Edad'] >= 45]['CUIL'].nunique()

    # Calcular el número de CUIL únicos
    unique_cuil_count = df_inscriptos['CUIL'].nunique()

    # Filtrar inscripciones para los departamentos específicos y que tengan menos de 45 años
    df_dept_specific = df_inscriptos[
        (df_inscriptos['N_DEPARTAMENTO'].isin([
            'PRESIDENTE ROQUE SAENZ PEÑA', 
            'GENERAL ROCA',
            "RIO SECO",
            "TULUMBA",
            "POCHO",
            "SAN JAVIER",
            "SAN ALBERTO",
            "MINAS",
            "CRUZ DEL EJE",
            "TOTORAL",
            "SOBREMONTE",
            "ISCHILIN"
        ])) & (df_inscriptos['Edad'] < 45)
    ]

    total_dept_specific = df_dept_specific.shape[0]

    # Métricas de adhesiones
    total_empresas = df_empresas['CUIT'].nunique()
    inscriptos_por_empresa = df_inscriptos.groupby('RAZON_SOCIAL')['ID_FICHA'].count().reset_index(name='Inscriptos')
    inscriptos_por_empresa = inscriptos_por_empresa.sort_values(by='Inscriptos', ascending=False)
    
    # Cálculo total
    total_inscriptos = df_inscriptos.shape[0]
    total_cti = df_cti.shape[0]

    # Mostrar métricas en la pestaña de Empresas
    st.metric(label="Empresas Adheridas", value=total_empresas)
    
    # Añadir las métricas "Matcheos"
    st.markdown("### Matcheos")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Inscriptos/Match", value=total_inscriptos)

    with col2:
        st.metric(label="Personas Únicas (CUIL)", value=unique_cuil_count)

    with col3:
        st.metric(label="Inscriptos 45 años o más", value=count_45_inscriptos_unique_cuil)

    with col4:
        st.metric(label="Inscriptos Zonas Favorecidas", value=total_dept_specific)
    
    with col5:
        st.markdown(
            f"""
            <div style="background-color:rgb(255, 209, 209); padding:10px; border-radius:5px;">
                <strong>CTI</strong><br>
                <span style="font-size:24px;">{total_cti}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Crear una copia para evitar mutar el DataFrame original
    df_empresas_display = df_empresas.copy()
    df_empresas_display['CUPO'] = df_empresas_display['CANTIDAD_EMPLEADOS'].apply(calculate_cupo)

    # Mostrar la tabla con columnas de igual ancho
    st.subheader("Tabla de Inscriptos por Empresa")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(inscriptos_por_empresa, hide_index=True)
    with col2:
        df_display = df_empresas_display[['N_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO']].drop_duplicates()
        st.dataframe(df_display, hide_index=True)

    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        # Agrupamos los datos por empresa y puesto de empleo, sumando la cantidad de empleados
        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()

        # Filtramos para mostrar solo las 10 empresas con mayor cantidad de empleados
        top_10_empresas = df_puesto_agg.groupby('N_EMPRESA')['CANTIDAD_EMPLEADOS'].sum().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_EMPRESA'].isin(top_10_empresas)]

        # Creación del gráfico de barras apiladas
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

        # Agrupamos los datos por puesto de empleo y contamos las apariciones
        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')

        # Convertimos los datos en un diccionario para la nube de palabras
        word_freq = dict(zip(conteo_puestos['N_PUESTO_EMPLEO'], conteo_puestos['Conteo']))

        if word_freq:
            # Generamos la nube de palabras
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)

            # Mostramos la nube de palabras en Streamlit
            st.subheader("Nube de Palabras de Apariciones por Puesto de Empleo")
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis("off")
            st.pyplot(plt)
        else:
            st.warning("No se pudieron generar datos para la nube de palabras.")
    
    # Agrupar y contar la cantidad de CUIL por empresa
    df_cuil_por_empresa_sorted = df_empresas_seleccionadas.groupby(['RAZON_SOCIAL']).agg({'CUIL': 'count'}).reset_index()
    df_cuil_por_empresa_sorted.columns = ['Empresa', 'Cantidad de CUIL']
    df_cuil_por_empresa_sorted = df_cuil_por_empresa_sorted.sort_values(by='Cantidad de CUIL', ascending=False)

    # Mostramos la tabla ordenada
    st.subheader("Empresas elegidas  por  CUIL")
    st.dataframe(df_cuil_por_empresa_sorted, hide_index=True)

