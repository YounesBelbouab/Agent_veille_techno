import os
import discord
import json
import re
from discord import app_commands
from dotenv import load_dotenv
from bigquery_utils import insert_config_to_bigquery

from veille_scraping import call_api_articles
from conversation_agent import ConversationAgent

MODEL_ID = "llama-3.3-70b-versatile"


class DiscordBot(discord.Client):
    def __init__(self, conversation_agent):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.conversation_agent = conversation_agent
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        @self.tree.command(name="ask", description="Pose une question à Jarvis")
        @app_commands.describe(question="Pose ta question...")
        async def ask(interaction: discord.Interaction, question: str):
            await interaction.response.defer()
            try:
                response = self.conversation_agent.ask_llm(user_interaction=question, model=MODEL_ID)
                full_response = f"**Question :** {question}\n\n{response}"

                if len(full_response) > 2000:
                    full_response = full_response[:1990] + "..."

                await interaction.followup.send(full_response)
            except Exception as e:
                await interaction.followup.send(f"Erreur : {e}")

        @self.tree.command(name="ask_veille", description="Lance une veille d'information")
        @app_commands.describe(
            sujet_veille="Sujet",
            langue="Langue",
            jour="Jours",
            nombre_article="Nombre"
        )
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="fr"),
            app_commands.Choice(name="English", value="en")
        ])
        async def ask_veille(
                interaction: discord.Interaction,
                sujet_veille: str,
                langue: app_commands.Choice[str],
                jour: int,
                nombre_article: int
        ):
            if jour < 1 or nombre_article < 1:
                await interaction.response.send_message("Erreur paramètres", ephemeral=True)
                return

            await interaction.response.defer()

            try:
                await interaction.followup.send(f"Recherche : {sujet_veille}...")

                articles_raw = call_api_articles(sujet=sujet_veille, langue=langue.value, jour=jour,
                                                 nb_articles=nombre_article)

                if isinstance(articles_raw, str):
                    try:
                        articles_raw = json.loads(articles_raw)
                    except json.JSONDecodeError:
                        await interaction.followup.send(f"Erreur format donnees : {articles_raw[:1000]}")
                        return

                if not isinstance(articles_raw, list):
                    await interaction.followup.send("Erreur : Format de liste invalide")
                    return

                if not articles_raw:
                    await interaction.followup.send("Aucun article trouve.")
                    return

                for article in articles_raw:
                    if not isinstance(article, dict):
                        continue

                    titre = article.get('title', article.get('titre', 'Sans titre'))
                    url = article.get('url', article.get('link', 'N/A'))
                    contenu_source = article.get('content',
                                                 article.get('summary', article.get('description', 'Pas de contenu')))

                    prompt_agent = (
                        f"Tache : Analyse cet article et genere un rapport de veille complet selon le format defini dans le contexte systeme.\n"
                        f"IMPORTANT : Tu DOIS rediger la section RESUME de maniere explicite.\n\n"
                        f"--- DONNEES ARTICLE ---\n"
                        f"Titre : {titre}\n"
                        f"URL : {url}\n"
                        f"Texte source : {contenu_source[:15000]}"
                    )

                    reponse_formatee = self.conversation_agent.ask_llm(user_interaction=prompt_agent, model=MODEL_ID)

                    if len(reponse_formatee) > 2000:
                        chunks = [reponse_formatee[i:i + 1990] for i in range(0, len(reponse_formatee), 1990)]
                        for chunk in chunks:
                            await interaction.channel.send(chunk)
                    else:
                        await interaction.channel.send(reponse_formatee)

                await interaction.channel.send("Veille terminee.")

            except Exception as e:
                await interaction.followup.send(f"Erreur critique : {str(e)}")

        # --- Commande /config_veille ---
        @self.tree.command(name="config_veille", description="Configure tes préférences de veille")
        @app_commands.describe(
            email="Ton adresse email pour les rapports",
            sujet="Le sujet principal de ta veille",
            langue="Langue des articles",
            periode="Période de recherche (jours)",
            nb_articles="Nombre d'articles à analyser"
        )
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="fr"),
            app_commands.Choice(name="English", value="en")
        ])
        async def config_veille(
            interaction: discord.Interaction,
            email: str,
            sujet: str,
            langue: app_commands.Choice[str],
            periode: int,
            nb_articles: int,
        ):
            # 1. Validation email
            email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_pattern, email):
                await interaction.response.send_message(
                    "❌ Adresse email invalide. Elle doit contenir un '@' et un domaine (ex: .com).", 
                    ephemeral=True
                )
                return

            # Sécurité valeur entrée
            if periode < 1 or nb_articles < 1:
                await interaction.response.send_message(
                    "❌ Le nombre de jours et d'articles doit être supérieur à 0.", 
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            try:
                user_data = {
                    "id_discord": str(interaction.user.id),
                    "email": email,
                    "sujet": sujet,
                    "langue": langue.value,
                    "periode": periode,
                    "nb_articles": nb_articles,
                }

                insert_config_to_bigquery(user_data) 

                await interaction.followup.send(
                    f"✅ Configuration sauvegardée pour **{sujet}** ({langue.name}) !\n"
                    f"Rapports envoyés à : `{email}`"
                )

            except Exception as e:
                print(f"Erreur BQ: {e}")
                await interaction.followup.send(f"❌ Erreur lors de la sauvegarde : {str(e)}")

        await self.tree.sync()
        print("Commandes synchronisees.")

    async def on_ready(self):
        print(f'Connecte : {self.user}')


if __name__ == "__main__":
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')

    if not discord_token:
        print("Erreur token")
    else:
        agent = ConversationAgent()
        bot = DiscordBot(conversation_agent=agent)
        bot.run(discord_token)