import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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

    # Agregar la columna 'CUPO' si no existe
    if 'CUPO' not in df_empresas.columns:
        df_empresas['CUPO'] = df_empresas['CANTIDAD_EMPLEADOS'].apply(calculate_cupo)

    # Métricas de adhesiones
    total_empresas = df_empresas['CUIT'].nunique()
    st.metric(label="Empresas Adheridas", value=total_empresas)

    # Filtrar inscriptos con ID_EST_FICHA = 8
    df_inscriptos = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 8] 
    total_inscriptos = df_inscriptos.shape[0]

    # Mostrar tablas al inicio en dos columnas (2,2)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tabla de Inscriptos por Empresa")
        df_display = df_empresas[['N_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO']].drop_duplicates()
        st.dataframe(df_display, hide_index=True)
    with col2:
        st.subheader("Empresas elegidas por CUIL")
        df_cuil_por_empresa_sorted = df_empresas_seleccionadas.groupby('RAZON_SOCIAL').agg({'CUIL': 'count'}).reset_index()
        df_cuil_por_empresa_sorted.columns = ['Empresa', 'Cantidad de CUIL']
        df_cuil_por_empresa_sorted = df_cuil_por_empresa_sorted.sort_values(by='Cantidad de CUIL', ascending=False)
        st.dataframe(df_cuil_por_empresa_sorted, hide_index=True)

    # Verificar si hay empresas para mostrar
    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        # Agrupar por empresa y puesto de empleo
        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()

        # Filtrar top 10 empresas con más empleados
        top_10_empresas = df_puesto_agg.groupby('N_EMPRESA')['CANTIDAD_EMPLEADOS'].sum().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_EMPRESA'].isin(top_10_empresas)]

        # Crear gráfico de barras apiladas
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

        # Generar nube de palabras
        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')
        word_freq = dict(zip(conteo_puestos['N_PUESTO_EMPLEO'], conteo_puestos['Conteo']))

        if word_freq:
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)
            st.subheader("Nube de Palabras de Apariciones por Puesto de Empleo")
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis("off")
            st.pyplot(plt)
        else:
            st.warning("No se pudieron generar datos para la nube de palabras.")

    # Agrupar y contar CUIL por empresa
    df_cuil_por_empresa_sorted = df_empresas_seleccionadas.groupby('RAZON_SOCIAL').agg({'CUIL': 'count'}).reset_index()
    df_cuil_por_empresa_sorted.columns = ['Empresa', 'Cantidad de CUIL']
    df_cuil_por_empresa_sorted = df_cuil_por_empresa_sorted.sort_values(by='Cantidad de CUIL', ascending=False)

    # Agrupar y contar inscriptos por empresa
    inscriptos_por_empresa = df_inscriptos.groupby('RAZON_SOCIAL')['ID_FICHA'].count().reset_index(name='Cantidad de Inscriptos')
    inscriptos_por_empresa = inscriptos_por_empresa.sort_values(by='Cantidad de Inscriptos', ascending=False)

    # Gráfico de inscriptos por empresa
    st.subheader("Cantidad de Inscriptos por Empresa")
    st.metric(label="Inscriptos/Matchs", value=total_inscriptos)
    empresa_chart = alt.Chart(inscriptos_por_empresa).mark_bar().encode(
        y=alt.Y('RAZON_SOCIAL:N', title='Empresa', sort='-x'),
        x=alt.X('Cantidad de Inscriptos:Q', title='Cantidad de Inscriptos'),
        color=alt.Color('RAZON_SOCIAL:N', legend=None)
    ).properties(width=600, height=400)

    st.altair_chart(empresa_chart, use_container_width=True)

  
