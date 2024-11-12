import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io
import pydeck as pdk
import plotly.express as px
import requests  # Añadir al inicio del archivo



def enviar_a_slack(comentario, valoracion):
    # Obtener el webhook URL desde secrets
    SLACK_WEBHOOK_URL = st.secrets["slack"]["webhook_url"]
    
    mensaje = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📝 Nuevo Comentario Recibido"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Comentario:*\n{comentario}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Valoración:*\n{'⭐' * valoracion}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=mensaje)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al enviar a Slack: {str(e)}")
        return False

def show_inscriptions(df_postulaciones_fup, df_inscripciones, df_inscriptos, df_poblacion, file_date_inscripciones, file_date_inscriptos, file_date_poblacion, geojson_data):
    
    df_inscriptos_ppp = df_inscriptos[df_inscriptos['IDETAPA'] == 53]
    df_match_ppp = df_inscriptos_ppp[df_inscriptos_ppp['ID_EST_FIC'] == 8]

    
    # REPORTE PPP
    st.markdown("### Programa Primer Paso")
    st.write(f"Datos actualizados al: {file_date_inscripciones.strftime('%d/%m/%Y %H:%M:%S')}")

    total_postulantes_ppp = df_postulaciones_fup['CUIL'].nunique()
    total_match_ppp = df_match_ppp['CUIL'].shape[0]
    total_match_ppp_unicos = df_match_ppp['CUIL'].nunique()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="background-color:#d0e3f1;padding:10px;border-radius:5px;">
                <strong>Total Postulantes PPP</strong><br>
                <span style="font-size:24px;">{total_postulantes_ppp}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="background-color:#d6efd6;padding:10px;border-radius:5px;">
                <strong>Total Match PPP</strong><br>
                <span style="font-size:24px;">{total_match_ppp}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div style="background-color:#ffecd2;padding:10px;border-radius:5px;">
                <strong>Total Match de Personas Únicas PPP</strong><br>
                <span style="font-size:24px;">{total_match_ppp_unicos}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # Gráfico de torta con la edad
    df_postulaciones_fup['FEC_NACIMIENTO'] = pd.to_datetime(df_postulaciones_fup['FEC_NACIMIENTO'], errors='coerce')
    
    # Asegurarse de que no haya valores NaT antes de calcular la edad
    df_postulaciones_fup = df_postulaciones_fup.dropna(subset=['FEC_NACIMIENTO'])
    
    # Verificar si hay valores NaT después de la conversión
    if df_postulaciones_fup['FEC_NACIMIENTO'].isnull().any():
        st.warning("Hay valores nulos en la columna FEC_NACIMIENTO después de la conversión.")
        return  # Salir de la función si hay valores nulos

    df_postulaciones_fup['Edad'] = (pd.Timestamp(datetime.now()) - df_postulaciones_fup['FEC_NACIMIENTO']).dt.days // 365
    
    # Filtrar mayores de 25 años
    edad_counts = df_postulaciones_fup[df_postulaciones_fup['Edad'] <= 25]['Edad'].value_counts().reset_index()
    edad_counts.columns = ['Edad', 'Count']  # Renombrar columnas para el gráfico
        
    # Agregar tooltips al gráfico de torta
    fig = px.pie(edad_counts, values='Count', names='Edad', title='Distribución de Edades', 
                 hover_data=['Count'], labels={'Edad': 'Edad'})
    st.plotly_chart(fig)

    ##### PPP POR DEPARTAMENTEO ##########

    st.markdown("### por Departamentos")
    if 'N_DEPARTAMENTO' in df_postulaciones_fup.columns:
        departamentos = df_postulaciones_fup['N_DEPARTAMENTO'].unique()
        selected_departamento = st.multiselect("Filtrar por Departamento", departamentos, default=departamentos)
        df_filtered_departamentos = df_postulaciones_fup[df_postulaciones_fup['N_DEPARTAMENTO'].isin(selected_departamento)]
    else:
        df_filtered_departamentos = df_postulaciones_fup

    # Calcular el conteo de CUIL únicos por departamento y localidad
    departamento_counts = df_filtered_departamentos.groupby(['N_DEPARTAMENTO', 'N_LOCALIDAD'])['CUIL'].nunique().reset_index(name='Cuenta')
    departamento_counts_sorted = departamento_counts.sort_values(by='Cuenta', ascending=False)

    col1, col2 = st.columns([2, 3])
    with col2:
        st.subheader("Conteo por Departamento")
        st.altair_chart(
            alt.Chart(departamento_counts_sorted).mark_bar().encode(
                y=alt.Y('N_DEPARTAMENTO:N', title='Departamento', sort='-x'),
                x=alt.X('Cuenta:Q', title='Conteo de CUIL Únicos'),
                color=alt.Color('N_DEPARTAMENTO:N', legend=None),
                tooltip=['N_DEPARTAMENTO', 'Cuenta']
            ).properties(width=900, height=500),
            use_container_width=True
        )
    with col1:
        st.subheader("Tabla de Postulaciones")
        st.dataframe(departamento_counts_sorted, hide_index=True)

    # Corregir el nombre del departamento en df_poblacion
    df_poblacion['NOMDEPTO'] = df_poblacion['NOMDEPTO'].replace('PRESIDENTE ROQUE SAENZ PENA', 'PRESIDENTE ROQUE SAENZ PENA')

    # Corregir el nombre del departamento en df_postulaciones_fup
    df_postulaciones_fup['N_DEPARTAMENTO'] = df_postulaciones_fup['N_DEPARTAMENTO'].str.replace("PTE ROQUE SAENZ PEÑA", "PRESIDENTE ROQUE SAENZ PENA", regex=False)
    
    # Calcular el número de inscriptos únicos por departamento usando 'CUIL'
    inscriptos_por_depto = df_postulaciones_fup.groupby('N_DEPARTAMENTO')['CUIL'].nunique().reset_index(name='Cuenta')

    # Asegúrate de que las columnas coincidan
    if 'NOMDEPTO' in df_poblacion.columns:
        df_poblacion['INSCRIPTOS'] = df_poblacion['NOMDEPTO'].map(inscriptos_por_depto.set_index('N_DEPARTAMENTO')['Cuenta']).fillna(0).astype(int)

    # Crear el mapa
    st.subheader("Distribucion de postulaciones por Departamento")
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

    
    
    ########### EMPLEO +26 ##############
    
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

    # Filtrar solo los registros con ID_EST_FICHA = 3
    df_beneficiarios = df_inscriptos[df_inscriptos['ID_EST_FIC'] == 3]

    # Filtrar solo los registros con que quedan aptos
    df_postulantes_aptos = df_inscriptos[(df_inscriptos['ID_EST_FIC'] == 8) & (df_inscriptos['ID_EMP'].isnull())]

    # Filtrar solo los registros con que quedan para la repesca
    df_postulantes_repesca = df_inscriptos[(df_inscriptos['ID_EST_FIC'] == 8) & (df_inscriptos['ID_EMP'].notnull())]

    # Filtrar solo los registros con ID_EST_FICHA = 8
    df_inscriptos = df_inscriptos[df_inscriptos['ID_EST_FIC'].isin([8,3])]

   

    # Pestaña inscripciones
    st.markdown("### Programas Empleo +26")
    st.write(f"Datos actualizados al: {file_date_inscripciones.strftime('%d/%m/%Y %H:%M:%S')}")

    
    # Buzón de mensajes y valoración del reporte
    st.sidebar.header("📝 Buzón de Mensajes")
    st.sidebar.caption("Dirección de Tecnología y Análisis de Datos")

    # Área de texto para comentarios
    comentario = st.sidebar.text_area("Para poder ofrecerte los mejores reportes posibles, tu opinión es muy valiosa. Nos encantaría recibir tus comentarios sobre el reporte y saber en qué aspectos podemos mejorarlo. ¡Muchas gracias por ayudarnos a crecer y mejorar!", "", height=100)

    # Selector de valoración
    valoracion = st.sidebar.selectbox("Valora el reporte:", [1, 2, 3, 4, 5])

    # Botón para enviar el mensaje
    if st.sidebar.button("Enviar"):
        if comentario:
            # Intentar enviar a Slack
            if enviar_a_slack(comentario, valoracion):
                st.sidebar.success("✅ Gracias por tu comentario! El mensaje ha sido enviado.")
                st.sidebar.write(f"**Comentario:** {comentario}")
                st.sidebar.write(f"**Valoración:** {valoracion} estrellas")
            else:
                st.sidebar.error("❌ Hubo un error al enviar el mensaje a Slack.")
        else:
            st.sidebar.warning("⚠️ Por favor, escribe un comentario antes de enviar.")

    # Filtros de fechas para inscripciones
    #if 'FEC_INSCRIPCION' in df_inscripciones.columns:
        #st.sidebar.header("Filtros de Fechas")
        #fecha_min, fecha_max = df_inscripciones['FEC_INSCRIPCION'].min().date(), df_inscripciones['FEC_INSCRIPCION'].max().date()
        #fecha_inicio = st.sidebar.date_input("Fecha de Inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
        #fecha_fin = st.sidebar.date_input("Fecha de Fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
        #df_inscripciones = df_inscripciones[(df_inscripciones['FEC_INSCRIPCION'].dt.date >= fecha_inicio) & 
        #                                    (df_inscripciones['FEC_INSCRIPCION'].dt.date <= fecha_fin)]
    
    #if df_inscripciones.empty:
        #st.write("No hay inscripciones para mostrar en el rango de fechas seleccionado.")
        #return
    
    

    # Calcular edades en inscripciones
    fecha_actual = pd.Timestamp(datetime.now())

    # Calcular edades en inscriptos
    df_inscriptos['Edad'] = (fecha_actual - df_inscriptos['FER_NAC']).dt.days // 365

    # Calcular personas de 45 o más años en inscriptos
    #count_45_inscriptos = df_inscriptos[df_inscriptos['Edad'] >= 45].shape[0]
    # Calcular personas de entre 26 y 44 en inscriptos
    #count_26_44 = df_inscriptos[(df_inscriptos['Edad'] > 26) & (df_inscriptos['Edad'] < 45)]['CUIL'].nunique()

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
    total_cti = df_cti['CUIL'].nunique()
    total_cti_benef = df_cti_benef['CUIL'].nunique()
    total_cti_alta = df_cti_alta['CUIL'].nunique()
    total_benef = df_beneficiarios['CUIL'].nunique()
    total_postulantes_aptos = df_postulantes_aptos['CUIL'].nunique()
    total_postulantes_repesca = df_postulantes_repesca['CUIL'].nunique()

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

    
    st.markdown("### Reel")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div style="background-color:rgb(148 217 118);padding:10px;border-radius:5px;">
                <strong>Beneficiarios</strong><br>
                <span style="font-size:24px;">{total_benef}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="background-color:rgb(153 195 255);padding:10px;border-radius:5px;">
                <strong>Postulantes Aptos</strong><br>
                <span style="font-size:24px;">{total_postulantes_aptos}</span><br>
                <span style="font-size:12px;line-height:1;">Número de postulantes "Fuera de Cupo de Empresa", </span><br>
                <span style="font-size:12px;line-height:1;">aún no tomados por otra empresa.</span>

            </div>
            """, 
            unsafe_allow_html=True
        )
        """
    with col2:
        st.markdown(
            f""
            <div style="background-color:rgb(104 185 75);padding:10px;border-radius:5px;">
                <strong>Beneficiarios "Repesca"</strong><br>
                <span style="font-size:24px;">{total_postulantes_repesca}</span><br>
                <span style="font-size:12px;line-height:1;">Número de postulantes que quedaron "Fuera de Cupo de Empresa",</span><br>
                <span style="font-size:12px;line-height:1;">que fueron tomados por otras empresas.</span>
            </div>
            "", 
            unsafe_allow_html=True
        )
"""
    # Crear dos columnas para los botones de descarga
    st.header("### Descarga de bases PPP y Empleo+26")
    col1, col2 = st.columns(2)
    
    
    with col1:
        buffer1 = io.BytesIO()
        col_inscripcion = ['ID_FICHA' ,'APELLIDO' ,'NOMBRE' ,'CUIL','N_ESTADO_FICHA','IDETAPA' ,'NUMERO_DOCUMENTO' ,'FER_NAC','EDAD','SEXO', 'FEC_SIST' ,'CALLE' ,'NUMERO' ,'BARRIO' ,'N_LOCALIDAD', 'N_DEPARTAMENTO' ,'TEL_FIJO' ,'TEL_CELULAR' ,'CONTACTO' ,'MAIL' ,'ES_DISCAPACITADO' ,'CERTIF_DISCAP' ,'FEC_SIST' ,'MODALIDAD' ,'TAREAS' ,'ALTA_TEMPRANA' ,'ID_MOD_CONT_AFIP' ,'MOD_CONT_AFIP' ,'FEC_MODIF' ,'RAZON_SOCIAL' ,'EMP_CUIT' ,'CANT_EMP' ,'EMP_CALLE' ,'EMP_NUMERO' ,'EMP_N_LOCALIDAD' ,'EMP_N_DEPARTAMENTO' ,'EMP_CELULAR' ,'EMP_MAIL' ,'EMP_ES_COOPERATIVA' ,'EU_NOMBRE' ,'EMP_APELLIDO' ,'EU_MAIL' ,'EU_TELEFONO']
        
        df_i = df_inscriptos[col_inscripcion]

        with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
            df_i.to_excel(writer, index=False, sheet_name='Inscriptos')
            #writer.save()
            buffer1.seek(0)

        st.download_button(
            label="Descargar Inscriptos REEL como Excel (con beneficiarios)",
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


    


