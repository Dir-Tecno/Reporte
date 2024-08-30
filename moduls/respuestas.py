import streamlit as st
import pandas as pd
import altair as alt

def show_responses(df_respuestas, file_date_respuestas):
    columnas_relevantes = ["APRENDER", "DECISIONES", "INFORMACION", "EXPLICAR", "HERRAMIENTAS", "CALCULO", "INSTRUCCIONES"]

    if all(col in df_respuestas.columns for col in columnas_relevantes) and 'ID_INSCRIPCION' in df_respuestas.columns:
        df_respuestas = df_respuestas[columnas_relevantes + ["ID_INSCRIPCION"]]

        df_promedios = df_respuestas.groupby("ID_INSCRIPCION").mean().reset_index()
        df_promedios_melted = df_promedios.drop("ID_INSCRIPCION", axis=1).mean().reset_index()
        df_promedios_melted.columns = ['Aspecto', 'Promedio']
        df_promedios_melted['Promedio'] = df_promedios_melted['Promedio'].round(2)

        # Filtro por categoría si se desea (requiere una columna 'CATEGORIA' en df_respuestas)
        categorias = df_respuestas['CATEGORIA'].unique() if 'CATEGORIA' in df_respuestas.columns else []
        selected_categoria = st.selectbox("Seleccionar Categoría", categorias) if categorias else None
        
        if selected_categoria:
            df_respuestas = df_respuestas[df_respuestas['CATEGORIA'] == selected_categoria]
            
        st.subheader("Promedio por Aspecto")
        total_respondieron = df_respuestas.shape[0]
        st.metric(label="45 años o más", value=total_respondieron)
        bar_chart_aspectos = alt.Chart(df_promedios_melted).mark_bar().encode(
            y=alt.Y('Aspecto:N', title='Aspecto', sort='-x'),
            x=alt.X('Promedio:Q', title='Promedio'),
            color=alt.Color('Aspecto:N', legend=None),  # Usa el esquema de color por defecto
            tooltip=['Aspecto:N', 'Promedio:Q']
        ).properties(width=800, height=400)

        text = bar_chart_aspectos.mark_text(align='left', baseline='middle', dx=3).encode(
            text=alt.Text('Promedio:Q', format='.2f')
        )
        final_chart = bar_chart_aspectos + text

        st.altair_chart(final_chart, use_container_width=True)

        st.subheader("Promedios de Aspectos")
        st.dataframe(df_promedios_melted, hide_index=True)
    else:
        st.error("Faltan columnas necesarias en el DataFrame. Verifica el archivo CSV.")
