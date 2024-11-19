import pandas as pd
import tempfile
import os
import json 
import geopandas as gpd
from datetime import timedelta
import json
from supabase import create_client
from io import BytesIO

def load_data_from_bucket(bucket_name, supabase_url, supabase_key):
    dfs = []
    file_dates = []
    try:
        supabase = create_client(supabase_url, supabase_key)
        files = supabase.storage.from_(bucket_name).list()
    except Exception as e:
        print(f"Error al cargar datos del bucket: {str(e)}")
   

    for file in files:
        # Obtener metadatos del archivo
        creation_date = file['created_at']
        # Descargar el archivo desde el bucket
        response = supabase.storage.from_(bucket_name).download(file['name'])
        if file['name'].endswith('.parquet'):
            df = pd.read_parquet(BytesIO(response))  # Leer el archivo parquet
            dfs.append(df)
            file_dates.append(creation_date)
        elif file['name'].endswith('.geojson'):
            if isinstance(response, bytes):
                geojson_dict = json.loads(response.decode('utf-8'))
            else:
                geojson_dict = response  # Ya es un dict
            # Crear un GeoDataFrame desde las características del GeoJSON
            gdf = gpd.GeoDataFrame.from_features(geojson_dict['features'])
            # Verificar y asignar el CRS original si es necesario
            if gdf.crs is None or gdf.crs.to_string() != 'EPSG:22174':
                gdf = gdf.set_crs(epsg=22174)  # Asegúrate de que este sea el CRS correcto
            # Convertir a WGS 84 para la visualización (EPSG:4326)
            gdf = gdf.to_crs(epsg=4326)
            # Convertir el GeoDataFrame a GeoJSON para la visualización
            response = gdf.__geo_interface__
            dfs.append(response)
        elif file['name'].endswith('.csv'):
            df = pd.read_csv(BytesIO(response))
            dfs.append(df)
            file_dates.append(creation_date)
    return dfs, file_dates