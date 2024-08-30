import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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

def show_companies(df_empresas, df_inscriptos, file_date):
    total_empresas = df_empresas['CUIT'].nunique()
    # Agrupar y contar la cantidad de inscriptos por empresa
    inscriptos_por_empresa = df_inscriptos.groupby('RAZON_SOCIAL')['ID_FICHA'].count().reset_index(name='Inscriptos')
    inscriptos_por_empresa = inscriptos_por_empresa.sort_values(by='Inscriptos', ascending=False)
    st.metric(label="Empresas Adheridas", value=total_empresas)

    # Calcular la columna 'CUPO'
    df_empresas['CUPO'] = df_empresas['CANTIDAD_EMPLEADOS'].apply(calculate_cupo)

    # Mostrar la tabla con columnas de igual ancho
    st.subheader("Tabla de Inscriptos por Empresa")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(inscriptos_por_empresa, hide_index=True)
    with col2:
        df_display = df_empresas[['N_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO']].drop_duplicates()
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

        # Generamos la nube de palabras
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)

        # Mostramos la nube de palabras en Streamlit
        st.subheader("Nube de Palabras de Apariciones por Puesto de Empleo")
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        st.pyplot(plt)

