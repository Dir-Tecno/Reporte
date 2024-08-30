import streamlit as st
import pandas as pd
import altair as alt
import math

def calculate_cupo(cantidad_empleados):
    if cantidad_empleados <= 7:
        return math.floor(2)
    elif cantidad_empleados <= 30:
        return math.floor(0.2 * cantidad_empleados)
    elif cantidad_empleados <= 165:
        return math.floor(0.15 * cantidad_empleados)
    elif cantidad_empleados <= 535:
        return math.floor(0.1 * cantidad_empleados)
    else:
        return math.floor(0.1 * cantidad_empleados)

def show_companies(df_empresas, file_date):
    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Empresas Adheridas", value=total_empresas)

    # Calcular la columna 'CUPO'
    df_empresas['CUPO'] = df_empresas['CANTIDAD_EMPLEADOS'].apply(calculate_cupo)

    if st.button("Mostrar empresas"):
        # Mostrar la tabla con columnas de igual ancho
        df_display = df_empresas[['N_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO']].drop_duplicates()
        st.dataframe(df_display,hide_index=True, width=800, height=400)  # Ajusta el ancho y la altura de la tabla según tus necesidades

    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()

        stacked_bar_chart_2 = alt.Chart(df_puesto_agg).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

        # Gráfico de aparición de puestos
        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')
        conteo_puestos['Proporcion'] = conteo_puestos['Conteo'] / conteo_puestos['Conteo'].sum()
        conteo_puestos['Acumulado'] = conteo_puestos['Proporcion'].cumsum()
        conteo_puestos['Acumulado'] = conteo_puestos['Acumulado'].shift(fill_value=0)
        conteo_puestos['Width'] = conteo_puestos['Proporcion']

        grafico_marimekko = alt.Chart(conteo_puestos).mark_bar().encode(
            x=alt.X('Acumulado:Q', title=None, axis=None, stack=None),
            x2='Width',
            y=alt.Y('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            color=alt.Color('N_PUESTO_EMPLEO:N', legend=None),
            tooltip=['N_PUESTO_EMPLEO', 'Conteo', 'Proporcion']
        ).properties(
            width=600,
            height=400
        )

        st.subheader("Gráfico de Marimekko de Apariciones por Puesto de Empleo")
        st.altair_chart(grafico_marimekko, use_container_width=True)

