import streamlit as st
import pandas as pd
import altair as alt

def show_companies(df_empresas, file_date):
    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Empresas Adheridas", value=total_empresas)

    if st.button("Mostrar empresas"):
        st.dataframe(df_empresas[['N_EMPRESA', 'CANTIDAD_EMPLEADOS']].drop_duplicates(), hide_index=True)

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


        # Grafico de aparicion de puestos

        # Agrupar los datos por N_PUESTO_EMPLEO y contar las apariciones de cada puesto
        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')

        # Calcular la proporción del total para cada puesto
        conteo_puestos['Proporcion'] = conteo_puestos['Conteo'] / conteo_puestos['Conteo'].sum()

        # Calcular la posición acumulativa para las barras apiladas
        conteo_puestos['Acumulado'] = conteo_puestos['Proporcion'].cumsum()
        conteo_puestos['Acumulado'] = conteo_puestos['Acumulado'].shift(fill_value=0)

        # Definir los anchos de las barras basados en la proporción
        conteo_puestos['Width'] = conteo_puestos['Proporcion']

        # Crear un gráfico de barras apiladas donde el ancho de las barras varía según la proporción
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

        # Mostrar el gráfico en Streamlit
        st.subheader("Gráfico de Marimekko de Apariciones por Puesto de Empleo")
        st.altair_chart(grafico_marimekko, use_container_width=True)
