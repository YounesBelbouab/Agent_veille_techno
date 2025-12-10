import requests
import trafilatura
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY_NEW_API")
print(API_KEY)


keywords = "technologie OR intelligence artificielle OR python"
query = keywords.replace(" ", "%20")

langage = input("En quelle langue ? 1 pour Français, 2 pour Anglais : ")

if langage == "1":
    langue = "fr"
else:
    langue = "en"

jours = int(input("Depuis combien de jours ? "))
nb_articles = int(input("Combien d'articles voulez-vous ? "))

date_from = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")

URL = (
    f"https://newsapi.org/v2/everything?"
    f"q={query}&"
    f"from={date_from}&"
    f"sortBy=publishedAt&"
    f"language={langue}&"
    f"apiKey={API_KEY}"
)

response = requests.get(URL)
data = response.json()

print("Nombre d’articles trouvés :", len(data.get("articles", [])))


articles_ecrit = 0

with open("veille_tech_semaine.txt", "w", encoding="utf-8") as f:
    for i, article in enumerate(data.get("articles", [])):

        if articles_ecrit >= nb_articles:
            break

        f.write(f"Article {i+1}:\n")
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
