import requests
import trafilatura
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


def load_api_key():
    load_dotenv()
    return os.getenv("API_KEY_NEW_API")


def call_api_articles(sujet, langue, jour, nb_articles):
    api_key = load_api_key()
    if not api_key:
        return []

    query = sujet.replace(" ", "%20")
    date = (datetime.now() - timedelta(days=jour)).strftime('%Y-%m-%d')

    URL = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={date}&"
        f"sortBy=relevancy&"
        f"language={langue.lower()}&"
        f"pageSize={nb_articles}&"
        f"apiKey={api_key}"
    )

    try:
        response = requests.get(URL).json()
    except requests.exceptions.RequestException:
        return []

    articles_api = response.get("articles", [])

    if not articles_api:
        return []

    articles_trouves = []

    for article in articles_api:
        try:
            downloaded = trafilatura.fetch_url(article["url"])
            content = trafilatura.extract(downloaded) if downloaded else ""

            if content and len(content) > 15000:
                content = content[:15000]

            if not content:
                content = "Pas de contenu disponible"

        except Exception:
            content = "Contenu non extractible"

        article['content'] = content
        articles_trouves.append(article)

    return articles_trouves