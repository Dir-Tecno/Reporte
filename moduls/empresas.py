import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io


def calculate_cupo(cantidad_empleados, empleador, adherido):
    # Condición para el programa PPP
    if adherido == "PPP - PROGRAMA PRIMER PASO [2024]":
        if cantidad_empleados < 1:
            return 0
        elif cantidad_empleados <= 5:
            return 1
        elif cantidad_empleados <= 10:
            return 2
        elif cantidad_empleados <= 25:
            return 3
        elif cantidad_empleados <= 50:
            return math.ceil(0.2 * cantidad_empleados)
        else:
            return math.ceil(0.1 * cantidad_empleados)

    # Condición para el programa EMPLEO +26
    elif adherido == "EMPLEO +26":
        if empleador == 'N':
            return 1
        if cantidad_empleados < 1:
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
    df_empresas['CUPO'] = df_empresas.apply(lambda row: calculate_cupo(row['CANTIDAD_EMPLEADOS'], row['EMPLEADOR'], row['ADHERIDO']), axis=1)

    # Filtrar por CUIT único y eliminar duplicados
    df_display = df_empresas[['N_LOCALIDAD','N_DEPARTAMENTO', 'CUIT', 'N_EMPRESA', 'NOMBRE_TIPO_EMPRESA','N_CATEGORIA_EMPLEO','ADHERIDO','CANTIDAD_EMPLEADOS', 'VACANTES', 'CUPO', 'IMP GANANCIAS', 'IMP IVA', 'MONOTRIBUTO', 'INTEGRANTE', 'EMPLEADOR', 'ACTIVIDAD MONOTRIBUTO']].drop_duplicates(subset='CUIT')
    df_display = df_display.sort_values(by='CUPO', ascending=False).reset_index(drop=True)

    # Asegúrate de que las columnas relevantes sean numéricas
    df_display['CUIT'] = pd.to_numeric(df_display['CUIT'], errors='coerce')
    df_display['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_display['CANTIDAD_EMPLEADOS'], errors='coerce')
    df_display['CUPO'] = pd.to_numeric(df_display['CUPO'], errors='coerce')
    df_display['VACANTES'] = pd.to_numeric(df_display['VACANTES'], errors='coerce')
    # Filtrar empresas adheridas al PPP 2024
    df_empresas_puestos = df_empresas[df_empresas['ADHERIDO'] == 'PPP - PROGRAMA PRIMER PASO [2024]'].copy()


    # Resto del código de visualización
    if not df_empresas_puestos.empty:
        st.markdown("### Programa Primer Paso - PERFIL de la demanda por categorías")

        # Añadir un filtro por N_DEPARTAMENTO
        departamentos_unicos = df_empresas_puestos['N_DEPARTAMENTO'].unique()
        departamentos_seleccionados = st.multiselect(
            'Selecciona los departamentos:',
            options=departamentos_unicos,
            default=departamentos_unicos.tolist()  # Por defecto, selecciona todos
        )

        # Filtrar df_empresas_puestos según los departamentos seleccionados
        df_empresas_puestos = df_empresas_puestos[df_empresas_puestos['N_DEPARTAMENTO'].isin(departamentos_seleccionados)]
        
        #N_EMPRESA
        #CUIT
        #N_LOCALIDAD
        #N_DEPARTAMENTO
        #CANTIDAD_EMPLEADOS
        #ID_TIPO_EMPRESA
        #NOMBRE_TIPO_EMPRESA
        #N_PUESTO_EMPLEO
        #N_CATEGORIA_EMPLEO
        #N_PERFIL
        #CUPO

        # Botón para descargar el DataFrame como Excel
        #buffer = io.BytesIO()
        #with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        #    df_empresas_puestos.to_excel(writer, sheet_name='Empresas_Puestos', index=False)
        
        #st.download_button(
        #    label="📥 Descargar Perfiles de Empresas PPP",
        #    data=buffer.getvalue(),
        #    file_name="empresas_puestos.xlsx",
        #    mime="application/vnd.ms-excel"
        #)
        # Agrupación para gráfico de barras apiladas
        df_puesto_agg = df_empresas_puestos.groupby(['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA']).agg({'CUIT': 'nunique'}).reset_index()
        top_10_categorias = df_puesto_agg.groupby('N_CATEGORIA_EMPLEO')['CUIT'].nunique().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_CATEGORIA_EMPLEO'].isin(top_10_categorias)]
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
            Este gráfico representa las empresas adheridas al programa PPP, que cargaron el PERFIL de su demanda, expresado en categorias.
            </div>
        """, unsafe_allow_html=True)
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CUIT:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_CATEGORIA_EMPLEO:N', title='Empresa', sort='-x'),
            color=alt.Color('NOMBRE_TIPO_EMPRESA:N', title='Tipo de Empresa'),
            tooltip=['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA', 'CUIT']
        ).properties(width=600, height=400)
        st.altair_chart(stacked_bar_chart_2, use_container_width=True)


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




   
