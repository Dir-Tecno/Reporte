import streamlit as st
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

        conteo_puestos = df_empresas.groupby('N_PUESTO_EMPLEO').size().reset_index(name='Conteo')
        conteo_puestos = conteo_puestos.sort_values(by='Conteo', ascending=False).reset_index(drop=True)

        st.subheader("Conteo de Apariciones por Puesto de Empleo")
        st.dataframe(conteo_puestos, hide_index=True)

        grafico_puestos = alt.Chart(conteo_puestos).mark_bar().encode(
            x=alt.X('Conteo:Q', title='Conteo'),
            y=alt.Y('N_PUESTO_EMPLEO:N', title='Puesto de Empleo', sort='-x'),
            color=alt.Color('N_PUESTO_EMPLEO:N', legend=None),
            tooltip=['N_PUESTO_EMPLEO', 'Conteo']
        ).properties(width=600, height=400)

        st.subheader("Gráfico de Barras de Apariciones por Puesto de Empleo")
        st.altair_chart(grafico_puestos, use_container_width=True)
