import os
import discord
import json
from discord import app_commands
from dotenv import load_dotenv
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

        await self.tree.sync()
        print("Commandes synchronisees.")

        # --- Commande /subscribe_newsletter ---
        @self.tree.command(name="subscribe_newsletter", description="S'abonner à la newsletter en indiquant son email")
        @app_commands.describe(email="Votre adresse email pour recevoir la newsletter")
        async def subscribe_newsletter(interaction: discord.Interaction, email: str):
            await interaction.response.defer(ephemeral=True)
            try:
                fichier_email = "adresses_mail.txt"
                emails_existants = set()
                if os.path.exists(fichier_email):
                    with open(fichier_email, "r", encoding="utf-8") as f:
                        emails_existants = set(l.strip() for l in f.readlines())
                if email in emails_existants:
                    await interaction.followup.send("⚠️ Cette adresse est déjà inscrite à la newsletter.")
                    return
                with open(fichier_email, "a", encoding="utf-8") as f:
                    f.write(email + "\n")
                await interaction.followup.send(f"✅ Adresse {email} ajoutée à la newsletter !")
            except Exception as e:
                await interaction.followup.send(f"❌ Une erreur est survenue : {e}")

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