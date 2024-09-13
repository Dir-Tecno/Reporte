import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

def show_inscriptions(df_inscripciones, df_inscriptos, df_empresas_seleccionadas, file_date_inscripciones, file_date_inscriptos, file_date_empresas):
    # Convertir las fechas en inscripciones
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        df_inscripciones['FEC_INSCRIPCION'] = pd.to_datetime(df_inscripciones['FEC_INSCRIPCION'], errors='coerce')
    if 'FEC_NACIMIENTO' in df_inscripciones.columns:
        df_inscripciones['FEC_NACIMIENTO'] = pd.to_datetime(df_inscripciones['FEC_NACIMIENTO'], errors='coerce')
        df_inscripciones = df_inscripciones.dropna(subset=['FEC_INSCRIPCION', 'FEC_NACIMIENTO'])

    # Convertir la columna FER_NAC en df_inscriptos a fecha
    df_inscriptos['FER_NAC'] = pd.to_datetime(df_inscriptos['FER_NAC'], errors='coerce')
    df_inscriptos['FEC_SIST'] = pd.to_datetime(df_inscriptos['FEC_SIST'], errors='coerce')
    df_inscriptos = df_inscriptos.copy()  # Asegurarse de trabajar con una copia

    # Filtrar solo los CTI
    df_cti = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 12]

    # Filtrar solo los registros con ID_EST_FICHA = 8
    df_inscriptos = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 8]  
    

    # Pestaña inscripciones
    st.markdown("### Programas Empleo +26")
    st.write(f"Datos actualizados al: {file_date_inscripciones.strftime('%d/%m/%Y %H:%M:%S')}")

    # Filtros de fechas para inscripciones
    if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        st.sidebar.header("Filtros de Fechas")
        fecha_min, fecha_max = df_inscripciones['FEC_INSCRIPCION'].min().date(), df_inscripciones['FEC_INSCRIPCION'].max().date()
        fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & 
                                            (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
    
    if df_inscripciones.empty:
        st.write("No hay inscripciones para mostrar en el rango de fechas seleccionado.")
        return
    
    # Calcular edades en inscripciones
    fecha_actual = pd.Timestamp(datetime.now())
    df_inscripciones['Edad'] = (fecha_actual - pd.to_datetime(df_inscripciones['FEC_NACIMIENTO'])).dt.days // 365

    # Calcular edades en inscriptos
    df_inscriptos['Edad'] = (fecha_actual - df_inscriptos['FER_NAC']).dt.days // 365

    # Métricas de adhesiones
    count_26_or_less = df_inscripciones[df_inscripciones['Edad'] <= 26]['CUIL'].nunique()
    count_26_44 = df_inscripciones[(df_inscripciones['Edad'] > 26) & (df_inscripciones['Edad'] < 45)]['CUIL'].nunique()
    count_45 = df_inscripciones[df_inscripciones['Edad'] >= 45]['CUIL'].nunique()

    # Calcular personas de 45 o más años en inscriptos
    count_45_inscriptos = df_inscriptos[df_inscriptos['Edad'] >= 45].shape[0]


    # Calcular el número de CUIL únicos
    unique_cuil_count = df_inscriptos['CUIL'].nunique()
    unique_cuil_cuit = df_empresas_seleccionadas['CUIL'].nunique()


    # Filtrar inscripciones para los departamentos específicos y que tengan menos de 45 años
    df_dept_specific = df_inscriptos[
        (df_inscriptos['N_DEPARTAMENTO'].isin([
            'PRESIDENTE ROQUE SAENZ PEÑA', 
            'GENERAL ROCA',
            "RIO SECO",
            "TULUMBA",
            "POCHO",
            "SAN JAVIER",
            "SAN ALBERTO",
            "MINAS",
            "CRUZ DEL EJE",
            "TOTORAL",
            "SOBREMONTE",
            "ISCHILIN"
        ])) & (df_inscriptos['Edad'] < 45)
    ]

    total_dept_specific = df_dept_specific.shape[0]

    # Cálculo total
    total_inscripciones = df_inscripciones.shape[0]
    total_inscriptos = df_inscriptos.shape[0]
    total_cti = df_cti['CUIL'].nunique()
    # Mostrar las métricas en columnas
    col1, col3, col4, col5, col6, col7 = st.columns(6)
    with col1:
        st.metric(label="Adhesiones/postulantes", value=total_inscripciones-count_26_or_less)
    with col3:
        st.metric(label="Entre 26 y 44 años", value=count_26_44)
    with col4:
        st.metric(label="45 años o más", value=count_45)
    with col5:
        st.metric(label="Personas con CUIT", value=unique_cuil_cuit)    
    with col6:
        st.markdown(
            f"""
            <div style="background-color:rgb(255 209 209);padding:10px;border-radius:5px;">
                <strong>CTI</strong><br>
                <span style="font-size:24px;">{total_cti}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Añadir una sección de métricas con título "Matcheos"
    st.markdown("### Matcheos")

    # Crear un DataFrame con dos métricas
    data = pd.DataFrame({
        'Métrica': ['Total CTI', 'Match unicos'],
        'Cantidad': [total_cti, unique_cuil_count]  # Reemplaza estos valores con tus métricas reales
    })

    # Crear gráfico de torta (pie chart)
    pie_chart = alt.Chart(data).mark_arc().encode(
        theta=alt.Theta(field="Cantidad", type="quantitative"),
        color=alt.Color(field="Métrica", type="nominal"),
        tooltip=['Métrica', 'Cantidad']
    ).properties(
        width=400,
        height=400
    )


    # Crear las columnas para las métricas
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="Inscriptos/Match", value=df_inscriptos.shape[0])
    with col2:
        st.metric(label="Personas Únicas inscriptas (CUIL)", value=unique_cuil_count)
    with col3:
        st.metric(label="Inscriptos 45 años o más", value=count_45_inscriptos)
    with col4:
        st.metric(label="Inscriptos Zonas Favorecidas", value=total_dept_specific)
    with col5:
        st.altair_chart(pie_chart, use_container_width=True)



    # Verifica que las columnas de fecha estén presentes en los DataFrames
    if 'FEC_INSCRIPCION' in df_inscripciones.columns and 'FEC_SIST' in df_inscriptos.columns:
        # Agrupar por fecha y contar inscripciones para el primer conjunto (Inscripciones)
        inscripciones_por_fecha = df_inscripciones.groupby(df_inscripciones['FEC_INSCRIPCION'].dt.date).size().reset_index(name='Conteo')
        inscripciones_por_fecha.columns = ['Fecha', 'Conteo']
        inscripciones_por_fecha['Tipo'] = 'Adhesiones'
    
        # Agrupar por fecha y contar inscripciones para el segundo conjunto (Match)
        match_por_fecha = df_inscriptos.groupby(df_inscriptos['FEC_SIST'].dt.date).size().reset_index(name='Conteo')
        match_por_fecha.columns = ['Fecha', 'Conteo']
        match_por_fecha['Tipo'] = 'Match'

        # Agrupar por fecha y contar inscripciones para el segundo conjunto (Match)
        cti_por_fecha = df_cti.groupby(df_cti['FEC_SIST'].dt.date).size().reset_index(name='Conteo')
        cti_por_fecha.columns = ['Fecha', 'Conteo']
        cti_por_fecha['Tipo'] = 'cti'
    
        # Combinar ambos DataFrames en uno solo
        datos_combinados = pd.concat([inscripciones_por_fecha, match_por_fecha, cti_por_fecha])
    
        # Crear gráfico combinado
        st.subheader("Postulaciones y Match por Fecha")
        fecha_chart_combined = alt.Chart(datos_combinados).mark_line().encode(
            x=alt.X('Fecha:T', title='Fecha', axis=alt.Axis(format='%d/%m/%Y', tickCount='day', labelAngle=-45)),
            y=alt.Y('Conteo:Q', title='Cantidad'),
            color='Tipo:N',  # Diferenciar por tipo (Inscripciones o Match)
            tooltip=['Fecha:T', 'Conteo:Q', 'Tipo:N']
        ).properties(width=800, height=400)

        st.altair_chart(fecha_chart_combined, use_container_width=True)


        # Calcular la suma acumulada de Conteo para cada tipo
        datos_combinados['Conteo Acumulado'] = datos_combinados.groupby('Tipo')['Conteo'].cumsum()

        # Crear gráfico acumulado
        st.subheader("Conteo Acumulado por Fecha")
        fecha_chart_acumulado = alt.Chart(datos_combinados).mark_line().encode(
            x=alt.X('Fecha:T', title='Fecha', axis=alt.Axis(format='%d/%m/%Y', tickCount='day', labelAngle=-45)),
            y=alt.Y('Conteo Acumulado:Q', title='Cantidad Acumulada'),
            color='Tipo:N',  # Diferenciar por tipo (Inscripciones, Match, cti)
            tooltip=['Fecha:T', 'Conteo Acumulado:Q', 'Tipo:N']
        ).properties(width=800, height=400)
    
        # Mostrar el gráfico en Streamlit
        st.altair_chart(fecha_chart_acumulado, use_container_width=True)

    
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

    st.markdown("### por Departamentos")
    if 'N_DEPARTAMENTO' in df_inscripciones.columns:
        departamentos = df_inscripciones['N_DEPARTAMENTO'].unique()
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=departamentos)
        df_filtered_departamentos = df_inscripciones[df_inscripciones['N_DEPARTAMENTO'].isin(selected_departamento)]
    else:
        df_filtered_departamentos = df_inscripciones

    departamento_counts = df_filtered_departamentos.groupby(['N_DEPARTAMENTO', 'N_LOCALIDAD']).size().reset_index(name='Cuenta')
    departamento_counts_sorted = departamento_counts.sort_values(by='Cuenta', ascending=False)

    col1, col2 = st.columns([2, 3])
    with col2:
        st.subheader("Conteo por Departamento")
        st.altair_chart(
            alt.Chart(departamento_counts_sorted).mark_bar().encode(
                y=alt.Y('N_DEPARTAMENTO:N', title='Departamento', sort='-x'),
                x=alt.X('Cuenta:Q', title='Conteo'),
                color=alt.Color('N_DEPARTAMENTO:N', legend=None),
                tooltip=['N_DEPARTAMENTO', 'Cuenta']
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
    st.metric(label="Inscriptos/Matchs",value=total_inscriptos)
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
