import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def show_puestos(df_puestos):
    """
    # Resto del código de visualización
    if not df_puestos.empty:
        st.subheader("Distribución de Empleados por Empresa y Puesto")

        # Agrupación para gráfico de barras apiladas
        df_puesto_agg = df_puestos.groupby(['N_EMPRESA', 'N_PUESTO_EMPLEO']).agg({'CANTIDAD_EMPLEADOS': 'sum'}).reset_index()
        top_10_empresas = df_puesto_agg.groupby('N_EMPRESA')['CANTIDAD_EMPLEADOS'].sum().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_EMPRESA'].isin(top_10_empresas)]

        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CANTIDAD_EMPLEADOS:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_EMPRESA:N', title='Empresa', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', title='Puesto de Empleo'),
            tooltip=['N_EMPRESA', 'N_PUESTO_EMPLEO', 'CANTIDAD_EMPLEADOS']
        ).properties(width=600, height=400)
        st.altair_chart(stacked_bar_chart_2, use_container_width=True)
"""



   
