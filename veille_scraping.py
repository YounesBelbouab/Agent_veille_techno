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
        return "❌ Erreur : Clé API NewsAPI manquante (API_KEY_NEW_API dans .env)."

    query = sujet.replace(" ", "%20")
    date = (datetime.now() - timedelta(days=jour)).strftime('%Y-%m-%d')
    
    URL = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={date}&"
        f"sortBy=publishedAt&"
        f"language={langue.lower()}&"
        f"pageSize={nb_articles}&" 
        f"apiKey={api_key}"      
    )
    
    # ------------------- problème ici -------------------
    try:
        response = requests.get(URL).json()
    except requests.exceptions.RequestException as e:
        return f"❌ Erreur lors de l'appel de l'API : {e}"
    
    articles = response.get("articles", [])

    if not articles:
        return f"🔍 Aucun article trouvé pour **{sujet}** dans les {jour} derniers jours."
    
    # ----------------------------------------------------

    output_lines = []
    
    output_lines.append(f"Articles trouvés (max {nb_articles} affichés) : {len(articles)}")
    
    for i, article in enumerate(articles):

        try:
            downloaded = trafilatura.fetch_url(article["url"])
            content = trafilatura.extract(downloaded) if downloaded else "Pas de contenu disponible"
            
            # limit message length
            if content and len(content) > 300:
                 content = content[:300] + "..."
            
        except Exception:
            content = "Contenu non extractible."

        # response formatting for Discord
        output_lines.append(
            f"\n--- Article {i+1} ---\n"
            f"**Titre :** {article['title']}\n"
            f"**Source :** {article['source']['name']} | **Date :** {article['publishedAt'][:10]}\n"
            f"**Lien :** <{article['url']}>\n"
            f"***Extrait :*** {content}"
        )

    return "\n".join(output_lines)