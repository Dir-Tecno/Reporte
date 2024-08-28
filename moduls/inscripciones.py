import streamlit as st
import pandas as pd
import altair as alt

def show_inscriptions(df_inscripciones, df_inscriptos, df_empresas_seleccionadas, file_date_inscripciones, file_date_inscriptos, file_date_empresas):
    # Convertir las fechas en inscripciones
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        df_inscripciones['FEC_INSCRIPCION'] = pd.to_datetime(df_inscripciones['FEC_INSCRIPCION'], errors='coerce')
    if 'FEC_NACIMIENTO' in df_inscripciones.columns:
        df_inscripciones['FEC_NACIMIENTO'] = pd.to_datetime(df_inscripciones['FEC_NACIMIENTO'], errors='coerce')
        df_inscripciones = df_inscripciones.dropna(subset=['FEC_INSCRIPCION', 'FEC_NACIMIENTO'])

    # Convertir las fechas en inscriptos
    df_inscriptos = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 8]  # Filtrar solo los registros con ID_EST_FICHA = 8
    
    # Pestaña inscripciones
    st.markdown("### Inscripciones Programas Empleo 2024")
    st.write(f"Datos de inscripciones actualizados al: {file_date_inscripciones.strftime('%d/%m/%Y %H:%M:%S')}")

    # Filtros de fechas para inscripciones
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        st.sidebar.header("Filtros de Fechas")
        fecha_min, fecha_max = df_inscripciones['FEC_INSCRIPCION'].min().date(), df_inscripciones['FEC_INSCRIPCION'].max().date()
        fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & 
                                            (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
        
    # Calcular edades en inscripciones
    df_inscripciones['Edad'] = (pd.Timestamp('2024-08-19') - df_inscripciones['FEC_NACIMIENTO']).dt.days // 365

    # Métricas de adhesiones
    total_inscripciones = df_inscripciones.shape[0]
    count_26_or_less = df_inscripciones[df_inscripciones['Edad'] <= 26].shape[0]
    count_26_44 = df_inscripciones[(df_inscripciones['Edad'] > 26) & (df_inscripciones['Edad'] < 45)].shape[0]
    count_45 = df_inscripciones[df_inscripciones['Edad'] >= 45].shape[0]
    total_inscriptos= df_inscriptos.shape[0] 

    # Mostrar las métricas en columnas
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label="Adhesiones", value=total_inscripciones)
    with col2:
        st.metric(label="26 años o menos", value=count_26_or_less)
    with col3:
        st.metric(label="Entre 26 y 44 años", value=count_26_44)   
    with col4:
        st.metric(label="45 años o más", value=count_45)
    with col5:
        st.metric(label="Inscriptos",value=total_inscriptos)


    # Gráfico de Inscripciones por Fecha
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
    # Agrupar por fecha y contar inscripciones
        inscripciones_por_fecha = df_inscripciones.groupby(df_inscripciones['FEC_INSCRIPCION'].dt.date).size().reset_index(name='Conteo')
        inscripciones_por_fecha.columns = ['Fecha', 'Conteo']  # Renombrar columnas para evitar problemas en el gráfico

    st.subheader("Inscripciones por Fecha")
    fecha_chart = alt.Chart(inscripciones_por_fecha).mark_line().encode(
        x=alt.X('Fecha:T', title='Fecha', axis=alt.Axis(format='%d/%m/%Y', tickCount='day', labelAngle=-45)),
        y=alt.Y('Conteo:Q', title='Cantidad de Inscripciones'),
        tooltip=['Fecha:T', 'Conteo:Q']
    ).properties(width=800, height=400)

    st.altair_chart(fecha_chart, use_container_width=True)


    # DNI por Localidad (Barras)
    if 'N_LOCALIDAD' in df_inscripciones.columns and 'N_DEPARTAMENTO' in df_inscripciones.columns:
        dni_por_localidad = df_inscripciones.groupby(['N_LOCALIDAD', 'N_DEPARTAMENTO']).size().reset_index(name='Conteo')
        dni_por_localidad['N_DEPARTAMENTO'] = dni_por_localidad['N_DEPARTAMENTO'].apply(lambda x: 'INTERIOR' if x != 'CAPITAL' else 'CAPITAL')

        dni_por_localidad_filter = st.multiselect("Filtrar por Región", dni_por_localidad['N_DEPARTAMENTO'].unique(), default=dni_por_localidad['N_DEPARTAMENTO'].unique())
        dni_por_localidad = dni_por_localidad[dni_por_localidad['N_DEPARTAMENTO'].isin(dni_por_localidad_filter)]

        top_10_localidades = dni_por_localidad.sort_values(by='Conteo', ascending=False).head(10)
        st.subheader("Top 10 de Adhesiones por Localidad")

        bar_chart_localidad = alt.Chart(top_10_localidades).mark_bar().encode(
            y=alt.Y('N_LOCALIDAD:N', title='Localidad', sort='-x'),
            x=alt.X('Conteo:Q', title='Conteo'),
            color=alt.Color('N_LOCALIDAD:N', legend=None)
        ).properties(width=600, height=400)

        text = bar_chart_localidad.mark_text(align='left', baseline='middle', dx=3).encode(text='Conteo:Q')
        final_chart = bar_chart_localidad + text
        st.altair_chart(final_chart, use_container_width=True)

    st.markdown("### Gráficos de Inscripciones por Departamentos")
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=departamentos)
        df_filtered_departamentos = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)]
    else:
        df_filtered_departamentos = df_inscripciones

    departamento_counts = df_filtered_departamentos.groupby(['N_DEPARTAMENTO', 'N_LOCALIDAD']).size().reset_index(name='Conteo de ID_INSCRIPCION')
    departamento_counts_sorted = departamento_counts.sort_values(by='Conteo de ID_INSCRIPCION', ascending=False)

    col1, col2 = st.columns([2, 3])
    with col2:
        st.subheader("Conteo por Departamento")
        st.altair_chart(
            alt.Chart(departamento_counts_sorted).mark_bar().encode(
                y=alt.Y('N_DEPARTAMENTO:N', title='Departamento', sort='-x'),
                x=alt.X('Conteo de ID_INSCRIPCION:Q', title='Conteo'),
                color=alt.Color('N_DEPARTAMENTO:N', legend=None),
                tooltip=['N_DEPARTAMENTO', 'Conteo de ID_INSCRIPCION']
            ).properties(width=900, height=500),
            use_container_width=True
        )
    with col1:
        st.subheader("Tabla de Adhesiones")
        st.dataframe(departamento_counts_sorted, hide_index=True)


    # Agrupar y contar la cantidad de inscriptos por empresa
    inscriptos_por_empresa = df_inscriptos.groupby('RAZON_SOCIAL')['ID_FICHA'].count().reset_index(name='Cantidad de Inscriptos')
    inscriptos_por_empresa = inscriptos_por_empresa.sort_values(by='Cantidad de Inscriptos', ascending=False)

    # Agrupar y contar la cantidad de CUIL por empresa
    df_cuil_por_empresa_sorted = df_empresas_seleccionadas.groupby(['RAZON_SOCIAL']).agg({'CUIL': 'count'}).reset_index()
    df_cuil_por_empresa_sorted.columns = ['RAZON_SOCIAL', 'Cantidad_CUIL']
    df_cuil_por_empresa_sorted = df_cuil_por_empresa_sorted.sort_values(by='Cantidad_CUIL', ascending=False)

    # Gráfico de cantidad de inscriptos por empresa
    st.subheader("Cantidad de Inscriptos por Empresa")
    empresa_chart = alt.Chart(inscriptos_por_empresa).mark_bar().encode(
    y=alt.Y('RAZON_SOCIAL:N', title='Empresa', sort='-x'),
    x=alt.X('Cantidad de Inscriptos:Q', title='Cantidad de Inscriptos'),
    color=alt.Color('RAZON_SOCIAL:N', legend=None)
    ).properties(width=600, height=400)

    st.altair_chart(empresa_chart, use_container_width=True)

    # Dividir en dos columnas con igual ancho
    col1, col2 = st.columns([1,1])

    with col1:
        st.subheader("Tabla de Inscriptos por Empresa")
        st.dataframe(inscriptos_por_empresa, hide_index=True)

    with col2:
        st.subheader("CUIL que seleccionaron Empresa")
        st.dataframe(df_cuil_por_empresa_sorted, hide_index=True)


    




