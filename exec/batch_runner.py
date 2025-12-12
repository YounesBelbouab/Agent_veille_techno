import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import asyncio
import ast
from email.message import EmailMessage
from bigquery_utils import extract_configs_from_bigquery
from agents.rating_agent import SortAgent
from agents.conversation_agent import ConversationAgent
# from discord_bot import send_veille_discord
from html_newsletter import generate_newsletter_html

KEYWORDS_DATA_IA_CYBER = [
    "Big Data", "ETL", "ELT", "Data Pipeline", "Data Lake", "Data Warehouse",
    "Data Governance", "Data Quality", "Apache Spark", "PySpark", "Databricks",
    "Apache Kafka", "Airflow", "dbt", "Snowflake", "BigQuery", "Artificial Intelligence",
    "Machine Learning", "Deep Learning", "NLP", "Generative AI", "LLM",
    "TensorFlow", "PyTorch", "Hugging Face", "AWS", "Azure", "Google Cloud",
    "Cybersecurity", "Zero Trust", "DevSecOps"
]

MODEL_ID = "llama-3.3-70b-versatile"

def send_newsletter(email_user, veille_content, subject="Newsletter Technologique"):
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 465))

    html_content = generate_newsletter_html(veille_content)

    try:
        with open("template_mail.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    except FileNotFoundError:
        print("Erreur : Le fichier template_mail.html est introuvable.")
        return
    
    
    msg = EmailMessage()
    msg["From"] = f"No-Reply <{email_address}>"
    msg["To"] = email_user
    msg["Subject"] = subject

    msg.set_content(veille_content)

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print(f"Email envoyé à {email_user} avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi à {email_user} : {e}")


# def send_private_discord(id_user, veille_user):
#     token = os.getenv("DISCORD_TOKEN")
#     if not token:
#         return

#     base_url = "https://discord.com/api/v10"
#     headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

#     dm_payload = {"recipient_id": id_user}
#     response_dm = requests.post(f"{base_url}/users/@me/channels", headers=headers, json=dm_payload)

#     if response_dm.status_code != 200:
#         print(f"Impossible d'ouvrir DM Discord avec {id_user}: {response_dm.status_code}")
#         return

#     channel_id = response_dm.json().get("id")

#     chunks = [veille_user[i:i + 1900] for i in range(0, len(veille_user), 1900)]

#     for chunk in chunks:
#         msg_payload = {"content": chunk}
#         requests.post(f"{base_url}/channels/{channel_id}/messages", headers=headers, json=msg_payload)

#     print(f"Message Discord envoye a {id_user}")


def generate_rapport_ia(articles, conv_agent):
    if not articles:
        return "Rien a signaler aujourd'hui."

    rapport_final = "Voici la marchandise du jour.\n\n"

    for article in articles:
        if hasattr(conv_agent, 'initiate_history'):
            conv_agent.initiate_history()

        titre = article.get('title', 'Titre inconnu')
        source = article.get('source', 'Source inconnue')
        url = article.get('url', 'N/A')
        content = article.get('content', '') or "" 

        prompt = (
            f"Tache : Analyse cet article et genere un rapport de veille formate (Style Jarvis).\n"
            f"--- DONNEES ARTICLE ---\n"
            f"Titre : {titre}\n"
            f"Source : {source}\n"
            f"URL : {url}\n"
            f"Contenu : {content[:15000]}"
        )

        try:
            resume = conv_agent.ask_llm(user_interaction=prompt, model=MODEL_ID)
            rapport_final += resume + "\n\n" + ("-" * 40) + "\n\n"
        except Exception as e:
            print(f"Erreur IA sur {titre}: {e}")
            rapport_final += f"⚠️ Erreur analyse IA : {titre}\n\n"

    return rapport_final


async def run_batch(bot_client):
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
            articles = await asyncio.to_thread(
                sort_agent.get_sorted_articles,  
                keywords_list=keywords_list,   
                lang=user['langue'],
                days=user['periode'],
                max_raw=50,
                top_k=user['nb_articles'],
                tech_vocabulary=KEYWORDS_DATA_IA_CYBER
            )
        except Exception as e:
            print(f"Erreur SortAgent : {e}")
            continue

        if not articles:
            print("Aucun article trouve.")
            continue

        veille_user = await asyncio.to_thread(generate_rapport_ia, articles, conv_agent)

        if user.get('email') and "@" in user['email']:
            send_newsletter(user['email'], veille_user)

        if user.get('id_discord'):
            print(f"📨 Envoi à {user['id_discord']}")
            try:
                await bot_client.send_veille_discord(user['id_discord'], veille_user)
            except Exception as e:
                print(f"❌ Erreur envoi : {e}")

    print("\nBatch termine.")


# if __name__ == "__main__":
    # run_batch()