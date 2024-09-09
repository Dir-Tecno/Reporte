import pandas as pd
import tempfile
import os
from google.cloud import storage
from datetime import timedelta

def download_from_bucket(blob_name, bucket_name, credentials):
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.reload()
    file_date = blob.updated

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        blob.download_to_filename(temp_file.name)
        temp_file_name = temp_file.name
    
    file_date_adjusted = file_date - timedelta(hours=3)
    return temp_file_name, file_date_adjusted

def load_data_from_bucket(blob_names, bucket_name, credentials):
    dfs = []
    file_dates = []
    for blob_name in blob_names:
        temp_file_name, file_date = download_from_bucket(blob_name, bucket_name, credentials)
        try:
            df = pd.read_csv(temp_file_name, low_memory=False)
            dfs.append(df)
            file_dates.append(file_date)
        finally:
            os.remove(temp_file_name)  # Elimina el archivo temporal
    return dfs, file_dates

