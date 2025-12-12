import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from utils.bigquery_utils import extract_configs_from_bigquery
from agents.rating_agent import SortAgent
from agents.conversation_agent import ConversationAgent

keywords = [
    "Big Data", "ETL", "ELT", "Data Pipeline", "Data Lake", "Data Warehouse",
    "Data Governance", "Data Quality", "Apache Spark", "PySpark", "Databricks",
    "Apache Kafka", "Airflow", "dbt", "Snowflake", "BigQuery", "Artificial Intelligence",
    "Machine Learning", "Deep Learning", "NLP", "Generative AI", "LLM",
    "TensorFlow", "PyTorch", "Hugging Face", "AWS", "Azure", "Google Cloud",
    "Cybersecurity", "Zero Trust", "DevSecOps", "ChatGPT", "DeepSeek", "Gemini", "ClaudeIA",
]

MODEL_ID = "llama-3.3-70b-versatile"

def send_newsletters(mail_user, veille_user):
    sender_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not password:
        print(f"SMTP non configure. Echec envoi pour {mail_user}")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = mail_user
    msg['Subject'] = "Rapport de Veille - Jarvis"

    msg.attach(MIMEText(veille_user, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, mail_user, text)
        server.quit()
        print(f"Mail envoye a {mail_user}")
    except Exception as e:
        print(f"Erreur envoi mail a {mail_user} : {e}")

def send_discord(id_user, veille_user):
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        return

    base_url = "https://discord.com/api/v10"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    dm_payload = {"recipient_id": id_user}
    response_dm = requests.post(f"{base_url}/users/@me/channels", headers=headers, json=dm_payload)

    if response_dm.status_code != 200:
        print(f"Impossible d'ouvrir DM Discord avec {id_user}: {response_dm.status_code}")
        return

    channel_id = response_dm.json().get("id")

    chunks = [veille_user[i:i + 1900] for i in range(0, len(veille_user), 1900)]

    for chunk in chunks:
        msg_payload = {"content": chunk}
        requests.post(f"{base_url}/channels/{channel_id}/messages", headers=headers, json=msg_payload)

    print(f"Message Discord envoye a {id_user}")

def generate_rapport_ia(articles, conv_agent):
    if not articles:
        return "Rien a signaler aujourd'hui."

    rapport_final = "Voici la marchandise du jour.\n\n"

    for article in articles:
        conv_agent.initiate_history()

        prompt = (
            f"Tache : Analyse cet article et genere un rapport de veille formate (Style Jarvis).\n"
            f"--- DONNEES ARTICLE ---\n"
            f"Titre : {article['title']}\n"
            f"Source : {article['source']}\n"
            f"URL : {article['url']}\n"
            f"Contenu : {article['content'][:15000]}"
        )

        try:
            resume = conv_agent.ask_llm(user_interaction=prompt, model=MODEL_ID)
            rapport_final += resume + "\n\n" + ("-" * 40) + "\n\n"
        except Exception as e:
            rapport_final += f"Erreur analyse IA : {article['title']}\n\n"

    return rapport_final

def run_batch():
    load_dotenv()
    print("Demarrage du Batch Veille...")

    users = extract_configs_from_bigquery()

    if not users:
        print("Aucun utilisateur trouve dans BigQuery.")
        return

    sort_agent = SortAgent()
    conv_agent = ConversationAgent()

    for user in users:
        print(f"\nTraitement pour : {user['email']} (Sujet: {user['sujet']})")

        if "," in user['sujet']:
            keywords_list = [k.strip() for k in user['sujet'].split(",")]
        else:
            keywords_list = [user['sujet'].strip()]

        try:
            articles = sort_agent.get_sorted_articles(
                keywords_list=keywords_list,
                lang=user['langue'],
                days=user['periode'],
                max_raw=50,
                top_k=user['nb_articles'],
                tech_vocabulary=keywords
            )
        except Exception as e:
            print(f"Erreur SortAgent : {e}")
            continue

        if not articles:
            print("Aucun article trouve.")
            continue

        veille_user = generate_rapport_ia(articles, conv_agent)

        if user.get('email') and "@" in user['email']:
            send_newsletters(user['email'], veille_user)

        if user.get('id_discord'):
            send_discord(user['id_discord'], veille_user)

    print("\nBatch termine.")

if __name__ == "__main__":
    run_batch()