import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def calculate_cupo(cantidad_empleados, empleador):
    if empleador == 'N':
        return 1
    if cantidad_empleados <= 1:
        return 1 
    elif cantidad_empleados <= 7:
        return 2
    elif cantidad_empleados <= 30:
        return math.ceil(0.2 * cantidad_empleados)
    elif cantidad_empleados <= 165:
        return math.ceil(0.15 * cantidad_empleados)
    else:
        return math.ceil(0.1 * cantidad_empleados)

def show_companies(df_empresas):
    # Asegúrate de que 'CANTIDAD_EMPLEADOS' sea numérico
    df_empresas['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_empresas['CANTIDAD_EMPLEADOS'], errors='coerce')

    # Reemplazar valores nulos con 0 o un valor adecuado
    df_empresas['CANTIDAD_EMPLEADOS'] = df_empresas['CANTIDAD_EMPLEADOS'].fillna(0)
        # Convertir ACTIVIDAD MONOTRIBUTO a entero eliminando el punto decimal
    df_empresas['ACTIVIDAD MONOTRIBUTO'] = pd.to_numeric(
        df_empresas['ACTIVIDAD MONOTRIBUTO'].astype(str).str.replace('.', ''), 
        errors='coerce'
    ).fillna(0).astype(int)

    # Calcular la columna 'CUPO' usando los datos en `df_empresas`
    df_empresas['CUPO'] = df_empresas.apply(lambda row: calculate_cupo(row['CANTIDAD_EMPLEADOS'], row['EMPLEADOR']), axis=1)

    # Filtrar por CUIT único y eliminar duplicados
    df_display = df_empresas[['N_LOCALIDAD','N_DEPARTAMENTO', 'CUIT', 'N_EMPRESA', 'NOMBRE_TIPO_EMPRESA','CANTIDAD_EMPLEADOS', 'VACANTES', 'CUPO', 'IMP GANANCIAS', 'IMP IVA', 'MONOTRIBUTO', 'INTEGRANTE', 'EMPLEADOR', 'ACTIVIDAD MONOTRIBUTO']].drop_duplicates(subset='CUIT')
    df_display = df_display.sort_values(by='CUPO', ascending=False).reset_index(drop=True)

    # Asegúrate de que las columnas relevantes sean numéricas
    df_display['CUIT'] = pd.to_numeric(df_display['CUIT'], errors='coerce')
    df_display['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_display['CANTIDAD_EMPLEADOS'], errors='coerce')
    df_display['CUPO'] = pd.to_numeric(df_display['CUPO'], errors='coerce')
    df_display['VACANTES'] = pd.to_numeric(df_display['VACANTES'], errors='coerce')
    # ... otras columnas que necesiten conversión

    # Crear subtítulo y métrica de empresas adheridas con aclaración en el label
    empresas_adh = df_display['CUIT'].nunique()

    # Crear dos columnas
    col1, col2 = st.columns([1, 2])  # La proporción [1, 2] da más espacio al texto explicativo

    # Métrica en la primera columna
    with col1:
        st.metric(label="Empresas Adheridas", value=empresas_adh)

    # Texto explicativo en la segunda columna, con estilo
    with col2:
        st.markdown("""
            <div style='
                padding: 15px; 
                border-radius: 5px; 
                border: 1px solid #e0e0e0; 
                background-color: #f8f9fa;
                margin-top: 10px;
                font-size: 0.9em;
                color: #505050;
            '>
            Las empresas en esta tabla se encuentran adheridas a uno o más programas de empleo, 
            han cumplido con los requisitos establecidos y han proporcionado sus datos 
            a través de los registros de programasempleo.cba.gov.ar
            </div>
        """, unsafe_allow_html=True)

    # Mostrar la tabla de empresas adheridas
    df_display = df_display.style.format({
        'CUIT': '{:.0f}',
        'CANTIDAD_EMPLEADOS': '{:.0f}',
        'CUPO': '{:.0f}',
        'VACANTES': '{:.0f}',
        'Inscriptos': '{:.0f}',
        'Inscriptos_para_Aceptar': '{:.0f}'
    })

    st.dataframe(df_display, hide_index=True)

     # Filtro y gráfico de distribución por tipo de empresa
    # Obtener lista única de departamentos y añadir opción "Todos"
    departamentos = ["Todos"] + sorted(df_empresas['N_DEPARTAMENTO'].unique())

    # Crear selectbox para departamentos
    selected_departamento = st.selectbox("Seleccione un Departamento:", departamentos)

    # Filtrar DataFrame basado en la selección
    if selected_departamento == "Todos":
        df_filtered = df_empresas
        titulo_grafico = ""
    else:
        df_filtered = df_empresas[df_empresas['N_DEPARTAMENTO'] == selected_departamento]
        titulo_grafico = f"en {selected_departamento}"

    # Primero eliminar duplicados de CUIT
    df_filtered_unique = df_filtered.drop_duplicates(subset=['CUIT'])

    # Luego hacer el agrupamiento
    df_tipo_agrupado = df_filtered_unique.groupby('NOMBRE_TIPO_EMPRESA').size().reset_index(name='Cantidad')
    df_tipo_agrupado['Porcentaje'] = (df_tipo_agrupado['Cantidad'] / df_tipo_agrupado['Cantidad'].sum()) * 100

    chart = alt.Chart(df_tipo_agrupado).mark_bar().encode(
        x=alt.X('Porcentaje:Q', title='Porcentaje de Empresas Únicas'),
        y=alt.Y('NOMBRE_TIPO_EMPRESA:N', title='Tipo de Empresa', sort='-x'),
        tooltip=[
            'NOMBRE_TIPO_EMPRESA', 
            alt.Tooltip('Cantidad:Q', title='Empresas Únicas', format=','),
            alt.Tooltip('Porcentaje:Q', title='% del Total', format='.1f')
        ]
    ).properties(
        width=600, 
        height=400, 
        title=f"Distribución de Empresas Únicas por Tipo en {titulo_grafico}"
    )

    st.altair_chart(chart, use_container_width=True)






   
