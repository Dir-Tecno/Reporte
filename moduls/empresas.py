import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import plotly.express as px



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


def show_companies(df_empresas, geojson_data):
    # Asegúrate de que las columnas numéricas sean del tipo correcto
    df_empresas['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_empresas['CANTIDAD_EMPLEADOS'], errors='coerce')
    df_empresas['CANTIDAD_EMPLEADOS'] = df_empresas['CANTIDAD_EMPLEADOS'].fillna(0)
    df_empresas['VACANTES'] = pd.to_numeric(df_empresas['VACANTES'], errors='coerce')
    df_empresas['VACANTES'] = df_empresas['VACANTES'].fillna(0)

    # Calcular la columna 'CUPO'
    df_empresas['CUPO'] = df_empresas.apply(lambda row: calculate_cupo(row['CANTIDAD_EMPLEADOS'], row['EMPLEADOR'], row['ADHERIDO']), axis=1)

    # Filtrar por CUIT único y eliminar duplicados
    df_display = df_empresas[['N_LOCALIDAD','N_DEPARTAMENTO', 'CUIT', 'N_EMPRESA', 'NOMBRE_TIPO_EMPRESA','ADHERIDO','CANTIDAD_EMPLEADOS', 'VACANTES', 'CUPO']].drop_duplicates(subset='CUIT')
    df_display = df_display.sort_values(by='CUPO', ascending=False).reset_index(drop=True)

    # Filtrar empresas adheridas al PPP 2024
    df_empresas_puestos = df_empresas[df_empresas['ADHERIDO'] == 'PPP - PROGRAMA PRIMER PASO [2024]'].copy()

    if not df_empresas_puestos.empty:
        st.markdown("### Programa Primer Paso - PERFIL de la demanda por categorías")

        with st.expander("Selecciona los departamentos (haz clic para expandir)"):
            departamentos_unicos = df_empresas_puestos['N_DEPARTAMENTO'].unique()
            departamentos_seleccionados = st.multiselect(
                label="Selecciona departamentos",
                options=departamentos_unicos,
                default=departamentos_unicos.tolist(),
                help='Mantén presionada la tecla Ctrl (o Cmd en Mac) para seleccionar múltiples opciones.',
                label_visibility="collapsed"
            )

        df_empresas_puestos = df_empresas_puestos[df_empresas_puestos['N_DEPARTAMENTO'].isin(departamentos_seleccionados)]
        
        df_puesto_agg = df_empresas_puestos.groupby(['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA']).agg({'CUIT': 'nunique'}).reset_index()
        top_10_categorias = df_puesto_agg.groupby('N_CATEGORIA_EMPLEO')['CUIT'].nunique().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_CATEGORIA_EMPLEO'].isin(top_10_categorias)]

        st.markdown("""<div style='padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; background-color: #f8f9fa;margin-top: 10px; font-size: 0.9em;color: #505050;'>Este gráfico representa las empresas adheridas al programa PPP, que cargaron el PERFIL de su demanda, expresado en categorias.</div>""", unsafe_allow_html=True)
        
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CUIT:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_CATEGORIA_EMPLEO:N', title='Categoría de Empleo', sort='-x'),
            color=alt.Color('NOMBRE_TIPO_EMPRESA:N', title='Tipo de Empresa'),
            tooltip=['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA', 'CUIT']
        ).properties(width=600, height=400)
        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

    st.markdown("<hr style='border: 1px solid #e0e0e0; margin: 20px 0;'>", unsafe_allow_html=True)

    # Métricas y tabla final
    empresas_adh = df_display['CUIT'].nunique()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="Empresas Adheridas", value=empresas_adh)

    with col2:
        st.markdown("""<div style='padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; background-color: #f8f9fa;margin-top: 10px; font-size: 0.9em;color: #505050;'>Las empresas en esta tabla se encuentran adheridas a uno o más programas de empleo, han cumplido con los requisitos establecidos y han proporcionado sus datos a través de los registros de programasempleo.cba.gov.ar</div>""", unsafe_allow_html=True)

    # Mostrar el DataFrame sin formato especial
    st.dataframe(df_display, hide_index=True)  
