from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import secretmanager
import os
import datetime
import json 

PROJECT_ID = "project-fil-orange"
DATASET_ID = "veille_automation"
TABLE_ID = "user_configs" 

def get_sa_credentials(service_account):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{service_account}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_bq_client():
    service_account_veille = get_sa_credentials("veille-automation")
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_veille)
    )
    return bigquery.Client(credentials=credentials,project=PROJECT_ID)

def insert_config_to_bigquery(user_data):

    client_bigquery = get_bq_client()
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


    query = f"""
    MERGE `{table_ref}` T
    USING (
      SELECT * FROM UNNEST([STRUCT(
        @id_discord as id_discord,
        @email as email,
        @sujet as sujet,
        @langue as langue,
        @periode as periode,
        @nb_articles as nb_articles
      )])
    ) S
    ON T.id_discord = S.id_discord
    
    WHEN MATCHED THEN
      UPDATE SET 
        email = S.email,
        sujet = S.sujet,
        langue = S.langue,
        periode = S.periode,
        nb_articles = S.nb_articles
        
    WHEN NOT MATCHED THEN
      INSERT (id_discord, email, sujet, langue, periode, nb_articles)
      VALUES (id_discord, email, sujet, langue, periode, nb_articles)
    """

    # ON GARDE LA SÉCURITÉ DES TYPES
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id_discord", "STRING", user_data["id_discord"]),
            bigquery.ScalarQueryParameter("email", "STRING", user_data["email"]),
            bigquery.ScalarQueryParameter("sujet", "STRING", user_data["sujet"]),
            bigquery.ScalarQueryParameter("langue", "STRING", user_data["langue"]),
            bigquery.ScalarQueryParameter("periode", "INTEGER", user_data["periode"]),
            bigquery.ScalarQueryParameter("nb_articles", "INTEGER", user_data["nb_articles"]),
        ]
    )

    try:
        query_job = client_bigquery.query(query, job_config=job_config)
        query_job.result() 
        print(f"✅ Config sauvegardée pour {user_data['id_discord']}")
        
    except Exception as e:
        print(f"❌ Erreur BigQuery : {e}")
        raise e
    

def extract_configs_from_bigquery():
    client_bigquery = get_bq_client()
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    query = f"""
    SELECT id_discord, email, sujet, langue, periode, nb_articles
    FROM `{table_ref}`
    """

    try:
        query_job = client_bigquery.query(query)
        results = query_job.result() 

        configs = []
        for row in results:
            configs.append({
                "id_discord": row.id_discord,
                "email": row.email,
                "sujet": row.sujet,
                "langue": row.langue,
                "periode": row.periode,
                "nb_articles": row.nb_articles,
            })
        print(f"✅ {len(configs)} configs extraites de BigQuery.")
        return configs

    except Exception as e:
        print(f"❌ Erreur BigQuery lors de l'extraction : {e}")
        raise e

if __name__ == "__main__":
    configs = extract_configs_from_bigquery()
    for config in configs:
        print(config)