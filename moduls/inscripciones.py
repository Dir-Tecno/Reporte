import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io
import pydeck as pdk
import plotly.express as px



def show_inscriptions(df_inscripciones, df_inscriptos, df_poblacion, file_date_inscripciones, file_date_inscriptos, file_date_poblacion, geojson_data):
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

    # df_descarga_cti
    df_cti_descarga = df_inscriptos[df_inscriptos['ID_EST_FIC'].isin([12, 13, 14])]

    # Filtrar solo los BENEFICIARIOS CTI
    df_cti_benef = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 13]

    # Filtrar solo los BENEFICIARIOS CTI
    df_cti_alta = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 14]

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

    # Calcular edades en inscriptos
    df_inscriptos['Edad'] = (fecha_actual - df_inscriptos['FER_NAC']).dt.days // 365

    # Calcular personas de 45 o más años en inscriptos
    count_45_inscriptos = df_inscriptos[df_inscriptos['Edad'] >= 45].shape[0]
    # Calcular personas de entre 26 y 44 en inscriptos
    count_26_44 = df_inscriptos[(df_inscriptos['Edad'] > 26) & (df_inscriptos['Edad'] < 45)]['CUIL'].nunique()

    # Calcular el número de CUIL únicos
    unique_cuil_count = df_inscriptos['CUIL'].nunique()
     
    # Filtrar inscriptos para los departamentos específicos y que tengan menos de 45 años
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
    #total_inscripciones = df_inscripciones.shape[0]
    total_inscriptos = df_inscriptos.shape[0]
    total_cti = df_cti['CUIL'].nunique()
    total_cti_benef = df_cti_benef['CUIL'].nunique()
    total_cti_alta = df_cti_alta['CUIL'].nunique()

    st.markdown("### CTI")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="background-color:rgb(255 209 209);padding:10px;border-radius:5px;">
                <strong>CTI INSCR.</strong><br>
                <span style="font-size:24px;">{total_cti}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="background-color:rgb(173, 216, 230);padding:10px;border-radius:5px;">
                <strong>CTI VALIDADOS</strong><br>
                <span style="font-size:24px;">{total_cti_benef}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style="background-color:rgb(165 228 156);padding:10px;border-radius:5px;">
                <strong>CTI ALTA TEMPRANA</strong><br>
                <span style="font-size:24px;">{total_cti_alta}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    

    # Añadir una sección de métricas con título "Matcheos"
    st.markdown("### Matcheos")

        # Crear las columnas para las métricas
    col1,col2, col3, col4,col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div style="background-color:white;padding:10px;border-radius:5px;">
                <strong>Fichas/Inscriptos</strong><br>
                <span style="font-size:24px;">{df_inscriptos.shape[0]}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="background-color:rgb(240, 240, 240);padding:10px;border-radius:5px;">
                <strong>Personas Unicas Inscriptos REEL</strong><br>
                <span style="font-size:24px;">{unique_cuil_count}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style="background-color:white;padding:10px;border-radius:5px;">
                <strong>Inscriptos entre 26 y 44 años</strong><br>
                <span style="font-size:24px;">{count_26_44}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div style="background-color:white;padding:10px;border-radius:5px;">
                <strong>Inscriptos 45 años o más</strong><br>
                <span style="font-size:24px;">{count_45_inscriptos}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col5:
        st.markdown(
            f"""
            <div style="background-color:white;padding:10px;border-radius:5px;">
                <strong>Inscriptos Zonas Favorecidas</strong><br>
                <span style="font-size:24px;">{total_dept_specific}</span>
            </div>
            """, 
            unsafe_allow_html=True
        ) 


    # Crear dos columnas para los botones de descarga
    st.markdown("### Descarga de bases")
    col1, col2 = st.columns(2)
    
    
    with col1:
        buffer1 = io.BytesIO()
        col_inscripcion = ['ID_FICHA' ,'APELLIDO' ,'NOMBRE' ,'CUIL','N_ESTADO_FICHA' ,'NUMERO_DOCUMENTO' ,'FER_NAC','EDAD','SEXO', 'FEC_SIST' ,'CALLE' ,'NUMERO' ,'BARRIO' ,'N_LOCALIDAD', 'N_DEPARTAMENTO' ,'TEL_FIJO' ,'TEL_CELULAR' ,'CONTACTO' ,'MAIL' ,'ES_DISCAPACITADO' ,'CERTIF_DISCAP' ,'FEC_SIST' ,'MODALIDAD' ,'TAREAS' ,'ALTA_TEMPRANA' ,'ID_MOD_CONT_AFIP' ,'MOD_CONT_AFIP' ,'FEC_MODIF' ,'RAZON_SOCIAL' ,'EMP_CUIT' ,'CANT_EMP' ,'EMP_CALLE' ,'EMP_NUMERO' ,'EMP_N_LOCALIDAD' ,'EMP_N_DEPARTAMENTO' ,'EMP_CELULAR' ,'EMP_MAIL' ,'EMP_ES_COOPERATIVA' ,'EU_NOMBRE' ,'EMP_APELLIDO' ,'EU_MAIL' ,'EU_TELEFONO']
        
        df_i = df_inscriptos[col_inscripcion]

        with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
            df_i.to_excel(writer, index=False, sheet_name='Inscriptos')
            #writer.save()
            buffer1.seek(0)

        st.download_button(
            label="Descargar Inscriptos REEL como Excel",
            data=buffer1,
            file_name='df_inscriptos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # Botón de descarga para df_cti
    with col2:
        buffer2 = io.BytesIO()
        df_c = df_cti_descarga[['ID_FICHA' ,'APELLIDO' ,'NOMBRE' ,'CUIL' ,'N_ESTADO_FICHA', 'NUMERO_DOCUMENTO' ,'FER_NAC','EDAD','SEXO', 'FEC_SIST' ,'CALLE' ,'NUMERO' ,'BARRIO' ,'N_LOCALIDAD', 'N_DEPARTAMENTO' ,'TEL_FIJO' ,'TEL_CELULAR' ,'CONTACTO' ,'MAIL' ,'ES_DISCAPACITADO' ,'CERTIF_DISCAP' ,'FEC_SIST' ,'MODALIDAD' ,'TAREAS' ,'ALTA_TEMPRANA' ,'ID_MOD_CONT_AFIP' ,'MOD_CONT_AFIP' ,'FEC_MODIF' ,'RAZON_SOCIAL' ,'EMP_CUIT' ,'CANT_EMP' ,'EMP_CALLE' ,'EMP_NUMERO' ,'EMP_N_LOCALIDAD' ,'EMP_N_DEPARTAMENTO' ,'EMP_CELULAR' ,'EMP_MAIL' ,'EMP_ES_COOPERATIVA' ,'EU_NOMBRE' ,'EMP_APELLIDO' ,'EU_MAIL' ,'EU_TELEFONO']]
        with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
            df_c.to_excel(writer, index=False, sheet_name='CTI')
            #writer.save()
            buffer2.seek(0)

        st.download_button(
            label="Descargar CTI como Excel",
            data=buffer2,
            file_name='df_cti.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


    # Verifica que las columnas de fecha estén presentes en los DataFrames
    if 'FEC_INSCRIPCION' in df_inscripciones.columns and 'FEC_SIST' in df_inscriptos.columns:
        # Filtrar fechas válidas en df_inscriptos
        df_inscriptos = df_inscriptos[df_inscriptos['FEC_SIST'].notna()]

        # Definir la fecha mínima como un Timestamp
        fecha_minima = pd.to_datetime("2024-08-19")

        # Agrupar por fecha y contar inscripciones para el primer conjunto (Inscripciones)
        inscripciones_por_fecha = df_inscripciones.groupby(df_inscripciones['FEC_INSCRIPCION'].dt.date).size().reset_index(name='Conteo')
        inscripciones_por_fecha.columns = ['Fecha', 'Conteo']
        inscripciones_por_fecha['Tipo'] = 'Adhesiones'
        
        # Agrupar por fecha y contar inscripciones para el segundo conjunto (Match)
        match_por_fecha = df_inscriptos.groupby(df_inscriptos['FEC_SIST'].dt.date).size().reset_index(name='Conteo')
        match_por_fecha.columns = ['Fecha', 'Conteo']
        match_por_fecha['Tipo'] = 'Match'

        # Agrupar por fecha y contar inscripciones para el tercer conjunto (CTI)
        cti_por_fecha = df_cti.groupby(df_cti['FEC_SIST'].dt.date).size().reset_index(name='Conteo')
        cti_por_fecha.columns = ['Fecha', 'Conteo']
        cti_por_fecha['Tipo'] = 'cti'
        
        # Combinar ambos DataFrames en uno solo
        datos_combinados = pd.concat([inscripciones_por_fecha, match_por_fecha, cti_por_fecha])
        
        # Asegúrate de que la columna 'Fecha' esté en formato datetime
        if 'Fecha' in datos_combinados.columns:
            datos_combinados['Fecha'] = pd.to_datetime(datos_combinados['Fecha'], errors='coerce')  # Convertir a datetime
            datos_combinados = datos_combinados.dropna(subset=['Fecha'])  # Eliminar filas con fechas nulas

       # Convertir 'Fecha' a datetime.date
        datos_combinados['Fecha'] = datos_combinados['Fecha'].apply(lambda x: x.date() if isinstance(x, pd.Timestamp) else x)

        # Filtrar datos combinados por fecha mínima
        fecha_minima = pd.Timestamp("2024-08-19")  # Asegurar que sea un Timestamp para la comparación
        datos_combinados = datos_combinados[datos_combinados['Fecha'] >= fecha_minima.date()]  # Convertir fecha_minima a date


        # Crear gráfico combinado
        st.subheader("Postulaciones y Match por Fecha")
        fecha_chart_combined = alt.Chart(datos_combinados).mark_line().encode(
            x=alt.X('Fecha:T', title='Fecha', axis=alt.Axis(format='%d/%m/%Y', tickCount='day', labelAngle=-45)),
            y=alt.Y('Conteo:Q', title='Cantidad'),
            color='Tipo:N',  # Diferenciar por tipo (Inscripciones, Match, cti)
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

    # Corregir el nombre del departamento en df_poblacion
    df_poblacion['NOMDEPTO'] = df_poblacion['NOMDEPTO'].replace('PRESIDENTE ROQUE SAENZ PENA', 'PRESIDENTE ROQUE SAENZ PENA')

    # Corregir el nombre del departamento en df_inscriptos
    df_inscriptos['N_DEPARTAMENTO'] = df_inscriptos['N_DEPARTAMENTO'].str.replace("PTE ROQUE SAENZ PEÑA", "PRESIDENTE ROQUE SAENZ PENA", regex=False)
    
    # Calcular el número de inscriptos por departamento usando 'ID_FICHA'
    inscriptos_por_depto = df_inscriptos.groupby('N_DEPARTAMENTO')['CUIL'].count().reset_index(name='Cuenta')

    # Asegúrate de que las columnas coincidan
    if 'NOMDEPTO' in df_poblacion.columns:
        df_poblacion['INSCRIPTOS'] = df_poblacion['NOMDEPTO'].map(inscriptos_por_depto.set_index('N_DEPARTAMENTO')['Cuenta']).fillna(0).astype(int)


    # Crear el mapa
    st.subheader("Distribucion de inscriptos por Departamento")
    ig = px.choropleth_mapbox(
    df_poblacion,
    geojson=geojson_data,
    locations='NOMDEPTO',
    featureidkey='properties.NOMDEPTO',
    color='INSCRIPTOS',
    mapbox_style="carto-positron",
    zoom=4,
    center={"lat": -31.416, "lon": -64.183},
    opacity=0.5,
    labels={'INSCRIPTOS': 'Número de Inscriptos'},
)

    # Actualizar la geometría
    ig.update_geos(fitbounds="locations", visible=False)

    # Mostrar el gráfico
    st.plotly_chart(ig, use_container_width=True)

    # Agregar botón de descarga para el DataFrame agrupado
    buffer = io.BytesIO()
    # Convertir inscriptos_por_depto a CSV con codificación utf-8-sig
    inscriptos_por_depto.to_csv(buffer, index=False, encoding='utf-8-sig')
    buffer.seek(0)

    st.download_button(
        label="Descargar Inscriptos por Departamento como CSV",
        data=buffer,
        file_name='inscriptos_por_depto.csv',
        mime='text/csv'
    )
    
