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

def show_companies(df_empresas, df_inscriptos, df_empresas_seleccionadas, file_date):
    total_empresas = df_empresas['CUIT'].nunique()
    
    # Agrupar y contar la cantidad de inscriptos por empresa
    inscriptos_por_empresa = df_inscriptos.groupby('RAZON_SOCIAL')['ID_FICHA'].count().reset_index(name='Inscriptos')
    inscriptos_por_empresa = inscriptos_por_empresa.sort_values(by='Inscriptos', ascending=False)
    
    # Calcular la columna 'CUPO'
    df_empresas['CUPO'] = df_empresas['CANTIDAD_EMPLEADOS'].apply(calculate_cupo)

    # Asegurarse de que las columnas de merge tengan el mismo tipo
    df_empresas['CUIT'] = df_empresas['CUIT'].astype(str)

    # Agrupar el DataFrame por CUIT de empresa y contar
    empresas_agrupado = df_empresas.groupby('CUIT').size().reset_index(name='Recuento')
    merged_df = empresas_agrupado.merge(df_inscriptos, left_on='CUIT', right_on='EMP_CUIT', how='left')
    empresas_sin_match = merged_df[merged_df['ID_EMP'].isna()]
    empresas_sin_match_detalles = empresas_sin_match.merge(df_empresas, left_on='CUIT', right_on='CUIT', how='left')
    
    empresas_sin_match_detalles = empresas_sin_match_detalles.groupby('CUIT').first().reset_index()

    
    # Ahora mostrar la métrica de empresas sin match
    total_empresas_sin_match = empresas_sin_match_detalles.shape[0]
    
    # Colocar las dos métricas lado a lado
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Empresas Adheridas", value=total_empresas)
    with col2:
        st.metric(label="Empresas que no hicieron match", value=total_empresas_sin_match)

    # Mostrar las tablas
    st.subheader("Tablas de Inscriptos y Empresas sin Match")
    col3, col4 = st.columns(2)
    with col3:
        st.dataframe(inscriptos_por_empresa, hide_index=True)
    with col4:
        st.dataframe(empresas_sin_match_detalles[['N_EMPRESA', 'CUIT']], hide_index=True)

    # Mostrar tabla de detalles de empresas
    df_display = df_empresas[['N_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO']].drop_duplicates()
    st.dataframe(df_display, hide_index=True)

    # Resto del código: gráficos de distribución y nube de palabras
    if not df_empresas.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")
        df_puesto_agg = df_empresas.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS':'sum'}).reset_index()
        top_10_empresas = df_puesto_agg.groupby('N_EMPRESA')['CANTIDAD_EMPLEADOS'].sum().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_EMPRESA'].isin(top_10_empresas)]
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(height=400)

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')
        word_freq = dict(zip(conteo_puestos['N_PUESTO_EMPLEO'], conteo_puestos['Conteo']))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)
        
        st.subheader("Nube de Palabras de Apariciones por Puesto de Empleo")
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        st.pyplot(plt)


        