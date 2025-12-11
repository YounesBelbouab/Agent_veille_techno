import requests
import trafilatura
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import tldextract

load_dotenv()
API_KEY = os.getenv("API_KEY_NEW_API")
print(API_KEY)

keywords = "Musculation OR intelligence artificielle OR Application"
query = keywords.replace(" ", "%20")
langage = input("En quelle langue ? 1 pour Français, 2 pour Anglais : ")

if langage == "1":
    langue = "fr"
    fichier_sources = "Agent_veille_techno/sources_fiables_fr.txt"
else:
    langue = "en"
    fichier_sources = "Agent_veille_techno/sources_fiables_anglais.txt"


jours = int(input("Depuis combien de jours ? "))
nb_articles = int(input("Combien d'articles voulez-vous ? "))


date_from = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")

with open(fichier_sources, "r", encoding="utf-8") as f:
    liste_sites_fiables = [ligne.strip() for ligne in f.readlines()]

URL = (
    f"https://newsapi.org/v2/everything?"
    f"q={query}&"
    f"from={date_from}&"
    f"sortBy=publishedAt&"
    f"language=fr&"
    f"apiKey={API_KEY}"
)

response = requests.get(URL)
data = response.json()

print("Nombre d’articles trouvés :", len(data.get("articles", [])))

articles_ecrit = 0

with open("veille_tech_semaine_r.txt", "w", encoding="utf-8") as f:
    for i, article in enumerate(data.get("articles", [])):

        if articles_ecrit >= nb_articles:
            break
        url = article["url"]
        domaine = urlparse(url).netloc.replace("www.", "")

        ext = tldextract.extract(url)
        domaine_principal = ext.domain + "." + ext.suffix
        if domaine_principal not in liste_sites_fiables:
            continue
        f.write(f"Article {articles_ecrit + 1}:\n")
        f.write(f"Titre: {article['title']}\n")
        f.write(f"Source: {article['source']['name']}\n")
        f.write(f"Date: {article['publishedAt']}\n")
        f.write(f"Lien: {article['url']}\n")

        downloaded = trafilatura.fetch_url(article["url"])
        content = trafilatura.extract(downloaded) if downloaded else "Pas de contenu disponible"

        f.write("\nContenu:\n")
        f.write(content if content else "Contenu non extractible")
        f.write("\n" + "=" * 90 + "\n\n")

        articles_ecrit += 1

print("Fichier généré avec succès")
