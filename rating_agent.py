import requests
import trafilatura
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv


class SortAgent:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("API_KEY_NEW_API")
        self.POOL_SIZE = 50

        self.noise_keywords = [
            "salaire", "salary", "salaries", "compensation", "remuneration", "rémunération", "pay",
            "hiring", "recrutement", "embauche", "job", "career", "carrière", "vacancy", "workforce",
            "event", "événement", "conference", "conférence", "summit", "webinar", "meetup",
            "hackathon", "award", "prix", "winner", "gagnant", "nomination", "appoints"
        ]

        self.reliable_sources = [
            "The Verge", "Wired", "TechCrunch", "Ars Technica", "MIT Technology Review",
            "Bloomberg Technology", "Reuters Technology", "Financial Times - Technology",
            "CNBC Technology", "The Gradient", "AI Alignment Forum", "Machine Learning Mastery",
            "Towards Data Science", "KDnuggets", "Analytics Vidhya", "Distill.pub",
            "DeepLearning.ai Blog", "Google AI Blog", "Meta AI Research Blog", "Microsoft Research Blog",
            "Amazon Science", "NVIDIA Technical Blog", "Stanford AI Lab News", "Berkeley AI Research",
            "OpenAI Blog", "Hugging Face Blog", "Neptune.ai Blog", "Weights & Biases Blog",
            "DVC Blog", "Data Engineering Podcast", "Data Engineering Weekly", "O’Reilly AI and Data News",
            "Synced Review", "EleutherAI Blog", "Databricks Blog", "Snowflake Blog", "Confluent Kafka Blog",
            "Airflow Blog", "Prefect Blog", "Dagster Blog", "dbt Labs Blog", "Fivetran Blog",
            "Monte Carlo Data Blog", "Great Expectations Blog", "Spotify Engineering Blog",
            "Airbnb Engineering & Data Science Blog", "Uber Engineering Blog", "LinkedIn Engineering Blog",
            "Netflix Tech Blog", "Meta Engineering Blog", "Google Cloud Blog", "AWS Big Data Blog",
            "Microsoft Azure Blog", "DigitalOcean Blog", "Tableau Blog", "Power BI Blog", "Looker Blog",
            "Mode Analytics Blog", "Observable Blog", "FlowingData", "Storytelling with Data",
            "Krebs on Security", "BleepingComputer", "The Hacker News", "Dark Reading", "Hacker News",
            "Reddit r/MachineLearning", "Reddit r/DataEngineering", "Reddit r/datascience", "Lobsters",
            "Stack Overflow Blog", "Next INpact", "L’Usine Digitale", "Les Numériques", "Frandroid",
            "Le Big Data", "Actu IA", "Siècle Digital", "Bdm"
        ]

    def fetch_from_api(self, keywords_list, lang, days, max_results):
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        query_string = " OR ".join([f'"{k.strip()}"' for k in keywords_list])
        query_formatted = query_string.replace(" ", "%20").replace('"', '%22')

        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={query_formatted}&"
            f"from={date_from}&"
            f"sortBy=publishedAt&"
            f"language={lang}&"
            f"pageSize={max_results}&"
            f"apiKey={self.api_key}"
        )

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except Exception as e:
            print(f"Erreur API : {e}")
            return []

    def pertinence_score_calcul(self, article, content, keywords_list, vocab_tech=None):
        score = 0
        title = article.get('title', '').lower()
        content_lower = content.lower()

        for term in keywords_list:
            term_clean = term.strip().lower()
            if term_clean in title:
                score += 20
            count = content_lower.count(term_clean)
            score += min(count * 1, 20)

        for noise in self.noise_keywords:
            if noise in title:
                score -= 40
            if content_lower.count(noise) > 2:
                score -= 5

        if vocab_tech:
            tech_hits = 0
            for tech_word in vocab_tech:
                if tech_word.lower() in content_lower:
                    tech_hits += 1

            score += min(tech_hits * 2, 30)

        if len(content) < 500:
            score -= 50
        elif len(content) > 3000:
            score += 5

        source_name = article['source']['name']
        if source_name and any(s.lower() in source_name.lower() for s in self.reliable_sources):
            score += 15

        return score

    def get_sorted_articles(self, keywords_list, lang="fr", days=7, max_raw=50, top_k=10, tech_vocabulary=None):
        print(f"SortAgent : Recuperation de {max_raw} articles pour {keywords_list}...")

        raw_articles = self.fetch_from_api(keywords_list, lang, days, max_raw)

        if not raw_articles:
            print("Aucun article trouve via l'API.")
            return []

        processed_articles = []

        print(f"SortAgent : Analyse et Scoring de {len(raw_articles)} articles en cours...")

        for i, article in enumerate(raw_articles):
            try:
                downloaded = trafilatura.fetch_url(article["url"])
                content = trafilatura.extract(downloaded) if downloaded else ""
            except:
                content = ""

            if not content:
                continue

            score = self.pertinence_score_calcul(article, content, keywords_list, vocab_tech=tech_vocabulary)

            if score > 0:
                article_data = {
                    "title": article['title'],
                    "url": article['url'],
                    "source": article['source']['name'],
                    "date": article['publishedAt'][:10],
                    "content": content[:15000],
                    "relevance_score": score
                }
                processed_articles.append(article_data)

        sorted_list = sorted(processed_articles, key=lambda x: x['relevance_score'], reverse=True)

        final_selection = sorted_list[:top_k]
        print(final_selection)
        print(f"SortAgent : {len(final_selection)} articles qualifies retenus sur {len(raw_articles)}.")
        return final_selection


if __name__ == "__main__":
    agent = SortAgent()
    # Test sans liste technique
    agent.get_sorted_articles(keywords_list=["Data"], days=1, top_k=1)