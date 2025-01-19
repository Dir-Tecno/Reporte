import pandas as pd
import geopandas as gpd
import requests
import logging
import traceback
import streamlit as st
import io

def obtener_archivo_gitlab(repo_id, file_path, branch='main', token='TU_TOKEN'):
    """
    Obtiene un archivo de un repositorio de GitLab.

    Args:
        repo_id (str): ID del proyecto en GitLab.
        file_path (str): Ruta del archivo en el repositorio.
        branch (str): Rama del repositorio (por defecto 'main').
        token (str): Token de acceso personal.

    Returns:
        bytes: Contenido del archivo.
    """
    file_path_encoded = requests.utils.quote(file_path)
    url = f'https://gitlab.com/api/v4/projects/{repo_id}/repository/files/{file_path_encoded}/raw?ref={branch}'
    headers = {
        'PRIVATE-TOKEN': token
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.content  # Devuelve el contenido del archivo
    else:
        raise Exception(f"Error al obtener el archivo: {response.status_code} - {response.text}")

def obtener_lista_archivos(repo_id, branch='main', token='TU_TOKEN'):
    """
    Obtiene la lista completa de archivos en el repositorio.
    """
    url = f'https://gitlab.com/api/v4/projects/{repo_id}/repository/tree'
    headers = {'PRIVATE-TOKEN': token}
    params = {'ref': branch}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        archivos = [file['path'] for file in response.json()]
        return archivos
    else:
        raise Exception(f"Error al obtener lista de archivos: {response.status_code} - {response.text}")

def obtener_metadata_archivo(repo_id, file_path, branch='main', token='TU_TOKEN'):
    """
    Obtiene los metadatos de un archivo específico de GitLab, incluyendo la fecha del último commit.
    """
    file_path_encoded = requests.utils.quote(file_path, safe='')
    url = f'https://gitlab.com/api/v4/projects/{repo_id}/repository/files/{file_path_encoded}'
    headers = {'PRIVATE-TOKEN': token}
    params = {'ref': branch}
    
    try:
        # Primero obtener el commit_id del archivo
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            file_info = response.json()
            last_commit_sha = file_info.get('last_commit_id')
            
            # Luego obtener la información del commit
            commit_url = f'https://gitlab.com/api/v4/projects/{repo_id}/repository/commits/{last_commit_sha}'
            commit_response = requests.get(commit_url, headers=headers)
            
            if commit_response.status_code == 200:
                commit_info = commit_response.json()
                # Devolver la fecha del commit
                return commit_info.get('committed_date')
    
    except Exception as e:
        st.error(f"Error al obtener metadata: {str(e)}")
    
    return None

def load_data_from_gitlab(repo_id, file_path, branch='main', token='TU_TOKEN'):
    """
    Carga archivos parquet, txt y geojson relevantes del repositorio.
    """
    try:
        archivos = obtener_lista_archivos(repo_id, branch, token)
        
        # Continuar con la carga normal
        dataframes = [None] * len(archivos)
        file_dates = [None] * len(archivos)
        
        for idx, archivo in enumerate(archivos):
            if archivo.endswith(('.parquet', '.txt', '.geojson')) and not archivo.endswith('log.txt'):
                commit_date = obtener_metadata_archivo(repo_id, archivo, branch, token)
                if commit_date:
                    file_dates[idx] = commit_date
                
                file_content = obtener_archivo_gitlab(repo_id, archivo, branch, token)
                
                if archivo.endswith('.parquet'):
                    df = pd.read_parquet(io.BytesIO(file_content))
                elif archivo.endswith('.txt'):
                    df = pd.read_csv(io.StringIO(file_content.decode('utf-8')), sep='\t')
                elif archivo.endswith('.geojson'):
                    import json
                    geojson_str = file_content.decode('utf-8')
                    df = json.loads(geojson_str)
                
                dataframes[idx] = df
        
        return dataframes, file_dates

    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None, None