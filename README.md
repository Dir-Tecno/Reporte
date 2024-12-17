# Dashboard Empleo +26

## Descripción
Aplicación web desarrollada con Streamlit para el seguimiento y análisis del programa Empleo +26. Esta herramienta permite visualizar datos de inscripciones y empresas participantes, facilitando la gestión y monitoreo del programa.

## Características Principales
- **Seguimiento de Inscripciones**: Análisis detallado de participantes inscritos
- **Gestión de Empresas**: Monitoreo de empresas participantes
- **Visualizaciones Interactivas**: Gráficos y tablas dinámicas
- **Actualización Automática**: Sincronización con base de datos Supabase

## Tecnologías Utilizadas
- Python 3.x
- Streamlit
- Pandas
- Supabase (almacenamiento de datos)

## Requisitos
streamlit
pandas
supabase
plotly

## Instalación
1. Clonar el repositorio
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración
1. Crear archivo `.streamlit/secrets.toml` con las credenciales de Supabase:
   ```toml
   [supabase]
   url = "TU_URL_SUPABASE"
   key = "TU_KEY_SUPABASE"
   ```

## Uso
1. Activar el entorno virtual:
   ```bash
   source venv/bin/activate
   ```
2. Ejecutar la aplicación:
   ```bash
   streamlit run app.py
   ```

## Estructura del Proyecto
```
Empleo/
├── app.py                # Aplicación principal
├── requirements.txt      # Dependencias
├── moduls/              # Módulos de la aplicación
│   ├── carga.py         # Carga de datos
│   ├── inscripciones.py # Gestión de inscripciones
│   └── empresas.py      # Gestión de empresas
└── .streamlit/          # Configuración de Streamlit
```

## Funcionalidades
- Visualización de estadísticas de inscripción
- Seguimiento de empresas participantes
- Filtros dinámicos por fecha y región
- Exportación de datos

## Mantenimiento
- Datos actualizados en tiempo real desde Supabase
- Sistema de manejo de errores integrado
- Interfaz intuitiva y responsive

## Soporte
Para reportar problemas o sugerir mejoras, por favor crear un issue en el repositorio.