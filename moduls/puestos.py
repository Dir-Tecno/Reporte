import streamlit as st
import pandas as pd
import altair as alt

def show_puestos(df_puestos, df_empresas,df_inscriptos):
    
    # Verificar si df_puestos no está vacío
    if not df_puestos.empty:
        st.subheader("Distribución de Categorías de Empleo por Estado de Ficha")

        # ** Análisis de Categorías de Empleo por Estado de Ficha **

        # Asegurarse de que las categorías de empleo sean una lista de categorías separadas por coma
        df_puestos['CATEGORIAS_EMPLEO'] = df_puestos['CATEGORIAS_EMPLEO'].str.split(',')

        # Explosión de las categorías para que cada categoría ocupe una fila
        categorias_explotadas = df_puestos.explode('CATEGORIAS_EMPLEO')
        
        # Limpieza de espacios extra en las categorías
        categorias_explotadas['CATEGORIAS_EMPLEO'] = categorias_explotadas['CATEGORIAS_EMPLEO'].str.strip()

        # Contar la frecuencia de cada categoría por estado de ficha
        categoria_estado_count = categorias_explotadas.groupby(['N_ESTADO_FICHA', 'CATEGORIAS_EMPLEO']).size().reset_index(name='Frecuencia')

        # Filtrar para mostrar solo las categorías con más de 5 fichas (ajustar según sea necesario)
        categoria_estado_count_filtered = categoria_estado_count[categoria_estado_count['Frecuencia'] > 5]

        # Para evitar sobrecargar el gráfico, mostrar solo las categorías con más frecuencia
        categoria_estado_count_filtered = categoria_estado_count_filtered.nlargest(10, 'Frecuencia')

        # Crear gráfico general de barras apiladas por estado de ficha y categoría de empleo
        categoria_estado_chart = alt.Chart(categoria_estado_count_filtered).mark_bar().encode(
            x=alt.X('Frecuencia:Q', title='Frecuencia de Categorías'),
            y=alt.Y('CATEGORIAS_EMPLEO:N', title='Categoría de Empleo'),
            color=alt.Color('N_ESTADO_FICHA:N', title='Estado de Ficha'),
            tooltip=['N_ESTADO_FICHA', 'CATEGORIAS_EMPLEO', 'Frecuencia']
        ).properties(width=600, height=400)

        st.altair_chart(categoria_estado_chart, use_container_width=True)

        # Desagregar el gráfico por estado de ficha
        for estado in categoria_estado_count_filtered['N_ESTADO_FICHA'].unique():
            st.subheader(f"Distribución de Categorías de Empleo para el Estado de Ficha: {estado}")
            df_estado = categoria_estado_count_filtered[categoria_estado_count_filtered['N_ESTADO_FICHA'] == estado]
            chart_estado = alt.Chart(df_estado).mark_bar().encode(
                x=alt.X('Frecuencia:Q', title='Frecuencia de Categorías'),
                y=alt.Y('CATEGORIAS_EMPLEO:N', title='Categoría de Empleo'),
                color=alt.Color('CATEGORIAS_EMPLEO:N', title='Categoría de Empleo'),
                tooltip=['CATEGORIAS_EMPLEO', 'Frecuencia']
            ).properties(width=600, height=400)

            st.altair_chart(chart_estado, use_container_width=True)

  
    # Verificar si df_empresas y df_inscriptos no están vacíos
    if not df_empresas.empty and not df_inscriptos.empty:
        st.subheader("Tabla de Empresas con Fichas por Estado y Cupo Disponible")

        # Limpiar los CUITs
        df_empresas['CUIT'] = df_empresas['CUIT'].str.replace('-', '', regex=False).fillna('')
        df_inscriptos['EMP_CUIT'] = df_inscriptos['EMP_CUIT'].str.replace('-', '', regex=False).fillna('')

        # Unir los dataframes
        df_merged = pd.merge(df_inscriptos, df_empresas, left_on='EMP_CUIT', right_on='CUIT', how='left')

        # Filtrar los estados relevantes
        estados_relevantes = [
            "INSCRIPTO NO ACEPTADO", "POSTULANTE SIN EMPRESA", "INSCRIPTO - CTI", 
            "RECHAZO FORMAL", "ADHERIDO", "INSCRIPTO", "BENEFICIARIO- CTI", "BENEFICIARIO"
        ]
        estados_cupo = ["INSCRIPTO - CTI", "INSCRIPTO", "BENEFICIARIO- CTI", "BENEFICIARIO"]

        # Filtrar solo los estados relevantes
        df_filtrado = df_merged[df_merged['N_ESTADO_FICHA'].isin(estados_relevantes)]

        # Agrupar para contar fichas por estado y empresa
        df_fichas_por_estado = df_filtrado.groupby(['N_EMPRESA', 'N_ESTADO_FICHA']).agg(
            cantidad_fichas=('EMP_CUIT', 'nunique')  # CUITs únicos por estado y empresa
        ).reset_index()

        # Calcular las fichas que afectan el cupo
        df_fichas_cupo = df_filtrado[df_filtrado['N_ESTADO_FICHA'].isin(estados_cupo)].groupby('N_EMPRESA').agg(
            fichas_afectan_cupo=('EMP_CUIT', 'nunique')  # CUITs únicos en estados relevantes
        ).reset_index()

        # Unir con los datos de cupo
        df_cupo = pd.merge(df_fichas_cupo, df_empresas[['N_EMPRESA', 'CUPO']], on='N_EMPRESA', how='left')

        # Calcular el cupo disponible y evitar valores negativos
        df_cupo['cupo_disponible'] = df_cupo['CUPO'] - df_cupo['fichas_afectan_cupo']
        df_cupo['cupo_disponible'] = df_cupo['cupo_disponible'].clip(lower=0)

        # Unir el cálculo del cupo con las fichas por estado
        df_resultado = pd.merge(df_fichas_por_estado, df_cupo[['N_EMPRESA', 'CUPO', 'cupo_disponible']], on='N_EMPRESA', how='left')

        # Consolidar la salida
        df_resultado = df_resultado.drop_duplicates(subset=['N_EMPRESA', 'N_ESTADO_FICHA'])

        # Mostrar la tabla final
        st.write("Tabla con la cantidad de fichas por estado, cupo y cupo disponible por empresa:")
        st.dataframe(df_resultado[['N_EMPRESA', 'N_ESTADO_FICHA', 'cantidad_fichas', 'CUPO', 'cupo_disponible']])









