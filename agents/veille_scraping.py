from agents.rating_agent import SortAgent

mot_cle_veille = [
    "Big Data", "ETL", "ELT", "Data Pipeline", "Data Lake", "Data Warehouse",
    "Data Governance", "Data Quality", "Data Lineage", "Data Catalog",
    "Master Data Management", "Data Modeling", "Data Architecture", "Real-time Data",
    "Streaming Data", "Event-driven Architecture", "Data Orchestration",
    "Data Engineer", "Data Analyst", "Data Scientist", "Analytics Engineer",
    "Machine Learning Engineer", "ML Ops Engineer", "Data Steward",
    "Data Product Manager", "Business Intelligence Analyst", "Data Consultant",
    "Apache Spark", "PySpark", "Databricks", "Apache Kafka", "Apache Flink",
    "Apache Beam", "Airflow", "Dagster", "Prefect", "dbt", "Fivetran", "Snowflake",
    "BigQuery", "Redshift", "Delta Lake", "S3", "Hadoop", "Hive", "Hudi", "Iceberg",
    "Tableau", "Power BI", "Looker", "Mode Analytics", "Superset", "Metabase", "Observable",
    "Artificial Intelligence", "Machine Learning", "Deep Learning", "Neural Networks",
    "NLP", "Computer Vision", "Generative AI", "Reinforcement Learning",
    "Large Language Models", "Model Training", "Model Evaluation", "Prompt Engineering",
    "Explainable AI", "Responsible AI", "AI Ethics",
    "TensorFlow", "PyTorch", "scikit-learn", "Hugging Face", "Transformers",
    "LangChain", "Weights & Biases", "DVC", "MLflow", "Keras", "OpenAI API",
    "NVIDIA CUDA", "XGBoost", "LightGBM", "CatBoost",
    "AI Engineer", "ML Engineer", "Research Scientist", "AI Product Manager",
    "NLP Engineer", "Computer Vision Engineer",
    "AWS", "Azure", "Google Cloud", "Serverless", "Cloud Architecture", "Scalability",
    "Observability", "Monitoring", "Data Security",
    "Cybersecurity", "Vulnerability Management", "Threat Intelligence", "Zero Trust",
    "SOC", "SIEM", "Incident Response", "Ransomware", "Malware Analysis",
    "Penetration Testing", "Encryption", "IAM", "Network Security",
    "Cloud Security", "DevSecOps"
]


def call_api_articles(sujet, langue, jour, nb_articles):
    agent = SortAgent()

    if "," in sujet:
        keywords_list = [k.strip() for k in sujet.split(",")]
    else:
        keywords_list = [sujet.strip()]

    return agent.get_sorted_articles(
        keywords_list=keywords_list,
        lang=langue,
        days=jour,
        max_raw=50,
        top_k=nb_articles,
        tech_vocabulary=mot_cle_veille
    )