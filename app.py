import streamlit as st
from streamlit_option_menu import option_menu
from moduls.carga import load_data_from_bucket
from moduls.inscripciones import show_inscriptions
from moduls.empresas import show_companies
from moduls.respuestas import show_responses
from google.oauth2 import service_account

# Configuración de las credenciales
credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Configuración de la página
st.set_page_config(page_title="Reporte Empleo +26", layout="wide")

# Nombres de los archivos en el bucket
bucket_name = "direccion"
blob_names = [
    "vt_inscripciones_empleo.csv",     # DataFrame 0
    "vt_empresas_adheridas.csv",        # DataFrame 1
    "VT_REPORTES_PPP_MAS26.csv",        # DataFrame 2
    "vt_inscripciones_empleo_e26empr.csv", # DataFrame 3
    "vt_respuestas.csv"                 # DataFrame 4
]

# Cargar datos desde el bucket
dfs, file_dates = load_data_from_bucket(blob_names, bucket_name, credentials)

# Calcular las métricas
# Total de inscripciones
total_inscripciones = dfs[0].shape[0]

# Total de empresas adheridas
total_empresas = dfs[1]['CUIT'].nunique()

# Filtrar el DataFrame df_inscriptos según la condición
df_inscriptos = dfs[2][dfs[2]['ID_EST_FIC'] == 8]  

# Total de inscriptos
total_inscriptos = df_inscriptos.shape[0]

# Mostrar contenido basado en la selección del menú
selected = option_menu(
    menu_title=None,
    options=["Inicio", "Inscripciones", "Empresas/Matcheos", "Respuestas"],
    icons=["house", "clipboard-data", "building", "chat"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#f0f0f0"},
        "icon": {"color": "#00aaff", "font-size": "18px"},
        "nav-link": {
            "font-size": "18px", 
            "text-align": "center", 
            "margin": "0px", 
            "padding": "10px", 
            "color": "#333",
            "border-radius": "8px",
            "background-color": "#fff",
            "--hover-color": "#ddd"
        },
        "nav-link-selected": {"background-color": "#00aaff", "color": "white"},
    }
)

# Función para crear una tarjeta de métrica
def create_metric_card(title, value, icon):
    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 150px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 20px;
        text-align: center;
        margin: 10px;
    ">
        <div style="font-size: 40px; margin-bottom: 10px;">{icon}</div>
        <div style="font-size: 20px; font-weight: bold;">{title}</div>
        <div style="font-size: 30px; color: #00aaff;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# Mostrar contenido basado en la selección del menú
if selected == "Inicio":
    st.title("Bienvenido al Reporte Empleo +26")
    st.write("Explore los datos y métricas relacionadas con el empleo seleccionando una opción en el menú.")

    # Crear una fila de tarjetas con métricas clave
    st.write("### Métricas Clave")
    col1, col2, col3 = st.columns(3)

    with col1:
        create_metric_card("Total Inscripciones", total_inscripciones, "📈")

    with col2:
        create_metric_card("Empresas Adheridas", total_empresas, "🏢")

    with col3:
        create_metric_card("Total Inscriptos", total_inscriptos, "👤")

elif selected == "Inscripciones":
    st.write("###")
    show_inscriptions(dfs[0],dfs[2], file_dates[0],file_dates[2])
elif selected == "Empresas/Matcheos":
    st.write("### Empresas/Matcheos")
    show_companies(dfs[1], dfs[2], dfs[3])
elif selected == "Respuestas":
    st.write("### Respuestas")
    show_responses(dfs[4], file_dates[4])
